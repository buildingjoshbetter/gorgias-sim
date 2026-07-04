#!/usr/bin/env python3
"""
p4_crawl.py — GORGIAS multi-layer citation/conflict graph builder.

Two phases:

  p4_crawl.py fetch
      Fetch whole chapters (target scope + BFS-discovered cross-referenced
      chapters) from the TCAS resource host, split EVERY section, resolve
      cross-references deterministically by regex over the actual fetched text,
      assign BFS layers from the 7 seed cites, and emit:
        - pipeline/out/crawl-nodes.json      full node corpus (with section text)
        - pipeline/jobs/t1_crawl.jsonl       one T1 statute_extract job per node
        - pipeline/jobs/t2_crawl.jsonl       one T2 conflict_scan job per node

  p4_crawl.py assemble
      Merge GLM outputs (out/t1c-*.json, out/t2c-*.json) back onto the node
      corpus and write:
        - gorgias/data/conflict-graph.json
        - gorgias/data/conflict-graph-summary.md

NO LLM calls here. Fetch + regex only. GLM runs between the two phases via herd.py.

Integrity: every node comes from actually-fetched chapter text. No invented cites.
Sections that fail GLM extraction keep their regex heading and are tagged; no
analysis is claimed for them.
"""
from __future__ import annotations

import json
import re
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Reuse the battle-tested HTML->text converter from p1 (no network side effects on import).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p1_statutes import html_to_text  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
JOBS = HERE / "jobs"
REPO = HERE.parent  # gorgias/
DATA = REPO / "data"
OUT.mkdir(parents=True, exist_ok=True)
JOBS.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

FETCH_BASE = "https://tcss.legis.texas.gov/resources/{code}/htm/{code}.{chap}.htm"
PUBLIC_BASE = "https://statutes.capitol.texas.gov/Docs/{code}/htm/{code}.{chap}.htm"

UA = "Mozilla/5.0 (gorgias-pipeline/1.0; +hackathon)"
FETCH_HEADERS = {"User-Agent": UA, "Accept": "*/*", "Referer": "https://statutes.capitol.texas.gov/"}

# Target scope: every section of these chapters becomes a node.
# Full-code expansion (G1 mega-crawl): Tax Code (all chapters), Education Code
# Ch. 1-49, Government Code 403/404/2001/2306, Local Government Code finance /
# special-taxing-district / economic-development chapters, Election Code
# 251-259 + 271-279 (campaign finance + amendment/measure elections), Water
# Code Ch. 49 (special districts). Const. art. VIII stays a seed layer below.
TARGET_CHAPTERS = [
    ("CN", "8"),   # Tex. Const. art. VIII — Taxation and Revenue (seed chapter)
    ("TX", "1"), ("TX", "5"), ("TX", "6"), ("TX", "11"), ("TX", "21"), ("TX", "22"), ("TX", "23"), ("TX", "24"),
    ("TX", "25"), ("TX", "26"), ("TX", "31"), ("TX", "32"), ("TX", "33"), ("TX", "34"), ("TX", "41"), ("TX", "42"),
    ("TX", "43"), ("TX", "101"), ("TX", "111"), ("TX", "112"), ("TX", "113"), ("TX", "141"), ("TX", "142"), ("TX", "151"),
    ("TX", "152"), ("TX", "154"), ("TX", "155"), ("TX", "156"), ("TX", "158"), ("TX", "160"), ("TX", "162"), ("TX", "163"),
    ("TX", "171"), ("TX", "172"), ("TX", "181"), ("TX", "182"), ("TX", "183"), ("TX", "191"), ("TX", "201"), ("TX", "202"),
    ("TX", "204"), ("TX", "301"), ("TX", "302"), ("TX", "311"), ("TX", "312"), ("TX", "313"), ("TX", "320"), ("TX", "321"),
    ("TX", "322"), ("TX", "323"), ("TX", "324"), ("TX", "325"), ("TX", "327"), ("TX", "351"), ("TX", "352"), ("ED", "1"),
    ("ED", "4"), ("ED", "5"), ("ED", "7"), ("ED", "8"), ("ED", "10"), ("ED", "11"), ("ED", "12"), ("ED", "13"),
    ("ED", "18"), ("ED", "19"), ("ED", "21"), ("ED", "22"), ("ED", "23"), ("ED", "25"), ("ED", "26"), ("ED", "27"),
    ("ED", "28"), ("ED", "29"), ("ED", "30"), ("ED", "31"), ("ED", "32"), ("ED", "33"), ("ED", "34"), ("ED", "35"),
    ("ED", "37"), ("ED", "38"), ("ED", "39"), ("ED", "43"), ("ED", "44"), ("ED", "45"), ("ED", "46"), ("ED", "47"),
    ("ED", "48"), ("ED", "49"), ("GV", "403"), ("GV", "404"), ("GV", "2001"), ("GV", "2306"), ("LG", "101"), ("LG", "102"),
    ("LG", "103"), ("LG", "104"), ("LG", "105"), ("LG", "106"), ("LG", "107"), ("LG", "111"), ("LG", "112"), ("LG", "113"),
    ("LG", "114"), ("LG", "115"), ("LG", "116"), ("LG", "117"), ("LG", "118"), ("LG", "130"), ("LG", "131"), ("LG", "133"),
    ("LG", "134"), ("LG", "135"), ("LG", "140"), ("LG", "141"), ("LG", "271"), ("LG", "281"), ("LG", "302"), ("LG", "303"),
    ("LG", "304"), ("LG", "306"), ("LG", "320"), ("LG", "321"), ("LG", "322"), ("LG", "323"), ("LG", "324"), ("LG", "325"),
    ("LG", "326"), ("LG", "327"), ("LG", "331"), ("LG", "332"), ("LG", "333"), ("LG", "334"), ("LG", "335"), ("LG", "336"),
    ("LG", "341"), ("LG", "342"), ("LG", "343"), ("LG", "344"), ("LG", "351"), ("LG", "352"), ("LG", "353"), ("LG", "361"),
    ("LG", "362"), ("LG", "363"), ("LG", "372"), ("LG", "373"), ("LG", "374"), ("LG", "375"), ("LG", "376"), ("LG", "377"),
    ("LG", "378"), ("LG", "379"), ("LG", "380"), ("LG", "381"), ("LG", "382"), ("LG", "383"), ("LG", "386"), ("LG", "387"),
    ("LG", "388"), ("LG", "391"), ("LG", "392"), ("LG", "393"), ("LG", "394"), ("LG", "395"), ("LG", "397"), ("LG", "399"),
    ("EL", "251"), ("EL", "252"), ("EL", "253"), ("EL", "254"), ("EL", "255"), ("EL", "257"), ("EL", "258"), ("EL", "259"),
    ("EL", "271"), ("EL", "272"), ("EL", "273"), ("EL", "274"), ("EL", "275"), ("EL", "276"), ("EL", "277"), ("EL", "278"),
    ("EL", "279"), ("WA", "49"),
]

# The 7 seed cites (existing t1-*.json outputs) at section granularity -> (code, chap, sec).
SEEDS = [
    ("TX", "11", "11.13"),
    ("TX", "11", "11.26"),
    ("TX", "26", "26.09"),
    ("ED", "48", "48.2556"),
    ("ED", "48", "48.255"),
    ("CN", "8", "1-b"),
]

# The single proposed change reused across every T2 conflict job.
PROPOSED_CHANGE = (
    "Increase the Texas residence homestead exemption under Tax Code §11.13(b) "
    "from $140,000 to $200,000 of appraised value."
)

# Code-name (as it appears in statute cross-refs) -> URL/cite abbreviation.
CODE_WORD = {
    "tax": "TX", "education": "ED", "government": "GV", "local government": "LG",
    "property": "PR", "insurance": "IN", "health and safety": "HS", "water": "WA",
    "transportation": "TN", "natural resources": "NR", "occupations": "OC",
    "finance": "FI", "agriculture": "AG", "estates": "ES", "family": "FA",
    "civil practice and remedies": "CP", "special district local laws": "SD",
    "labor": "LA", "election": "EL", "utilities": "UT", "human resources": "HR",
    "parks and wildlife": "PW",
}
ABBR_NAME = {v: k for k, v in CODE_WORD.items()}
ABBR_NAME["CN"] = "constitution"

# Human-readable code abbreviation for canonical cite strings.
CITE_ABBR = {
    "TX": "Tax Code", "ED": "Educ. Code", "GV": "Gov't Code", "LG": "Local Gov't Code",
    "PR": "Prop. Code", "IN": "Ins. Code", "HS": "Health & Safety Code", "WA": "Water Code",
    "TN": "Transp. Code", "NR": "Nat. Res. Code", "OC": "Occ. Code", "FI": "Fin. Code",
    "AG": "Agric. Code", "ES": "Est. Code", "FA": "Fam. Code", "CP": "Civ. Prac. & Rem. Code",
    "SD": "Spec. Dist. Code", "LA": "Labor Code", "EL": "Elec. Code", "UT": "Util. Code",
    "HR": "Human Res. Code", "PW": "Parks & Wild. Code",
}

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
         "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
         "XVI": 16, "XVII": 17, "XVIII": 18}

# Safety cap so a bad regex can't fetch the entire statute corpus.
# Mega-crawl fetches ~186 target chapters plus BFS cross-ref chapters.
MAX_CHAPTERS = 400
MAX_LAYER = 4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

def split_sections(text: str, code: str, chap: str) -> dict[str, str]:
    """Split a chapter's plain text into {section_number: verbatim_block}.

    Real headers use the 'Sec.' abbreviation + a same-chapter number + an
    uppercase catchline. Cross-references in the body spell out 'Section', and
    amendment annotations ('..., Sec. 1, eff.') lack the chapter dot — neither
    matches, so they don't create phantom sections.
    """
    if code == "CN":  # constitution: 'Sec. 1-b. CATCHLINE'
        hdr = re.compile(r"Sec\.\s*([0-9][0-9A-Za-z\-]*)\.\s+[A-Z0-9(]")
    else:  # statute: 'Sec. 11.13. CATCHLINE' constrained to this chapter
        c = re.escape(chap)
        hdr = re.compile(rf"Sec\.\s*({c}\.[0-9][0-9A-Za-z\-]*)\.\s+[A-Z0-9(]")
    matches = list(hdr.finditer(text))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sec = m.group(1)
        if sec not in out:  # keep first occurrence (the real header, not a repeat)
            out[sec] = text[start:end].strip()
    return out


def extract_heading(block: str) -> str:
    """Heading = the uppercase catchline immediately after 'Sec. <num>.'."""
    m = re.match(r"Sec\.\s*[0-9][0-9A-Za-z\.\-]*\.\s+([A-Z][A-Z0-9 ,'\-/()&;.]+?)\.\s", block)
    if m:
        h = re.sub(r"\s+", " ", m.group(1)).strip()
        # Trim a trailing lone letter that is actually the start of subsection (a).
        return h
    return ""


# ---------------------------------------------------------------------------
# Cross-reference resolution
# ---------------------------------------------------------------------------

SEC_RE = re.compile(
    r"Section\s+(\d+\.\d+[0-9A-Za-z\-]*)"          # 1: section number
    r"(?:\([a-z0-9\-]+\))*"                          # optional subsection markers
    r"(?:\s*,?\s*(Tax|Education|Government|Local Government|Property|Insurance|"
    r"Health and Safety|Water|Transportation|Natural Resources|Occupations|Finance|"
    r"Agriculture|Estates|Family|Civil Practice and Remedies|Labor|Election|Utilities|"
    r"Human Resources|Parks and Wildlife)\s+Code)?"  # 2: optional explicit code
)
CONST_RE = re.compile(r"Article\s+([IVXLC]+)\s*,?\s+Section\s+([0-9][0-9A-Za-z\-]*)")


def resolve_xrefs(block: str, container_code: str) -> set[tuple[str, str, str]]:
    """Return the set of (code, chap, sec) cross-referenced from a section block."""
    refs: set[tuple[str, str, str]] = set()
    norm = re.sub(r"\s+", " ", block)
    for m in SEC_RE.finditer(norm):
        sec = m.group(1)
        codeword = m.group(2)
        code = CODE_WORD[codeword.lower()] if codeword else container_code
        if code == "CN":  # a "Section 1.2" style ref never means the constitution
            continue
        chap = sec.split(".")[0]
        refs.add((code, chap, sec))
    for m in CONST_RE.finditer(norm):
        art = ROMAN.get(m.group(1).upper())
        if art is not None:
            refs.add(("CN", str(art), m.group(2)))
    return refs


def slug(code: str, sec: str) -> str:
    return f"{code}-{sec}".replace(".", "-").replace("_", "-").lower()


def canonical_cite(code: str, sec: str) -> str:
    if code == "CN":
        return f"Tex. Const. art. VIII, §{sec}"
    return f"{CITE_ABBR.get(code, code)} §{sec}"


def public_url(code: str, chap: str, sec: str) -> str:
    return PUBLIC_BASE.format(code=code, chap=chap) + f"#{sec}"


# ---------------------------------------------------------------------------
# Phase 1: fetch + build graph
# ---------------------------------------------------------------------------

def fetch_chapter(client: httpx.Client, code: str, chap: str) -> str | None:
    url = FETCH_BASE.format(code=code, chap=chap)
    try:
        r = client.get(url)
    except Exception as e:  # noqa: BLE001
        print(f"[FETCH-ERR] {code}.{chap}: {e}", file=sys.stderr)
        return None
    if r.status_code != 200:
        print(f"[FETCH] {code}.{chap} -> HTTP {r.status_code}", file=sys.stderr)
        return None
    if "data-beasties-container" in r.text[:2000]:
        print(f"[FETCH] {code}.{chap} -> SPA shell (no static text)", file=sys.stderr)
        return None
    return html_to_text(r.text)


def do_fetch() -> int:
    # sections[(code, chap, sec)] = {block, heading, xrefs:set}
    sections: dict[tuple[str, str, str], dict] = {}
    fetched: set[tuple[str, str]] = set()
    chapter_meta: list[dict] = []

    def ingest_chapter(client, code, chap):
        if (code, chap) in fetched:
            return
        fetched.add((code, chap))
        text = fetch_chapter(client, code, chap)
        if not text:
            chapter_meta.append({"code": code, "chap": chap, "status": "MISS"})
            return
        secs = split_sections(text, code, chap)
        for sec, block in secs.items():
            key = (code, chap, sec)
            if key in sections:
                continue
            sections[key] = {
                "block": block,
                "heading": extract_heading(block),
                "xrefs": resolve_xrefs(block, code),
            }
        chapter_meta.append({"code": code, "chap": chap, "status": "OK", "sections": len(secs)})
        print(f"[FETCH] {code}.{chap} -> {len(secs)} sections")

    with httpx.Client(follow_redirects=True, timeout=60.0, headers=FETCH_HEADERS) as client:
        # 1) Fetch all target chapters.
        for code, chap in TARGET_CHAPTERS:
            ingest_chapter(client, code, chap)

        # 2) BFS over cross-referenced chapters (bounded) so referenced-out
        #    sections have real text to resolve against and to become nodes.
        for _ in range(MAX_LAYER):
            wanted: set[tuple[str, str]] = set()
            for meta in sections.values():
                for (rc, rch, _rs) in meta["xrefs"]:
                    if (rc, rch) not in fetched and rc in ABBR_NAME:
                        wanted.add((rc, rch))
            if not wanted:
                break
            for code, chap in sorted(wanted):
                if len(fetched) >= MAX_CHAPTERS:
                    print(f"[CAP] chapter fetch cap {MAX_CHAPTERS} reached", file=sys.stderr)
                    break
                ingest_chapter(client, code, chap)

    print(f"\nfetched {len([m for m in chapter_meta if m['status']=='OK'])} chapters, "
          f"{len(sections)} total sections split")

    # 3) Determine node set + layers via BFS from seeds over the cross-ref graph.
    target_codes = {(c, ch) for c, ch in TARGET_CHAPTERS}
    seed_keys = {(c, ch, s) for c, ch, s in SEEDS if (c, ch, s) in sections}

    layer: dict[tuple[str, str, str], int] = {}
    for k in seed_keys:
        layer[k] = 1

    # Layer 2: all target-chapter sections + direct refs of seeds.
    layer2: set[tuple[str, str, str]] = set()
    for key in sections:
        if (key[0], key[1]) in target_codes and key not in layer:
            layer2.add(key)
    for k in seed_keys:
        for ref in sections[k]["xrefs"]:
            if ref in sections and ref not in layer:
                layer2.add(ref)
    for k in layer2:
        layer[k] = 2

    # Layer 3: refs of layer-2 nodes not already placed.
    layer3: set[tuple[str, str, str]] = set()
    for k in list(layer2):
        for ref in sections[k]["xrefs"]:
            if ref in sections and ref not in layer:
                layer3.add(ref)
    for k in layer3:
        layer[k] = 3

    # Layer 4: refs of layer-3 nodes not already placed (min(bfs, 4)).
    layer4: set[tuple[str, str, str]] = set()
    for k in list(layer3):
        for ref in sections[k]["xrefs"]:
            if ref in sections and ref not in layer:
                layer4.add(ref)
    for k in layer4:
        layer[k] = 4

    nodes_keys = set(layer)
    # BFS distance sanity: keep only layers 1..MAX_LAYER (already guaranteed).

    # 4) Build node records + edges.
    nodes: dict[str, dict] = {}
    for key in sorted(nodes_keys):
        code, chap, sec = key
        sl = slug(code, sec)
        meta = sections[key]
        nodes[sl] = {
            "id": sl,
            "cite": canonical_cite(code, sec),
            "heading": meta["heading"],
            "layer": layer[key],
            "code": code,
            "chap": chap,
            "sec": sec,
            "source_url": public_url(code, chap, sec),
            "text": meta["block"],
            "xref_slugs": sorted({slug(rc, rs) for (rc, rch, rs) in meta["xrefs"]
                                  if (rc, rch, rs) in nodes_keys}),
        }

    edges = []
    seen_edges = set()
    for sl, n in nodes.items():
        for tgt in n["xref_slugs"]:
            e = (sl, tgt)
            if tgt in nodes and sl != tgt and e not in seen_edges:
                seen_edges.add(e)
                edges.append({"from": sl, "to": tgt, "kind": "cross_ref"})

    layer_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for n in nodes.values():
        layer_counts[n["layer"]] += 1

    corpus = {
        "generated_at": now_iso(),
        "proposed_change": PROPOSED_CHANGE,
        "chapter_meta": chapter_meta,
        "stats": {
            "sections_crawled": len(nodes),
            "total_sections_split": len(sections),
            "cross_refs_followed": len(edges),
            "chapters_fetched": len([m for m in chapter_meta if m["status"] == "OK"]),
            "layers": layer_counts,
        },
        "nodes": nodes,
        "edges": edges,
    }
    (OUT / "crawl-nodes.json").write_text(json.dumps(corpus, indent=1, ensure_ascii=False))

    # 5) Emit T1 + T2 jobs (flat herd lines).
    # Only emit jobs whose GLM output doesn't already exist, so re-runs reuse
    # the ~1,500 extractions already completed instead of paying for them again.
    t1 = JOBS / "t1_crawl.jsonl"
    t2 = JOBS / "t2_crawl.jsonl"
    t1_emitted = t2_emitted = 0
    with t1.open("w") as f1, t2.open("w") as f2:
        for sl, n in nodes.items():
            if not (OUT / f"t1c-{sl}.json").exists():
                f1.write(json.dumps({
                    "job_id": f"t1c-{sl}", "task": "T1",
                    "cite_hint": n["cite"], "source_url": n["source_url"], "text": n["text"],
                }, ensure_ascii=False) + "\n")
                t1_emitted += 1
            if not (OUT / f"t2c-{sl}.json").exists():
                f2.write(json.dumps({
                    "job_id": f"t2c-{sl}", "task": "T2",
                    "proposed_change": PROPOSED_CHANGE,
                    "rule_cite": n["cite"], "rule_text": n["text"],
                }, ensure_ascii=False) + "\n")
                t2_emitted += 1

    print(f"\n=== p4 fetch summary ===")
    print(f"nodes           : {len(nodes)}  (L1={layer_counts[1]} L2={layer_counts[2]} "
          f"L3={layer_counts[3]} L4={layer_counts[4]})")
    print(f"edges           : {len(edges)}")
    print(f"T1 jobs (new)   : {t1_emitted} -> {t1}")
    print(f"T2 jobs (new)   : {t2_emitted} -> {t2}")
    print(f"corpus          : {OUT / 'crawl-nodes.json'}")
    return 0


# ---------------------------------------------------------------------------
# Phase 2: assemble
# ---------------------------------------------------------------------------

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def do_assemble() -> int:
    corpus = json.loads((OUT / "crawl-nodes.json").read_text())
    nodes: dict[str, dict] = corpus["nodes"]

    # herd spend from the manifest (authoritative cumulative).
    glm_spend = 0.0
    glm_jobs = 0
    mf = OUT / "herd-manifest.jsonl"
    if mf.exists():
        for line in mf.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            glm_spend += r.get("cost", 0) or 0
            glm_jobs += 1

    sev_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    conflicted = []
    out_nodes = []
    t1_hits = t2_hits = 0

    for sl, n in nodes.items():
        heading = n["heading"]
        # T1 enrichment (heading fallback if regex missed it).
        t1p = OUT / f"t1c-{sl}.json"
        if t1p.exists():
            t1_hits += 1
            try:
                t1d = json.loads(t1p.read_text())
                if not heading and t1d.get("heading"):
                    heading = t1d["heading"]
            except Exception:  # noqa: BLE001
                pass

        node_out = {
            "id": sl,
            "cite": n["cite"],
            "heading": heading,
            "layer": n["layer"],
            "code": n["code"],
            "source_url": n["source_url"],
            "conflict_severity": 0,
            "analyzed": False,  # True only if a valid T2 conflict scan exists for this node
        }

        t2p = OUT / f"t2c-{sl}.json"
        if t2p.exists():
            t2_hits += 1
            try:
                t2d = json.loads(t2p.read_text())
                node_out["analyzed"] = True
                sev = int(t2d.get("severity", 0) or 0)
                is_conf = bool(t2d.get("conflict"))
                if not is_conf:
                    sev = 0
                sev = max(0, min(3, sev))
                node_out["conflict_severity"] = sev
                if sev > 0:
                    node_out["conflict_rationale"] = (t2d.get("rationale") or "")[:400]
                    node_out["quote"] = t2d.get("quote") or ""
                    conflicted.append((sev, sl, n["cite"], heading, node_out["conflict_rationale"]))
            except Exception:  # noqa: BLE001
                pass
        # Chapter of this section, for prune scoping (from the crawl corpus).
        node_out["_chap"] = n.get("chap", "")
        out_nodes.append(node_out)

    # ---- Prune to the homestead-relevant cascade, under the 2 MB cap ----
    # NEVER drop a conflicted node (all 54 conflicts, wherever they land, stay).
    # Keep the layer-1 seeds and the four codes that ARE the homestead ->
    # school-finance -> state-backfill cascade: Tax, Education, Constitution,
    # Government (LBB/Comptroller). Drop cross-ref spillover into unrelated codes
    # (Local Gov't, Water, Election, Family, ...) and out-of-spec layer-4 nodes.
    CASCADE_CODES = {"TX", "ED", "CN", "GV"}

    def keep(n: dict) -> bool:
        if n["conflict_severity"] > 0 or n["layer"] == 1:
            return True
        if n["layer"] >= 4:
            return False
        return n["code"] in CASCADE_CODES

    kept = [n for n in out_nodes if keep(n)]
    for n in kept:
        n.pop("_chap", None)
    kept_ids = {n["id"] for n in kept}
    edges = [e for e in corpus["edges"] if e["from"] in kept_ids and e["to"] in kept_ids]

    # Recompute stats on the kept set (honest denominators).
    sev_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    layer_counts: dict[int, int] = {}
    unscanned = 0
    for n in kept:
        sev_counts[n["conflict_severity"]] += 1
        layer_counts[n["layer"]] = layer_counts.get(n["layer"], 0) + 1
        if not n["analyzed"]:
            unscanned += 1
    # "analyzed" is a build-time flag, not part of the node schema — drop it.
    for n in kept:
        n.pop("analyzed", None)

    graph = {
        "stats": {
            "sections_crawled": len(kept),
            "sections_in_full_corpus": len(nodes),
            "cross_refs_followed": len(edges),
            "chapters_fetched": corpus["stats"]["chapters_fetched"],
            "conflicts_by_severity": {str(k): v for k, v in sev_counts.items()},
            "glm_jobs": glm_jobs,
            "glm_spend_usd": round(glm_spend, 4),
            "layers": {str(k): layer_counts.get(k, 0) for k in sorted(layer_counts)},
            "t1_extracted": t1_hits,
            "t2_scanned": t2_hits,
            "nodes_heading_only": unscanned,
            "proposed_change": corpus["proposed_change"],
        },
        "nodes": kept,
        "edges": edges,
    }
    outp = DATA / "conflict-graph.json"
    outp.write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")))
    size_mb = outp.stat().st_size / 1e6

    # Summary markdown.
    conflicted.sort(reverse=True)
    top = conflicted[:25]
    lines = [
        "# Gorgias conflict graph — summary",
        "",
        f"Proposed change: {corpus['proposed_change']}",
        "",
        f"Sections in graph: **{len(kept)}** (from a {len(nodes)}-section full crawl of "
        f"{corpus['stats']['chapters_fetched']} chapters, pruned to the property-tax / "
        f"school-finance cascade); cross-refs followed: **{len(edges)}**; layers "
        f"L1/L2/L3 = {layer_counts.get(1,0)}/{layer_counts.get(2,0)}/{layer_counts.get(3,0)}.",
        f"Conflicts by severity: 3={sev_counts[3]}, 2={sev_counts[2]}, 1={sev_counts[1]}, "
        f"0={sev_counts[0]} (of which {unscanned} heading-only / not GLM-scanned). "
        f"GLM: {glm_jobs} jobs, ${round(glm_spend,2)}.",
        "",
        "## Top conflicts",
    ]
    if top:
        for sev, sl, cite, heading, rat in top:
            lines.append(f"- **sev {sev}** — {cite} ({heading[:60]}): {rat[:160]}")
    else:
        lines.append("- (none returned severity > 0)")
    (DATA / "conflict-graph-summary.md").write_text("\n".join(lines) + "\n")

    print(f"=== p4 assemble summary ===")
    print(f"nodes kept       : {len(kept)} of {len(nodes)} crawled (T1 {t1_hits}, T2 {t2_hits})")
    print(f"conflicts       : sev3={sev_counts[3]} sev2={sev_counts[2]} sev1={sev_counts[1]} sev0={sev_counts[0]}")
    print(f"glm             : {glm_jobs} jobs, ${round(glm_spend,4)}")
    print(f"graph           : {outp}  ({size_mb:.2f} MB)")
    print(f"summary         : {DATA / 'conflict-graph-summary.md'}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if cmd == "fetch":
        sys.exit(do_fetch())
    elif cmd == "assemble":
        sys.exit(do_assemble())
    else:
        print("usage: p4_crawl.py [fetch|assemble]", file=sys.stderr)
        sys.exit(2)
