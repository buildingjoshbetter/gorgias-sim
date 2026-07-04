#!/usr/bin/env python3
"""
p1_statutes.py — GORGIAS Tier 1 statute scraper (Appendix A.2 cites).

Fetches the Texas statute/constitution chapter HTML for every cite the homestead
cascade touches, extracts the verbatim section text, and writes:
  - pipeline/out/raw/<cite-slug>.json   {cite, url, fetched_at, text, ...}
  - pipeline/jobs/t1_statutes.jsonl     one T1 statute_extract job per cite
  - pipeline/jobs/t2_conflicts.jsonl    T2 conflict_scan jobs (proposed change vs rule)
  - appends fetch records to pipeline/out/manifest.json

NO LLM calls here. This is fetch + regex chunking only. GLM jobs run later via herd.py.

Run:  ../.venv/bin/python p1_statutes.py   (from pipeline/), or
      .venv/bin/python pipeline/p1_statutes.py   (from repo root)
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
OUT_RAW = HERE / "out" / "raw"
JOBS = HERE / "jobs"
MANIFEST = HERE / "out" / "manifest.json"

OUT_RAW.mkdir(parents=True, exist_ok=True)
JOBS.mkdir(parents=True, exist_ok=True)

# The statutes site (statutes.capitol.texas.gov) is now an Angular SPA; the legacy
# static /Docs/<CODE>/htm/<CODE>.<CHAP>.htm path returns the app shell, not the text.
# The SPA fetches the real HTML from the TCAS file server (discovered by reading the
# app bundle: TCASCore = https://tcss.legis.texas.gov/api/, FileServerPath resources).
# We fetch the raw HTML from the resource host and keep the public URL for citations.
FETCH_BASE = "https://tcss.legis.texas.gov/resources/{code}/htm/{code}.{chap}.htm"
PUBLIC_BASE = "https://statutes.capitol.texas.gov/Docs/{code}/htm/{code}.{chap}.htm"


def chapter_urls(code: str, chap: str) -> tuple[str, str]:
    """(fetch_url on the TCAS resource host, public citation URL)."""
    return (FETCH_BASE.format(code=code, chap=chap), PUBLIC_BASE.format(code=code, chap=chap))


# Which chapter file each code+chapter lives in. CN = Constitution (article number as "chapter").
# Maps (code, chapter) -> (fetch_url, public_url).
CHAPTERS = {
    ("TX", "11"): chapter_urls("TX", "11"),  # Tax Code Ch. 11
    ("TX", "26"): chapter_urls("TX", "26"),  # Tax Code Ch. 26
    ("ED", "48"): chapter_urls("ED", "48"),  # Education Code Ch. 48
    ("CN", "8"): chapter_urls("CN", "8"),    # Tex. Const. art. VIII
}

# Appendix A.2 cite table: canonical cite -> (chapter key, section number to extract,
# optional subsection letter, slug, sanity substring that must appear in the section text).
CITES = [
    {
        "cite": "Tax Code §11.13(b)",
        "chap": ("TX", "11"), "sec": "11.13", "sub": "b",
        "slug": "tax-11-13-b",
        "sanity": None,  # dollar figure checked at the section level via 11-13 aggregate
        "claim": "mandatory school-district residence homestead exemption amount — the section the policy amends",
    },
    {
        "cite": "Tax Code §11.13(n)",
        "chap": ("TX", "11"), "sec": "11.13", "sub": "n",
        "slug": "tax-11-13-n",
        "sanity": None,
        "claim": "optional percentage exemption interplay — must not conflict with new floor",
    },
    {
        "cite": "Tax Code §11.26",
        "chap": ("TX", "11"), "sec": "11.26", "sub": None,
        "slug": "tax-11-26",
        "sanity": None,
        "claim": "tax ceiling for 65+/disabled — ceiling must be reduced to reflect increased exemption",
    },
    {
        "cite": "Tax Code §26.09",
        "chap": ("TX", "26"), "sec": "26.09", "sub": None,
        "slug": "tax-26-09",
        "sanity": None,
        "claim": "assessor calculation of tax — mechanical downstream change",
    },
    {
        "cite": "Educ. Code §48.2556",
        "chap": ("ED", "48"), "sec": "48.2556", "sub": None,
        "slug": "educ-48-2556",
        "sanity": None,
        "claim": "state compensation to districts for exemption-driven revenue loss (hold harmless)",
    },
    {
        "cite": "Educ. Code §48.255",
        "chap": ("ED", "48"), "sec": "48.255", "sub": None,
        "slug": "educ-48-255",
        "sanity": None,
        "claim": "Foundation School Program funding formulas absorbing the local revenue drop",
    },
    {
        "cite": "Tex. Const. art. VIII, §1-b(c)",
        "chap": ("CN", "8"), "sec": "1-b", "sub": "c",
        "slug": "const-viii-1b-c",
        "sanity": None,
        "claim": "constitutional amendment prerequisite — exemption amount is constitutionalized",
    },
]

# The proposed change paragraph reused across every T2 conflict job.
PROPOSED_CHANGE = (
    "Amend Tax Code §11.13(b): increase the general residence homestead exemption "
    "for school district ad valorem taxation from $100,000 to $140,000 of appraised value."
)

# T2 pairings: the proposed change vs. each rule whose text may collide with it.
T2_TARGETS = [
    ("Tax Code §11.26", "tax-11-26"),
    ("Tax Code §11.13(n)", "tax-11-13-n"),
    ("Tex. Const. art. VIII, §1-b(c)", "const-viii-1b-c"),
]

WORKER_VERSION = "wp-1.0"
UA = "Mozilla/5.0 (gorgias-pipeline/1.0; +hackathon)"
FETCH_HEADERS = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Referer": "https://statutes.capitol.texas.gov/",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def html_to_text(raw: str) -> str:
    """Convert statute chapter HTML to plain text, preserving paragraph breaks."""
    s = raw
    # Drop scripts/styles wholesale.
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    # Turn block/br boundaries into newlines so section headers stay on their own lines.
    s = re.sub(r"(?i)<\s*br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</\s*(p|div|tr|li|h[1-6])\s*>", "\n", s)
    # Strip remaining tags.
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace(" ", " ").replace("\xa0", " ")
    # Normalize spaces within lines but keep newlines.
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.splitlines()]
    s = "\n".join(ln for ln in lines if ln != "")
    return s


def extract_section(text: str, sec_num: str) -> str | None:
    """
    Return the verbatim text of one section, from its 'Sec. <num>.' header up to the
    next real section header. sec_num like '11.13', '48.2556', '1-b'.

    Two hazards handled:
      - '11.13' must not stop at a cross-ref or swallow '11.131': the boundary is
        constrained to the SAME chapter number (e.g. 'Sec. 26.<n>').
      - Session-law refs inside amendment annotations ('...(S.B. 4), Sec. 2.12')
        must NOT be treated as the next statute header: a real header is followed by
        an uppercase catchline ('Sec. 26.09. CALCULATION OF TAX.'), so we require
        '. <UPPERCASE>' after the number.
    """
    catchline = r"\.\s+[A-Z0-9(]"  # header period, then caps catchline / subsection marker
    esc = re.escape(sec_num)
    start_pat = re.compile(rf"Sec\.\s*{esc}{catchline}", re.IGNORECASE)
    m = start_pat.search(text)
    if not m:
        # Fallback: header may lack the caps catchline (rare); accept a bare header.
        m = re.compile(rf"Sec\.\s*{esc}\.(?!\d)", re.IGNORECASE).search(text)
        if not m:
            return None

    if "." in sec_num:  # statute: constrain the next header to the same chapter
        chap = re.escape(sec_num.split(".")[0])
        next_pat = re.compile(rf"Sec\.\s*{chap}\.[0-9][0-9A-Za-z\-]*{catchline}")
    else:  # constitution article section (e.g. '1-b'): any real, catchlined header
        next_pat = re.compile(rf"Sec\.\s*[0-9][0-9A-Za-z\-]*{catchline}")

    end = len(text)
    for nm in next_pat.finditer(text, m.end()):
        end = nm.start()
        break
    block = text[m.start():end].strip()
    return block or None


def extract_subsection(section_text: str, letter: str) -> str | None:
    """
    Pull one lettered subsection, e.g. '(b) ...' up to the next same-level '(x)' marker.
    Best-effort; the full section text is always the authoritative chunk.
    """
    pat = re.compile(rf"\(\s*{re.escape(letter)}\s*\)")
    m = pat.search(section_text)
    if not m:
        return None
    start = m.start()
    nxt = re.compile(r"\n?\(\s*[a-z]{1,3}\s*\)")
    end = len(section_text)
    for nm in nxt.finditer(section_text, m.end()):
        end = nm.start()
        break
    return section_text[start:end].strip() or None


def fetch(client: httpx.Client, url: str) -> tuple[int, str]:
    r = client.get(url)
    return r.status_code, r.text


def main() -> int:
    manifest: list[dict] = []
    chapter_text: dict[tuple[str, str], str] = {}
    chapter_status: dict[tuple[str, str], int] = {}

    with httpx.Client(follow_redirects=True, timeout=45.0, headers=FETCH_HEADERS) as client:
        # 1) Fetch each unique chapter file once (from the TCAS resource host).
        for key, (fetch_url, public_url) in CHAPTERS.items():
            try:
                code, raw = fetch(client, fetch_url)
            except Exception as e:  # noqa: BLE001 - log and continue; misses reported later
                print(f"[FETCH-ERR] {fetch_url}: {e}", file=sys.stderr)
                manifest.append({"url": fetch_url, "status": "ERROR", "error": str(e),
                                 "fetched_at": now_iso(), "kind": "statute-chapter"})
                chapter_status[key] = -1
                continue
            is_spa = "data-beasties-container" in raw[:2000]
            chapter_status[key] = code
            txt = html_to_text(raw) if (code == 200 and not is_spa) else ""
            chapter_text[key] = txt
            manifest.append({
                "url": public_url, "fetch_url": fetch_url, "status": code, "bytes": len(raw),
                "text_chars": len(txt), "fetched_at": now_iso(),
                "kind": "statute-chapter", "chapter": f"{key[0]}.{key[1]}",
                "spa_shell": is_spa,
            })
            flag = " [SPA-SHELL!]" if is_spa else ""
            print(f"[FETCH] {fetch_url} -> {code}, {len(raw)} bytes, {len(txt)} text chars{flag}")

    # 2) Extract each cite's section, write raw JSON.
    captured: dict[str, dict] = {}
    misses: list[dict] = []
    for c in CITES:
        key = c["chap"]
        text = chapter_text.get(key, "")
        if not text:
            misses.append({"cite": c["cite"], "reason": f"chapter {key} not fetched (status {chapter_status.get(key)})"})
            continue
        section = extract_section(text, c["sec"])
        if not section:
            misses.append({"cite": c["cite"], "reason": f"section {c['sec']} not found in chapter {key}"})
            continue
        sub_text = extract_subsection(section, c["sub"]) if c["sub"] else None
        _, public_url = CHAPTERS[key]
        record = {
            "cite": c["cite"],
            "url": public_url + f"#{c['sec']}",
            "chapter_url": public_url,
            "fetched_at": now_iso(),
            "section": c["sec"],
            "subsection": c["sub"],
            "operative_claim": c["claim"],
            "text": section,
            "subsection_text": sub_text,
            "text_chars": len(section),
        }
        (OUT_RAW / f"{c['slug']}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
        captured[c["slug"]] = record
        print(f"[EXTRACT] {c['cite']:34s} -> {len(section)} chars"
              + (f", sub({c['sub']}) {len(sub_text) if sub_text else 0} chars" if c["sub"] else ""))

    # 3) Emit T1 statute_extract jobs (one per captured cite).
    t1_path = JOBS / "t1_statutes.jsonl"
    with t1_path.open("w") as f:
        n_t1 = 0
        for c in CITES:
            rec = captured.get(c["slug"])
            if not rec:
                continue
            job = {
                "job_id": f"t1-{c['slug']}",
                "worker_version": WORKER_VERSION,
                "task": "T1",
                "cite_hint": c["cite"],
                "source_url": rec["url"],
                "text": rec["text"],
            }
            f.write(json.dumps(job, ensure_ascii=False) + "\n")
            n_t1 += 1

    # 4) Emit T2 conflict_scan jobs (proposed change vs each rule text).
    t2_path = JOBS / "t2_conflicts.jsonl"
    with t2_path.open("w") as f:
        n_t2 = 0
        for rule_cite, slug in T2_TARGETS:
            rec = captured.get(slug)
            if not rec:
                misses.append({"cite": rule_cite, "reason": "T2 target text unavailable — job skipped"})
                continue
            job = {
                "job_id": f"t2-{slug}",
                "worker_version": WORKER_VERSION,
                "task": "T2",
                "proposed_change": PROPOSED_CHANGE,
                "rule_cite": rule_cite,
                "rule_text": rec["subsection_text"] or rec["text"],
            }
            f.write(json.dumps(job, ensure_ascii=False) + "\n")
            n_t2 += 1

    # 5) Sanity gate: the homestead exemption dollar figure must appear in §11.13 text.
    #    NOTE: as of the 89th Legislature (2025, S.B. 4) the live figure is $140,000 —
    #    the "$100,000 -> $140,000" scenario is the change the 89th Lege actually made,
    #    so current statute text reflects $140,000, not $100,000. Accept either.
    s1113 = captured.get("tax-11-13-b", {}).get("text", "")
    live_amount = "$140,000" if "$140,000" in s1113 else ("$100,000" if "$100,000" in s1113 else None)
    dollar_ok = live_amount is not None
    if not dollar_ok:
        misses.append({
            "cite": "Tax Code §11.13(b)",
            "reason": "sanity FAIL: no homestead exemption dollar figure ($140,000/$100,000) in extracted §11.13 text",
        })

    # 6) Write manifest + MISSING report.
    existing = []
    if MANIFEST.exists():
        try:
            existing = json.loads(MANIFEST.read_text())
        except Exception:  # noqa: BLE001
            existing = []
    existing.extend(manifest)
    MANIFEST.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    if misses:
        lines = ["# MISSING / FAILED CAPTURES — p1_statutes.py", "", f"Generated {now_iso()}", ""]
        for m in misses:
            lines.append(f"- **{m['cite']}** — {m['reason']}")
        (OUT_RAW / "MISSING.md").write_text("\n".join(lines) + "\n")

    # 7) Report.
    print("\n=== p1_statutes summary ===")
    print(f"cites captured : {len(captured)}/{len(CITES)}")
    print(f"T1 jobs        : {n_t1} -> {t1_path}")
    print(f"T2 jobs        : {n_t2} -> {t2_path}")
    print(f"§11.13(b) live exemption figure: {live_amount or 'NONE — SANITY FAIL'}"
          + ("  (89R already raised it to $140,000)" if live_amount == "$140,000" else ""))
    if misses:
        print(f"misses         : {len(misses)} (see out/raw/MISSING.md)")
        for m in misses:
            print(f"  - {m['cite']}: {m['reason']}")
    return 0 if (len(captured) == len(CITES) and dollar_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
