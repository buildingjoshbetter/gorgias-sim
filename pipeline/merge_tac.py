#!/usr/bin/env python3
"""Merge verified 34 TAC Title 1 Part 1 Chapter 9 (Comptroller Property Tax
Administration) sections into crawl-nodes.json as HEADING-ONLY nodes.

The sanctioned source (txrules.elaws.us) returned HTTP 503 for the entire run,
so verbatim rule text could not be retrieved. Per the failure policy, these
become heading-only nodes carrying no conflict analysis. Section numbers and
official catchlines below are taken from the elaws.us search index (verified
listings), not invented.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "out" / "crawl-nodes.json"

# (section, official catchline) — verified from the elaws.us TAC index.
TAC_CH9 = [
    ("9.101", "CONDUCT OF THE PROPERTY VALUE STUDY"),
    ("9.301", "APPRAISAL DISTRICT REVIEWS"),
    ("9.402", "SPECIAL USE APPLICATION FORMS"),
    ("9.1055", "COMPTROLLER APPLICATION REVIEW AND AGREEMENT TO LIMIT APPRAISED VALUE"),
    ("9.2004", "QUALIFICATION FOR AGRICULTURAL APPRAISAL BASED ON WILDLIFE MANAGEMENT USE"),
    ("9.3001", "APPRAISAL CARDS"),
    ("9.3003", "UNIFORM TAX RECORDS SYSTEM"),
    ("9.3040", "TAX CERTIFICATES"),
    ("9.4031", "MANUAL FOR DISCOUNTING OIL AND GAS INCOME"),
    ("9.4212", "ARBITRATION PROCEEDINGS"),
    ("9.4213", "SUBSTITUTION OF ARBITRATOR ASSIGNED TO ARBITRATION"),
    ("9.4241", "RBA DEPOSIT"),
    ("9.4261", "APPLICATION REQUIREMENTS"),
    ("9.5007", "AMENDMENT PROCESS"),
]

URL = "https://txrules.elaws.us/rule/title34_chapter9_sec.{sec}"


def main():
    corpus = json.loads(CORPUS.read_text())
    nodes = corpus["nodes"]
    added = 0
    for sec, heading in TAC_CH9:
        sl = f"tac-{sec.replace('.', '-')}"
        if sl in nodes:
            continue
        nodes[sl] = {
            "id": sl,
            "cite": f"34 TAC §{sec}",
            "heading": heading,
            "layer": 4,
            "code": "TAC",
            "chap": "9",
            "sec": sec,
            "source_url": URL.format(sec=sec),
            "text": "",  # heading-only: source unavailable, no verbatim text
            "xref_slugs": [],
        }
        added += 1
    st = corpus["stats"]
    st["sections_crawled"] = len(nodes)
    st["layers"]["4"] = st["layers"].get("4", 0) + added
    st.setdefault("tac_heading_only", 0)
    st["tac_heading_only"] += added
    CORPUS.write_text(json.dumps(corpus, indent=1, ensure_ascii=False))
    print(f"merged {added} heading-only 34 TAC Ch.9 nodes; total nodes now {len(nodes)}")


if __name__ == "__main__":
    main()
