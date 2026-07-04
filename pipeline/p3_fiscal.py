#!/usr/bin/env python3
"""
p3_fiscal.py — GORGIAS Tier 1 fiscal-note scraper (Appendix A.5 budget stratum).

Fetches LBB fiscal notes + bill status from Texas Legislature Online (capitol.texas.gov,
plain server-rendered HTML) for the homestead-exemption cascade, saves raw text, and
emits T3 ocr_cleanup jobs for the GLM fleet. NO LLM calls here — fetch + chunk only.

Bills fetched:
  - HB 9 (89R)  — business-personal-property ad-valorem exemption; the analog the
                  BUILD_PROMPT names for the fiscal-impact panel (A.1/A.5).
  - S.B. 4 (89R) and S.B. 23 (89R) — the bills that ACTUALLY raised the residence
                  homestead exemption to $140,000 (Ch. 338 / Ch. 340, 2025), per the
                  amendment history in Tax Code §11.13. These carry the true homestead
                  dollar figures and are the honest ground truth for the budget nodes.

Outputs:
  - pipeline/out/raw/fiscal-<bill>-<ver>.json   {bill, cite, url, fetched_at, text, dollars_found}
  - pipeline/out/raw/status-<bill>.json         {bill, url, fetched_at, text, last_action}
  - pipeline/jobs/t3_fiscal.jsonl               one T3 ocr_cleanup job per fiscal note
  - appends to pipeline/out/manifest.json

Run:  ../.venv/bin/python p3_fiscal.py
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

SESS = "89R"
FN_HTML = "https://capitol.texas.gov/tlodocs/{sess}/fiscalnotes/html/{bill5}{ver}.htm"
FN_PDF = "https://capitol.texas.gov/tlodocs/{sess}/fiscalnotes/pdf/{bill5}{ver}.pdf"
HISTORY = "https://capitol.texas.gov/BillLookup/History.aspx?LegSess={sess}&Bill={bill}"

WORKER_VERSION = "wp-1.0"
UA = "Mozilla/5.0 (gorgias-pipeline/1.0; +hackathon)"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"}

# Bill -> (5-digit padded id, human cite, role note). Fiscal-note versions tried in order.
BILLS = [
    {"bill": "HB9", "bill5": "HB00009", "cite": "HB 9 (89R)",
     "role": "business personal property ad-valorem exemption — fiscal-impact analog (BUILD_PROMPT A.1/A.5)",
     "versions": ["I", "E", "A", "F"]},
    {"bill": "SB4", "bill5": "SB00004", "cite": "S.B. 4 (89R)",
     "role": "ACTUAL residence homestead exemption raise to $140,000 (Tax Code §11.13, Ch. 338) — true homestead ground truth",
     "versions": ["I", "E", "A", "F"]},
    {"bill": "SB23", "bill5": "SB00023", "cite": "S.B. 23 (89R)",
     "role": "companion homestead exemption measure (Ch. 340) — additional homestead ground truth",
     "versions": ["I", "E", "A", "F"]},
]
PRIMARY_BILL = "HB9"  # the one the BUILD_PROMPT explicitly names


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def html_to_text(raw: str) -> str:
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    s = re.sub(r"(?i)<\s*br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</\s*(p|div|tr|li|h[1-6]|table)\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*td\s*>", " \t", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln)


# LBB notes format negatives as "($465,483,918)"; capture the leading paren too.
DOLLAR_RE = re.compile(r"\(?\$\s?-?[0-9][0-9,]*(?:\.[0-9]+)?\)?")


def dollars(text: str) -> list[str]:
    return [m.group(0).strip() for m in DOLLAR_RE.finditer(text)]


def fetch(client: httpx.Client, url: str) -> tuple[int, str]:
    r = client.get(url)
    return r.status_code, r.text


def last_action(text: str) -> str | None:
    # History pages list "Last Action:" or an action table; grab the Last Action line.
    m = re.search(r"Last Action[:\s]*([^\n]{6,140})", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def main() -> int:
    manifest: list[dict] = []
    misses: list[dict] = []
    fiscal_saved: list[dict] = []

    with httpx.Client(follow_redirects=True, timeout=45.0, headers=HEADERS) as client:
        for b in BILLS:
            # --- fiscal note: take the first version that returns real HTML with dollars ---
            got_fn = False
            for ver in b["versions"]:
                url = FN_HTML.format(sess=SESS, bill5=b["bill5"], ver=ver)
                try:
                    code, raw = fetch(client, url)
                except Exception as e:  # noqa: BLE001
                    manifest.append({"url": url, "status": "ERROR", "error": str(e),
                                     "fetched_at": now_iso(), "kind": "fiscal-note"})
                    continue
                is_spa = "data-beasties-container" in raw[:2000]
                text = html_to_text(raw) if (code == 200 and not is_spa) else ""
                dols = dollars(text)
                manifest.append({
                    "url": url, "status": code, "bytes": len(raw), "text_chars": len(text),
                    "dollars_found": len(dols), "fetched_at": now_iso(),
                    "kind": "fiscal-note", "bill": b["bill"], "version": ver,
                })
                if code == 200 and not is_spa and len(dols) >= 3:
                    rec = {
                        "bill": b["bill"], "cite": b["cite"], "role": b["role"],
                        "version": ver, "url": url,
                        "pdf_url": FN_PDF.format(sess=SESS, bill5=b["bill5"], ver=ver),
                        "fetched_at": now_iso(), "text": text,
                        "dollars_found": dols, "dollars_count": len(dols),
                    }
                    slug = f"{b['bill'].lower()}-{ver.lower()}"
                    (OUT_RAW / f"fiscal-{slug}.json").write_text(
                        json.dumps(rec, indent=2, ensure_ascii=False))
                    rec["slug"] = slug
                    fiscal_saved.append(rec)
                    print(f"[FISCAL] {b['cite']:16s} v{ver} -> {code}, {len(text)} chars, "
                          f"{len(dols)} dollar figures  {dols[:3]}")
                    got_fn = True
                    break
            if not got_fn:
                misses.append({"cite": b["cite"], "reason": "no fiscal-note version returned HTML with >=3 dollar figures"})
                print(f"[FISCAL-MISS] {b['cite']}: no usable HTML fiscal note", file=sys.stderr)

            # --- bill status / history (for the primary bill and the real homestead bills) ---
            hurl = HISTORY.format(sess=SESS, bill=b["bill"])
            try:
                code, raw = fetch(client, hurl)
                is_spa = "data-beasties-container" in raw[:2000]
                text = html_to_text(raw) if (code == 200 and not is_spa) else ""
                la = last_action(text)
                (OUT_RAW / f"status-{b['bill'].lower()}.json").write_text(json.dumps({
                    "bill": b["bill"], "cite": b["cite"], "url": hurl,
                    "fetched_at": now_iso(), "last_action": la, "text": text,
                }, indent=2, ensure_ascii=False))
                manifest.append({"url": hurl, "status": code, "bytes": len(raw),
                                 "text_chars": len(text), "fetched_at": now_iso(),
                                 "kind": "bill-status", "bill": b["bill"], "last_action": la})
                print(f"[STATUS] {b['cite']:16s} -> {code}, last action: {la}")
            except Exception as e:  # noqa: BLE001
                manifest.append({"url": hurl, "status": "ERROR", "error": str(e),
                                 "fetched_at": now_iso(), "kind": "bill-status"})
                misses.append({"cite": b["cite"] + " status", "reason": str(e)})

    # --- emit T3 ocr_cleanup jobs (one per saved fiscal note) ---
    t3_path = JOBS / "t3_fiscal.jsonl"
    with t3_path.open("w") as f:
        for rec in fiscal_saved:
            job = {
                "job_id": f"t3-{rec['slug']}",
                "worker_version": WORKER_VERSION,
                "task": "T3",
                "doc_kind": "fiscal_note",
                "bill": rec["bill"],
                "cite_hint": rec["cite"],
                "source_url": rec["url"],
                "text": rec["text"],
            }
            f.write(json.dumps(job, ensure_ascii=False) + "\n")

    # --- manifest ---
    existing = []
    if MANIFEST.exists():
        try:
            existing = json.loads(MANIFEST.read_text())
        except Exception:  # noqa: BLE001
            existing = []
    existing.extend(manifest)
    MANIFEST.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    # --- MISSING report (append-aware: keep p1's misses if present) ---
    if misses:
        existing_missing = ""
        mp = OUT_RAW / "MISSING.md"
        if mp.exists():
            existing_missing = mp.read_text()
        lines = [existing_missing.rstrip(), "", "# MISSING / FAILED — p3_fiscal.py",
                 f"Generated {now_iso()}", ""]
        for m in misses:
            lines.append(f"- **{m['cite']}** — {m['reason']}")
        mp.write_text("\n".join(lines).lstrip() + "\n")

    # --- sanity gate: at least the primary bill's fiscal note has dollar figures ---
    primary_ok = any(r["bill"] == PRIMARY_BILL and r["dollars_count"] >= 3 for r in fiscal_saved)
    any_dollars = any(r["dollars_count"] >= 3 for r in fiscal_saved)

    print("\n=== p3_fiscal summary ===")
    print(f"fiscal notes saved : {len(fiscal_saved)} ({', '.join(r['slug'] for r in fiscal_saved)})")
    print(f"T3 jobs            : {len(fiscal_saved)} -> {t3_path}")
    print(f"primary (HB 9) fiscal note has $ figures: {'YES' if primary_ok else 'NO'}")
    print(f"any fiscal note has $ figures          : {'YES' if any_dollars else 'NO — SANITY FAIL'}")
    if misses:
        print(f"misses             : {len(misses)} (see out/raw/MISSING.md)")
        for m in misses:
            print(f"  - {m['cite']}: {m['reason']}")
    return 0 if any_dollars else 1


if __name__ == "__main__":
    sys.exit(main())
