# GORGIAS — BUILD_PROMPT skeleton (sections owned by orchestrator)
# Final doc assembly order:
# 1. Mission & product definition (below)
# 2. Vulcan judge alignment (below)
# 3. Architecture (below)
# 4. Data pipeline  ← merge research/tx-data-sources.md
# 5. Vulcan corpus integration ← merge research/vulcan-surfaces.md
# 6. UI/UX spec ← merge research/ui-spec.md
# 7. Reusable assets ← merge research/local-assets.md
# 8. 2.5-hour execution timeline (below)
# 9. Agent orchestration plan (below)
# 10. Demo script & failure drills (below)
# 11. Risk register & scope guillotine (below)
# 12. Definition of done / QA checklist (below)

---

## 1. Mission

GORGIAS — a flight simulator for lawmaking. Named for the Greek rhetorician, in the classical-naming family of the hosts' Justinian and Trajan.

One sentence: type a proposed Texas policy change and watch it cascade through every statute it touches, every rule it conflicts with, every agency that must respond, every budget line it moves, and every county that feels it — each node citation-linked to the primary source, before a single vote is cast.

The thesis, said to the judges: democracy's real failure mode is passing laws nobody understood the consequences of. Everyone else in this room built a mirror for elections. We built a windshield for legislation.

Hero scenario (rehearsed, bulletproof): Texas homestead exemption $100,000 → $140,000.
- Statute chain: Tax Code §11.13, Education Code Ch. 48 (school finance hold-harmless), Gov't Code fiscal-note requirements.
- Budget cascade: school district M&O revenue → state hold-harmless obligation → Foundation School Program draw.
- County map: per-county levy impact (real comptroller data).
- Litigation exposure: school-finance suit history (Edgewood lineage) as the exposure narrative.
Backup scenarios (staged data, same UI): (a) eliminate occupational license for hair braiding; (b) raise rural broadband grant match.

Non-negotiables (from BRIEF.md, restated for every builder):
- #0A0A0A bg, gold #9D8B5E / #6C6042, border-radius 0 everywhere.
- Inter / JetBrains Mono / Archivo stacks, local fallbacks, ZERO external requests at demo time.
- Pure CSS/SVG. No canvas. No Chart.js. No emojis. Sentence case.
- Every visualized number scales proportionally to its real value.
- Every cascade node opens its source text — "grounded before generated" is the judges' religion; violating it in front of them is disqualifying.

## 2. Vulcan judge alignment (from RESEARCH.md — verified)

- Tanner Jones (CEO): ex-Cicero Institute regulatory policy, prior elections exit (Downballot). Gorgias speaks to the regulatory thread directly and demos on THEIR state (they just launched SAM with the Texas Regulatory Efficiency Office, May 2026).
- Their religion, verbatim from their site: "grounded before generated"; audit trails "an inspector general could reconstruct"; human approval gates on consequential actions.
- Pitch lines to use: "citation-linked", "human approval gate", "the path from question to source to answer is real and reviewable".
- Do NOT say: "legal cartography" (refuted framing), Virginia 25%/50% figures (refuted), Louisiana contract as public fact (unverified — table talk only).
- Positioning line: "Justinian reads the law as it is. Trajan serves the citizen as it is. Gorgias asks what happens if you change it — the third Roman in the room." (Gorgias is Greek; the founders will know; self-aware beat: "the Greek in the room keeps the Romans honest.")

## 3. Architecture

Decision rule for 2.5h: static-first, server-optional.

- Tier 0 (must ship): single self-contained `index.html` — all data for the hero scenario embedded as a JS object (`SCENARIO_HOMESTEAD`), full cascade/map/verdict experience offline. This is what demos even if wifi dies.
- Tier 1 (should ship): `pipeline/` Python scripts (bun-free zone; plain python3 + httpx) that scraped the real data and emitted the embedded JS object — shown in the repo to prove the data is real, run once before demo, not during.
- Tier 2 (stretch): FastAPI wrapper (`api.py`) with `/simulate?policy=...` calling Claude (claude-fable-5 or sonnet) with a structured-output prompt over the embedded corpus extracts, enabling ONE live free-text query in the demo. Feature-flagged; demo script works with it off.
- LLM usage: extraction and conflict-detection prompts run in Tier 1 preprocessing (before demo). Live inference only in Tier 2.
- Repo: /Users/j/Desktop/patriot-games-hackathon/gorgias/app/
  - index.html (Tier 0 artifact)
  - data/ (scenario JSON + county GeoJSON→SVG paths)
  - pipeline/*.py (scrapers + extractors, numbered in run order)
  - api.py (Tier 2, optional)
  - README.md (judges may look — write it like a product, cite every data source)

## 5b. GLM worker fleet (OpenRouter, $250 credits)

Model: GLM 5.2 via OpenRouter (the hosts' traditional model — say so in the demo; it's a nod they'll catch). Fable orchestrates; GLM does volume.

- Key handling: OPENROUTER_API_KEY env var only. Never written to any file, never committed, never echoed in logs. Repo gets a sanitizer pass before any push.
- Harness: `pipeline/herd.py` — asyncio + httpx fan-out. N=10 concurrent workers, each worker = one (task_type, chunk) job against openrouter chat completions, model `z-ai/glm-5.2` (verify exact slug at kickoff with a 1-token ping; fall back to latest GLM slug on OpenRouter). Retries: 2, exponential backoff. Per-job token cap 8k out. Budget guard: running cost estimate printed per batch; hard stop at $200 spend (leave $50 headroom).
- Worker instruction doc: `pipeline/WORKER_PROMPT.md` — the in-depth markdown brief every job embeds (role, task types, output JSON schemas, canonical citation format, "never invent a number; emit null + reason instead", examples per task type). Written by Fable before wave A; version-stamped so output provenance is traceable.
- Task types:
  - T1 statute_extract: raw statute/TAC HTML chunk → {cite, heading, operative_text, cross_refs[], defined_terms[]}
  - T2 conflict_scan: pairs of (proposed change, rule excerpt) → {conflict: bool, severity 0-3, rationale, quote}
  - T3 ocr_cleanup: scraped PDF text (fiscal notes, comptroller tables) → clean structured rows; flag low-confidence cells
  - T4 county_extract: comptroller table chunk → [{fips, county, levy, exemption_base}]
  - T5 agency_map: statute cites → {implementing_agency, action_required, statutory_deadline?}
- Validation: every GLM output passes a schema check (pydantic) + spot audit by Fable-side agent (B3). Failed jobs requeue once, then flagged "modeled" in UI rather than silently trusted. GLM is labor, not authority — citations must match source text verbatim (string-containment check against the scraped chunk).
- Why this shape: 10 sub-sessions of a cheap-fast model on chunked extraction beats one big context; matches how the hosts themselves run (per table conversation).

## 8. 2.5-hour execution timeline (hard gates)

- 0:00–0:15 — Scaffold: repo, index.html shell with design tokens, county SVG placed, scenario JS stub with FAKE-but-proportional numbers. Gate: page opens, looks premium, cascade renders with stub data.
- 0:15–1:00 — Parallel: (a) pipeline agents scrape hero-scenario real data; (b) cascade animation built against stub; (c) county map wired to stub. Gate at 1:00: animation complete end-to-end on stub data.
- 1:00–1:40 — Real data swap: pipeline output replaces stub. Numbers audited against sources (no invented figures — mark any unobtainable number "modeled" in the UI). Gate: hero scenario fully real or explicitly labeled.
- 1:40–2:00 — Verdict scene + citation side panels + demo keyboard flow (space advances scenes).
- 2:00–2:20 — Tier 2 live-query IF Tier 0/1 gates all passed. Otherwise polish.
- 2:20–2:30 — Freeze. Full demo rehearsal twice. No code after second rehearsal except text fixes.
- Scope guillotine (pre-agreed, in order of amputation): Tier 2 live query → backup scenarios → county hover tooltips → verdict export view. NEVER cut: cascade animation, citations panel, county map, hero numbers being real.

## 9. Agent orchestration (waves of 3–5, full context in every prompt)

- Wave A (0:00): A1 shell+tokens+map placement; A2 cascade SVG+animation engine (stub data contract below); A3 pipeline: statutes+TAC scrape; A4 pipeline: comptroller county levy data.
- Wave B (~0:45): B1 citations side panel + source-text embeds; B2 verdict scene; B3 data audit agent (every number → source URL table in README); B4 (conditional) api.py.
- Data contract (agents build against this, defined before Wave A): SCENARIO = {policy:{title,delta}, nodes:[{id,type:statute|conflict|agency|budget,label,cite,source_excerpt,parent,delta_usd}], counties:[{fips,name,impact_usd,impact_pct}], verdict:{exposure_pct,drivers:[...],next_steps:[...]}}.
- Orchestrator (this session) owns: integration, gates, rehearsal, README voice.

## 10. Demo script (90 seconds) & failure drills

[Beat-by-beat merged from ui-spec.md §8; drills:]
- Wifi dies → Tier 0 file:// run (rehearse this path FIRST).
- Judge asks "is this real data?" → click any node, source text + URL visible; README table on screen two.
- Judge asks "how would this use YOUR corpus?" → answer: nodes are corpus-type-tagged with Vulcan /coverage taxonomy [pending vulcan-surfaces.md findings]; "we built against public Texas sources in 3 hours — pointed at your 157B-record corpus it generalizes to all 50 states."
- Live query fails on stage → space-bar skips to precomputed hero scenario, line: "we'll take the one we grounded properly — that's the point of the product."

## 11. Risk register

- R1 Comptroller data format surprises → mitigation: A4 has fallback to top-25 counties hand-keyed from published PDF tables, labeled "modeled" for the rest.
- R2 Cascade animation eats the clock → mitigation: animation engine is CSS-class-driven stagger; if JS timing slips, static reveal with one transition still reads premium.
- R3 County SVG unavailable offline → mitigation: [pending r-tx-data / local-assets findings]; worst case a 254-cell county grid ("cartogram") — still proportional, still gold.
- R4 Vulcan-corpus reference reads as presumptuous → mitigation: attribution framed as homage ("corpus taxonomy after vulcan.ai/coverage"), never claim access we don't have.
- R5 Fable/API unavailability for Tier 2 → Tier 2 is flagged off by default.

## 12. Definition of done

- [ ] file:// open, zero network, full demo path
- [ ] Every displayed number: real+cited, or visibly labeled "modeled"
- [ ] Cascade: ≥12 nodes hero scenario, every node opens source panel
- [ ] County map: 254 counties, proportional gold ramp, top-10 strip matches map
- [ ] Two full rehearsals clean
- [ ] README: data-source table, agent-built-in-3h story, Gorgias naming note
- [ ] No emojis, no external fonts/CDNs, border-radius 0 audit (grep)
- [ ] Sanitizer pass if repo goes public (no keys, no PII)
