# GORGIAS — BUILD_PROMPT.md
## A flight simulator for lawmaking · Patriot Games 250 · 2026-07-03

Orchestrator: Claude Fable (this session). Workers: 10x GLM 5.2 sub-sessions via OpenRouter ($250 credit, $200 hard stop) + Claude sub-agents in waves of 3-5.
Ship target: 2.5 hours from GO. Repo: /Users/j/Desktop/patriot-games-hackathon/gorgias/app/

STATUS: PLAN — awaiting Josh's confirmation. The OpenRouter key is NOT used until confirmed.

---

## Table of contents
1. Mission & product definition
2. Vulcan judge alignment
3. Architecture (Tier 0/1/2)
4. Data pipeline — verified Texas sources
5. Vulcan corpus integration (public surfaces only)
6. GLM 5.2 worker fleet (OpenRouter)
7. UI/UX specification (complete)
8. Reusable local assets
9. 2.5-hour execution timeline (hard gates)
10. Agent orchestration plan
11. Demo script & failure drills
12. Risk register & scope guillotine
13. Definition of done / QA

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

---

# 4. DATA PIPELINE — VERIFIED TEXAS SOURCES
(research: r-tx-data, all sources test-fetched)

# Gorgias — Texas Data Sources (verified)

Research date: 2026-07-03. Every source below was ACTUALLY test-fetched (curl / FireCrawl / WebFetch), not just listed. Sample responses and HTTP codes are real.

Legislature context: current session is **89R** (89th Legislature, Regular Session, 2025). There was also an 89th 2nd Called Session. Use `89R` for the demo.

Scrapeable score = "usable in 15 min", 1 (fight it) to 5 (trivial).

---

## TL;DR — the minimum set for the homestead demo

Demo scenario: raise homestead exemption (Tax Code §11.13) and show the cascade + per-county burden heat map.

| # | Source | What it powers | Format | Score |
|---|--------|----------------|--------|-------|
| 1 | Tax Code Ch. 11 HTML (§11.13) | The statute being changed | per-chapter HTML | 5 |
| 2 | Comptroller county rates/levies XLSX | Per-county levy → heat map | XLSX (56 KB) | 4 |
| 3 | plotly geojson-counties-fips.json (filter FIPS 48) | County map polygons | GeoJSON, 254 TX counties | 5 |
| 4 | TLO fiscal note HTML (HB9 89R = ad valorem exemption) | "Litigation/budget exposure" panel, real $ | server HTML | 5 |
| 5 | Collin CAD Socrata (per-parcel homestead flag) | Realism: real homestead parcels & values | Socrata JSON API | 5 |

Statutes + county levy XLSX + GeoJSON alone give one flawless demo. Fiscal note + Collin CAD add credibility. Everything else (TAC, TLO bill-status crawl) is optional polish.

---

## 1. Texas statutes full text — SCORE 5

Base: `https://statutes.capitol.texas.gov/Docs/TX/htm/TX.<CODE>.htm`

- **Per-chapter HTML files.** One file = one chapter of a code. No JS, plain server HTML.
- Tax Code Chapter 11 (contains **§11.13 residence homestead exemption**): `https://statutes.capitol.texas.gov/Docs/TX/htm/TX.11.htm`
  - Verified: returns **334 KB** of plain HTML (had to be sliced, too big for one read — that's how much full text it is). No JS render needed.
- Code abbreviations in the URL: `TX` = Tax Code, `ED` = Education, `GV` = Government, `LG` = Local Government, `PR` = Property, etc. Chapter number after the code.
- Section anchors within the chapter file are named like `11.13`.
- **How to use:** scrape the one chapter you need, regex-split on `Sec. 11.13.` headers. §11.13 is the homestead exemption; §11.26 (school tax limitation / "freeze") and Education Code Ch. 48 (school finance / recapture) are the natural cascade targets.
- JS render: NO. Size: tens–hundreds of KB per chapter. Scrapeable: **5** (but files are large — fetch only the chapters you cascade into).

Cascade seed for the demo (homestead $100k→$140k):
- Tax Code §11.13 (the exemption itself)
- Tax Code §11.26 (school district tax freeze for 65+/disabled — interacts)
- Education Code Ch. 48 (Foundation School Program — state must backfill lost local school revenue → this is the budget-line hit)
- Tax Code §26.04, §26.08 (rollback / voter-approval rate math)

---

## 2. Texas Administrative Code (TAC) — SCORE 2 (MOVED, deprioritize)

- OLD URL `https://texreg.sos.state.tx.us/public/readtac$ext.ViewTAC?...` now returns a **"This Site Has Moved"** redirect notice.
- New home: `https://texas-sos.appianportalsgov.com/rules-and-meetings?interface=LANDING_PAGE` — an **Appian portal**, JS-heavy, not clean-scrapeable in 15 min.
- Structure was Title / Part / Chapter / Rule (e.g. Title 34 = Public Finance, which holds Comptroller property-tax rules). That taxonomy still exists on the new portal but behind JS.
- **Recommendation:** skip TAC for the demo. If you need agency rules for the "conflicting rules → implementing agencies" step, hardcode the 2–3 relevant Comptroller PTAD rules (34 TAC Ch. 9) rather than live-scraping. Live scraping needs headless browser + Appian navigation = not a 15-min job.
- JS render: YES (Appian). Scrapeable: **2**.

---

## 3. Texas Legislature Online — bill text + status + fiscal notes — SCORE 5

All server-rendered HTML on `capitol.texas.gov`. Bill number is zero-padded to 5 digits.

**Bill history / status:**
`https://capitol.texas.gov/BillLookup/History.aspx?LegSess=<SESS>&Bill=<CHAMBER><NUM>`
- Example verified: `?LegSess=89R&Bill=HB2` → full action history, authors, sponsors, subjects, committee votes, links to Text / Actions / Amendments / Bill Stages. Server-rendered HTML tables, no JS framework.

**Bill full text (HTML):**
`https://capitol.texas.gov/tlodocs/<SESS>/billtext/html/<CHAMBER><NUM5><VER>.htm`
- Example verified: `https://capitol.texas.gov/tlodocs/89R/billtext/html/HB00002F.htm` → full enrolled bill text, plain HTML.
- Version codes: `I` introduced, `E` engrossed, `F`/enrolled, `A` amended. (HB2 89R = public school finance — directly relevant to homestead→school-recapture cascade.)

JS render: NO. Scrapeable: **5**.

---

## 4. LBB fiscal notes — SCORE 5 (HTML available, not just PDF)

Fiscal notes are hosted on TLO (capitol.texas.gov), authored by the Legislative Budget Board. **Both HTML and PDF exist** — use HTML.

- HTML: `https://capitol.texas.gov/tlodocs/<SESS>/fiscalnotes/html/<CHAMBER><NUM5><VER>.htm`
- PDF:  `https://capitol.texas.gov/tlodocs/<SESS>/fiscalnotes/pdf/<CHAMBER><NUM5><VER>.pdf`

Verified live examples (89R):
- `.../fiscalnotes/html/HB00009A.htm` — **HB9: exemption from ad valorem taxation** of tangible personal property (ad-valorem exemption bill — perfect analog for the homestead demo's fiscal-impact panel).
- `.../fiscalnotes/pdf/HB01515I.pdf` — LBB fiscal note PDF, standard "LEGISLATIVE BUDGET BOARD / Austin, Texas / FISCAL NOTE, 89TH LEGISLATIVE REGULAR SESSION" header.
- `.../fiscalnotes/html/HB04488A.htm` — funds/accounts dedication note.

The HTML renders as a clean table: five-year revenue impact by fund, methodology paragraph, "Local Government Impact" section. This is the real dollar cascade — parse the five-year table for the budget-line panel.

LBB portal (secondary, for discovery): `https://www.lbb.texas.gov/Fiscal_Notes.aspx`.

JS render: NO (TLO HTML). Scrapeable: **5**. Use HTML endpoint; fall back to PDF only if HTML 404s.

---

## 5. Comptroller / data.texas.gov open data — SCORE 4

**Socrata catalog API works** but federates across ALL Socrata domains — you MUST scope to data.texas.gov:
`https://data.texas.gov/api/catalog/v1?domains=data.texas.gov&search_context=data.texas.gov&q=<query>&only=dataset&limit=12`
- Verified: returns dataset IDs + names as JSON. Data rows: `https://data.texas.gov/resource/<id>.json?$limit=N` (SoQL: `$where`, `$select`, `$group`, `$limit`).
- Caveat: data.texas.gov does **not** host a clean statewide "property tax levy per county" dataset. The statewide levy data lives on comptroller.texas.gov as XLSX (see #6). Socrata's strength here is per-parcel appraisal data (Collin CAD, below).

**Collin CAD appraisal data (per-parcel, has homestead fields) — the realism source:**
- Dataset id `vffy-snc6` ("Collin CAD Appraisal Data - 2025"). Verified query: `https://data.texas.gov/resource/vffy-snc6.json?$limit=1`
- Real fields (verified): `exempthmstdflag`, `currvalmarket`, `currvalland`, `currvalimprv`, `currvalappraised`, `currvalassessed`, `currvalhscaploss` (homestead cap loss), `prevval*`, `entityschoolcode`, `situscity`, `situszip`, `ownername`.
- **This is gold for the demo:** filter `exempthmstdflag='Y'`, compute assessed-value delta when the exemption rises $100k→$140k, aggregate by `entityschoolcode`. Real parcels, real numbers, one county (Collin). Other CADs on the portal too, but Collin is complete.
- JS render: NO (JSON API). Scrapeable: **5** for Collin; **4** overall because there's no single statewide parcel dataset.

---

## 6. County-level data for the heat map — SCORE 4

**Primary: Comptroller Property Tax rates & levies, by county (XLSX).**
`https://comptroller.texas.gov/taxes/property-tax/docs/<YEAR>-county-rates-levies.xlsx`
- Verified: `2025-county-rates-levies.xlsx` → HTTP 200, **56 KB**, `application/octet-stream`. `2024-...` also 200 (55 KB).
- Sibling files (same page, same pattern): `-school-district-rates-levies.xlsx`, `-city-rates-levies.xlsx`, `-special-district-rates-levies.xlsx`, plus a combined file. Years 2021–2025.
- Index page: `https://comptroller.texas.gov/taxes/property-tax/rates/index.php` (verified links).
- Contains per-county tax rate + total levy. **This is the per-county $ burden for the heat map.** Small file, but XLSX → needs a parse step (SheetJS / openpyxl / pandas). ~5 min.
- JS render: NO (static file). Scrapeable: **4** (XLSX parse, not JSON).

**Secondary (population, optional):** Census ACS county population via `api.census.gov` or a static CSV. data.texas.gov's `q=county population` returns mostly HHS/CPS program datasets, not a clean population table — pull population from Census if needed, otherwise skip (levy alone drives the heat map).

Join key for the map: **county name / county FIPS** — both present in the Comptroller XLSX and the GeoJSON (#7).

---

## 7. County boundaries (offline SVG/GeoJSON) — SCORE 5

**Winner: plotly datasets US counties GeoJSON, filtered to Texas.**
`https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json`
- Verified: HTTP 200, **3.2 MB**, raw GeoJSON FeatureCollection, 3,221 US county features.
- Filter `properties.STATE == "48"` → **exactly 254 Texas counties** (verified count).
- Sample TX feature props (verified): `{"GEO_ID":"0500000US48357","STATE":"48","COUNTY":"357","NAME":"Ochiltree","LSAD":"County","CENSUSAREA":917.627}`.
- Join to levy data on `NAME` or FIPS (`48` + `COUNTY`). One `fetch()` at build time, filter to 254, embed inline for offline use (~1.5 MB after stripping non-TX).
- JS render: NO (raw file). Scrapeable: **5**.

**Alternatives (verified):**
- `Cincome/tx.geojson` — per-county files at `https://raw.githubusercontent.com/Cincome/tx.geojson/master/counties/individual/<County>_County.geojson` (e.g. `Bexar_County.geojson` → HTTP 200, 54 KB). 254 individual files; assemble if you want higher-detail polygons. The repo's combined `tx.geojson` is the **state** outline only (1 feature), NOT counties — don't use it for the map.
- `texas/maps` → `geojson/counties_2010.geojson` — full detail but **15.7 MB** (too heavy to embed). Skip.
- TxDOT Open Data ("Texas County Boundaries Detailed") — downloads currently disabled on the ArcGIS portal. Skip.

Recommendation: plotly file, filtered to FIPS 48. Simplest single-file path to an offline 254-county heat map.

---

## Build notes / gotchas

- **Fetch statute chapters selectively** — Tax Code Ch.11 alone is 334 KB. Don't crawl the whole code.
- **Scope Socrata to the domain** or you'll get King County WA, Fulton County GA, etc. in results.
- **TAC is behind an Appian JS portal now** — don't budget live-scraping time for it; hardcode the 2–3 Comptroller rules if needed.
- **Comptroller levy data is XLSX**, not JSON — add a parse step.
- **Join key is county NAME/FIPS** across the levy XLSX and the GeoJSON — normalize case/whitespace before joining.
- Prefer TLO **HTML** fiscal-note endpoint over PDF; fall back to PDF on 404.


---

# 5. VULCAN CORPUS INTEGRATION — PUBLIC SURFACES ONLY
(research: r-vulcan-surface)

# Vulcan public surfaces — integration research for Gorgias

Scope: PUBLIC, unauthenticated surfaces only. No auth bypass, no anti-bot evasion,
no undocumented/private backend probing. Everything below uses pages Vulcan and
the State of Texas have published for public consumption, at Vulcan's own hackathon.

Date: 2026-07-03. Researcher: Vulcan-surfaces probe (FireCrawl + Exa).

---

## TL;DR

- **SAM chatbot is real and public** at `https://efficiency.texas.gov` (prod alias
  `treo.texas.gov`), branded "Texas Legal Explorer," built by Vulcan Technologies
  (their "Trajan" product). English + Spanish. But the page is **gated behind a
  Cloudflare Turnstile human-verification challenge** — you cannot programmatically
  submit a question without solving Turnstile, which is out of scope (anti-bot
  evasion). **A human presenter CAN use it live in a browser.** That is the play.
- **`vulcan.ai/coverage` is the gold.** Fully public, static, scrapeable. A complete
  corpus inventory: **137 corpus types across 15 categories**, with exact record
  counts and per-corpus detail pages. This is directly mirror-able in the Gorgias UI.
- **Recommended integration:** (1) Gorgias authority-chain nodes each cite a Vulcan
  corpus type by its real name/count from `/coverage`; (2) live side-by-side SAM
  query during the demo, driven by a human, not our code. No private-API integration.

---

## 1. SAM — the Texas regulations/permits chatbot

### What it is
- Launched May 2026 by the Texas Regulatory Efficiency Office (TREO), built by Vulcan.
- SAM = "State Administration Manager." Public product name on-page: **Texas Legal Explorer**.
- Answers permit/license/regulation questions in **English or Spanish**, returns
  tables of license levels + fees, agency contacts, and a "not legal advice" disclaimer.
- Vulcan product line: this is **Trajan** (government AI concierge). Footer literally
  reads `© 2026 Vulcan Technologies | Trajan`.
- Confirmed by StateScoop (2026-05-15), gov.texas.gov press release, GovTech.

### URLs (all public)
- Chatbot / homepage: `https://efficiency.texas.gov`  (prod: `https://treo.texas.gov`)
- AI notice / specs: `https://efficiency.texas.gov/ai-notice`
- Reductions dashboard: `https://efficiency.texas.gov/dashboard`
- Per-page metadata calls it "Texas Legal Explorer — AI-powered explorer for Texas
  regulations, statutes, licensing, and permits."

### Is it usable / can we hit it programmatically?
- The page is a **Next.js app behind Cloudflare Turnstile**. Every load shows
  "Confirm you are not a robot / Verifying…" before the app renders. FireCrawl
  reached the DOM (the SAM widget "Message the assistant" is present) but the
  chat is behind the challenge.
- **The chat backend is an undocumented private endpoint** guarded by Turnstile.
  Submitting questions via script = solving/evading a bot challenge and hitting a
  non-public API. **Both are out of scope. Do NOT reverse-engineer or bypass.**
- Page is marked `robots: noindex, nofollow` — Texas does not want it indexed/crawled.
  Reinforces: treat as human-use-only, not a machine surface for us.

### What a human CAN legitimately do (in scope)
- Open `efficiency.texas.gov` in a normal browser, pass Turnstile like any citizen,
  and ask SAM a question live. This is using the tool exactly as published.
- **Verdict: no code integration. Live human demo only.**

---

## 2. vulcan.ai/coverage — the corpus browser (fully public, scrapeable)

This is the most useful surface by far. Static HTML, no gate, rich structure.

### Headline scale (as published on the page)
- **157 billion records** — "the biggest legal and policy database in the world"
- **137 corpus types** ("source families indexed")
- **15 categories** (legal + operational domains)
- **51 jurisdictions** (all 50 states + DC)
- **13.125 billion court records**

### The 15 categories and corpus counts (mirror-able taxonomy)
Each category below is a real node group; each has a landing description and links
to per-corpus detail pages at `vulcan.ai/coverage/{category}/{slug}`.

| Category | # corpora | Example corpus types (with real counts) |
|---|---|---|
| Legal | 27 | Federal Regulations (225M), State Regulations (95.4M), Federal Register (19.8M), State Court Records (13.1B), Citation Graph (5.37B), State Bills (50 states) |
| Local | 1 | Municipal Codes (every US municipal code) |
| Public Finance | 10 | Public Finance Records (26.6B), Federal Budget (1.95B), Federal Payroll (1.28B), Medicaid Waivers |
| Health | 7 | CMS Health Records (17.2B), CMS Medicaid Spending (7.95B), CMS Manuals, Coverage Determinations |
| Environment | 7 | EPA Environmental Records (3.17B), EPA Operational Compliance (1.83B), EPA SDWA/SDWIS (685M) |
| Energy | 4 | FERC Energy Transactions (4.06B), Federal Energy Grid (2.84B), EIA Energy Data (1.79B) |
| Labor | 4 | BLS Labor Observations (4.79B), Form 5500 ERISA (1.06B), NLRB (9.8M), EEOC (441K) |
| Education | 3 | K-12 Education Metrics (4.08B), ED/NCES (1.05B), Texas TEA/K-12 (2.45B) |
| Public Safety | 4 | Policing Records (4.78B), FBI UCR (1.6M), ATF FFL/Trace (43.2M), NHTSA (29.4M) |
| Transportation | 6 | FMCSA (540M), BTS On-Time (37.1M), FHWA Bridge/Highway (21.8M), FAA Airports (1.7M) |
| Agriculture | 4 | Agriculture Records (12.3B), USDA FNS/SNAP (39.7M), NRCS Easements (816K) |
| Disclosures | 9 | FEC Campaign Finance (2.77B), FCC ULS Licenses (1.37B), CFPB Complaints (529M), IRS 990 (~245M) |
| Reference | 13 | FEMA (974M), Census ACS (51.1M), HUD Housing (10.1M), NIH RePORTER (2.8M), Permit Forms |
| Louisiana | 32 | LDEQ TEMPO (1.02B), LA Campaign Finance (209M), LA SOS Elections (112M), LaGov Procurement (100M) |
| Louisiana Energy & Conservation | 6 | SONRIS Wells (2.37B), Well Bonds (3.2M), SONRIS UIC Applications |

(Note: the page's own "137 corpus types / 15 categories" headline vs. the rows above
sums slightly differently in places — the page is authoritative; cite its headline
numbers verbatim.)

### Per-corpus detail pages
Each corpus links to a detail page, e.g.:
- `vulcan.ai/coverage/legal/federal-regulations`
- `vulcan.ai/coverage/legal/citation-graph`
- `vulcan.ai/coverage/health/cms-health-records`
- `vulcan.ai/coverage/environment/epa-sdwa`

These are scrapeable if we want per-node source detail (jurisdictional scope,
document/data types, volume notes). Fully public.

### What we can mirror in Gorgias UI (all legitimate — published data)
- A "built on the same sources Vulcan indexes" panel: reproduce the 15-category /
  137-corpus taxonomy as our authority-chain source inventory.
- Each Gorgias authority-chain node cites a real Vulcan corpus type + count
  (e.g., a rule node → "Federal Regulations · 225M records · CFR" linking to the
  `/coverage/legal/federal-regulations` page).
- Headline stat row echoing Vulcan's: 157B records / 137 corpus types / 51 jurisdictions.

---

## 3. vulcan.ai site map — other public surfaces

FireCrawl map of `vulcan.ai` returned ~50 public URLs. Relevant ones:
- Product pages: `/agents/justinian`, `/agents/trajan` (Trajan = SAM's engine),
  `/government`, `/commercial`, `/fedramp`, `/security`.
- Justinian runs on "157 billion records across American law and policy" (matches coverage).
- Release notes: `/justinian/2-1-7-update` … `/justinian/2-0-0-update`, `/justinian/18-4-update`.
- Vertical solution pages under `/gov/*` and `/commercial/*` (permits, budget,
  interpretation, red-tape, etc.) — good language to borrow for Gorgias framing.
- **No public JSON/API docs, no OpenAPI, no developer portal found.** Marketing site only.
- `/coverage` is the only machine-useful data surface. No public query API exists.

---

## 4. Feasibility in 2.5h + recommendation

### Not feasible / out of scope
- Programmatic SAM queries — Turnstile-gated + undocumented private backend. Skip entirely.
- Any Vulcan "API" — none is published.

### Feasible now (do this)
1. **Corpus-mirror (primary, ~30–45 min):** scrape `vulcan.ai/coverage` once (done —
   data is in this file), hardcode the 15-category / 137-corpus taxonomy + counts into
   Gorgias. Each authority-chain node cites a real corpus type, name, count, and links
   to its `/coverage/...` page. Frames Gorgias as "running on the same source families
   Vulcan indexes." Zero external runtime dependency; nothing can break in the demo.
2. **Live SAM side-by-side (secondary, demo-time, human-driven):** presenter opens
   `efficiency.texas.gov` in a real browser, asks SAM the same policy question Gorgias
   simulates, shows them side by side. Legitimate public use, and it flatters the host.
   Rehearse it (Turnstile + ~15s answer latency); have a screen-recording fallback in
   case wifi/Turnstile misbehaves live.

### Recommended integration (final)
- **Primary:** static corpus-citation layer sourced from `/coverage` (in-scope, robust).
- **Fallback/complement:** live human SAM demo side-by-side (in-scope, high-impact,
  no code). Record a backup video.
- **Explicitly avoid:** SAM backend calls, Turnstile bypass, any private endpoint.

### Data already captured for the build
- Full 15-category / 137-corpus list with counts is in Section 2 above — enough to
  build the Gorgias source-citation UI without re-scraping.


---

# 6. GLM 5.2 WORKER FLEET

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

---

# 7. UI/UX SPECIFICATION
(research: r-ui-spec — every value concrete)

# GORGIAS — UI/UX Specification

> A flight simulator for lawmaking. Type a proposed Texas policy change; watch it cascade through statutes, rule conflicts, agencies, budget lines, a 254-county burden map, and litigation exposure — every node grounded in a citation from the Vulcan corpus.

Status: build spec, v1. Target: 2.5-hour hackathon build, demo on a projector (16:9, 1080p) at distance.
Authoring note: written from the team-lead brief + design system. The three seed files (`BRIEF.md`, `RESEARCH.md`, `concepts/06-statecraft-simulator.html`) were not machine-readable in this environment (macOS TCC blocked read of pre-existing Desktop files); all design tokens below are reproduced from the brief and are authoritative. If the seed concept's cascade markup differs, prefer this spec — it is self-contained.

Every value here is concrete: px, ms, hex, easing. A builder must not have to ask a question.

---

## 0. Design language (non-negotiable)

Inherited from the hackathon design system. Do not deviate.

- Background `#0A0A0A`. Gold accent `#9D8B5E`. Secondary gold `#6C6042`.
- `border-radius: 0` everywhere. No rounded corners, ever. No soft shadows used as decoration.
- Pure CSS/SVG only. No `<canvas>`, no Chart.js, no D3, no charting library. Every chart, gauge, map, and connector is hand-authored SVG or CSS.
- No emojis. No icons from icon fonts. If a glyph is needed, draw it in SVG or use a monospace character.
- Dramatic typography. Monospace texture (JetBrains Mono) is the premium signal, used at scale — labels, citations, counters, coordinates. Not playful terminal cosplay; restrained and intentional.
- Fonts: Inter (body/UI), JetBrains Mono (mono/data/citations), Archivo (display/wordmark). Local fallbacks below — the demo machine may be offline.
- Reference family: Oxide.computer, Vercel, Cohere, Linear. Restrained, high-contrast, editorial.

### Font stacks (with offline fallbacks)

```css
--font-display: "Archivo", "Helvetica Neue", Arial, sans-serif;
--font-body:    "Inter", -apple-system, "Segoe UI", Roboto, sans-serif;
--font-mono:    "JetBrains Mono", "SF Mono", "Menlo", ui-monospace, monospace;
```

Load fonts with `font-display: swap`. If web fonts fail, the system fallbacks carry the layout without reflow breakage. Never let a font 404 stall first paint — the demo cannot afford a blank screen.

---

## 1. App shell

### 1.1 Layout model

Single-page application. One `<main id="stage">` that holds four full-viewport scenes stacked in the DOM; only one is `.is-active` at a time. Scenes do not scroll the page — each scene fits 1920×1080 with no vertical scroll at demo resolution. Internal panels (citation drawer, county strip) scroll inside their own `overflow` containers only.

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER  (fixed, 96px)                                        │
│   GORGIAS            a flight simulator for lawmaking        │
│                      grounded in the Vulcan statutory corpus │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   STAGE  (fills remaining height)                           │
│     scene-console | scene-cascade | scene-map | scene-verdict│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ FOOTER  (fixed, 56px)                                        │
│   scene dots ● ○ ○ ○     SPACE ADVANCE · R RESET · esc       │
│                          254 counties · TX 88th Leg. corpus  │
└─────────────────────────────────────────────────────────────┘
```

Grid: `grid-template-rows: 96px 1fr 56px; height: 100vh;` on the app root. No horizontal page scroll ever — `body { overflow: hidden; }` at demo sizes; `overflow-x: hidden` always.

### 1.2 Header

- Height 96px, `border-bottom: 1px solid var(--hairline)`, background `#0A0A0A`.
- Left: wordmark `GORGIAS` in Archivo, `font-size: 34px`, `font-weight: 800`, `letter-spacing: 0.14em`, color `--text`. Uppercase.
- Immediately right of wordmark, a 1px vertical hairline divider (28px tall), then a two-line block in JetBrains Mono:
  - Line 1: `a flight simulator for lawmaking` — `13px`, color `--gold`, `letter-spacing: 0.04em`.
  - Line 2 (attribution, the "grounded" proof): `grounded in the Vulcan statutory corpus · TX Tax/Gov/Local Gov codes` — `11px`, color `--text-dim`.
- Right edge: a live corpus status pill, JetBrains Mono `11px`, `border: 1px solid var(--hairline)`, `padding: 4px 10px`: `CORPUS ONLINE · 41,882 sections`. A 6px gold square (not a dot — `border-radius: 0`) sits left of the text, pulsing opacity 0.4↔1.0 over 2000ms. If offline mode is active, text reads `CORPUS CACHED` and the square is `--gold-2`.

### 1.3 Footer

- Height 56px, `border-top: 1px solid var(--hairline)`.
- Left: scene indicator — four 10px squares, 12px gap. Active = filled `--gold`; visited = `--gold-2`; unvisited = `1px solid var(--hairline)` hollow. Labels under, JetBrains Mono `10px` uppercase: `CONSOLE · CASCADE · MAP · VERDICT`.
- Center/right: keyboard legend, JetBrains Mono `11px`, `--text-dim`: `SPACE ADVANCE   ←/→ SCENE   R RESET   C CITATIONS   ESC CONSOLE`. Keys rendered in `--text`, actions in `--text-dim`.

### 1.4 Responsive / projector behavior

- Primary target: 1920×1080, viewed from 3–8 meters. Type scale below is tuned for this — nothing load-bearing under 13px on the projector; the fiscal counter and scene headings are deliberately huge (48–104px) for legibility at distance.
- Breakpoints:
  - `≥1600px` (projector, laptop-to-projector): full scale as specified.
  - `1200–1599px` (presenter laptop): multiply the type scale by 0.85 via a `--scale: 0.85` custom property applied to `font-size` on `:root` through `clamp()`; cascade node width shrinks from 260px to 220px.
  - `<1200px` (fallback only, not a demo target): scenes become vertically scrollable, cascade collapses to a single column, map drops the county strip below the SVG. This path is a safety net, not polished.
- Use `clamp()` on the big display numbers so they never overflow: e.g. fiscal counter `font-size: clamp(48px, 6vw, 104px)`.
- All wide content (county strip, citation source text, cascade SVG) lives in `overflow: auto` containers so the page body never gains a scrollbar.
- Respect `prefers-reduced-motion`: cascade animation collapses to a 400ms cross-fade with all nodes already in place; counters snap to final value; pulses stop.

---

## 2. Scene 1 — The Console (policy input)

The calm before the cascade. This scene must read as an instrument panel, not a search box.

### 2.1 Layout

Centered column, `max-width: 1100px`, vertically centered in the stage.

1. Kicker (JetBrains Mono `13px`, `--gold`, `letter-spacing: 0.22em`, uppercase): `TEXAS POLICY IMPACT SIMULATOR`.
2. Headline (Archivo, `clamp(40px, 4.4vw, 68px)`, weight 800, line-height 1.02, `--text`): `Propose a change. See what it breaks.`
3. Subhead (Inter, `20px`, `--text-dim`, `max-width: 720px`): `Gorgias traces a proposed statutory change through every downstream rule, agency, budget line, and county — and shows you the litigation you just bought. Every node is grounded in the source text.`
4. Scenario cards row (see 2.2).
5. Free-text field (see 2.3).
6. Run affordance (see 2.4).

Vertical rhythm between blocks: 32px, except headline→subhead 20px, cards→field 40px.

### 2.2 Prewritten scenario cards

Three cards in a `grid-template-columns: repeat(3, 1fr); gap: 20px`. The first is the hero (pre-selected on load). Cards are the primary demo path — the field exists to prove it is not hardcoded.

Card geometry: `border: 1px solid var(--hairline)`, `border-radius: 0`, `padding: 24px`, `background: #0C0C0C`, `min-height: 200px`, `cursor: pointer`. On hover: `border-color: var(--gold)`, a 2px gold top-edge bar animates in (`transform: scaleX(0)→1`, 180ms). Selected card: `border-color: var(--gold)`, top-edge bar solid, `background: #0E0D0A`, and a JetBrains Mono `10px` `SELECTED` tag top-right in `--gold`.

Card content:
- Index tag top-left, JetBrains Mono `11px` `--text-dim`: `01 / HERO`, `02`, `03`.
- Title, Archivo `22px` weight 700 `--text`.
- One-line premise, Inter `15px` `--text-dim`.
- Footer row, JetBrains Mono `11px`: predicted-magnitude teaser — `~$X.XB statewide · N agencies · M conflicts`.

Exact card copy:

**Card 01 — HERO**
- Title: `Raise the homestead exemption`
- Premise: `Increase the residence homestead exemption from $100,000 to $140,000 of appraised value.`
- Footer teaser: `~$3.1B/yr shifted · 4 agencies · 3 statutory conflicts`
- Canonical policy string fed to engine: `Amend Tax Code §11.13(b): increase general residence homestead exemption from $100,000 to $140,000.`

**Card 02 — BACKUP A**
- Title: `Cap local property-tax growth`
- Premise: `Lower the voter-approval tax rate trigger for cities and counties from 3.5% to 2.5%.`
- Footer teaser: `~$1.4B/yr constrained · 5 agencies · 2 conflicts`
- Canonical string: `Amend Tax Code §26.07 / §26.075: reduce voter-approval rate de minimis from 3.5% to 2.5% for taxing units.`

**Card 03 — BACKUP B**
- Title: `Universal school ESA vouchers`
- Premise: `Create Education Savings Accounts of $10,000 per student, funded from the Foundation School Program.`
- Footer teaser: `~$4.6B/yr redirected · 6 agencies · 5 conflicts`
- Canonical string: `Create Education Code Ch. 29 Subch. J: $10,000 ESA per eligible student, drawn on the Foundation School Program.`

The teasers are the pre-computed results; when a card is run, the cascade and map reproduce these totals exactly. Keep them consistent across scenes — the fiscal counter in Scene 2 must land on the card's stated figure.

### 2.3 Free-text field

- Full-width, `border: 1px solid var(--hairline)`, `border-radius: 0`, `background: #0C0C0C`, `padding: 20px 24px`.
- Placeholder (Inter `18px`, `--text-faint`): `Or describe your own change — "double the franchise tax exemption to $2.47M"`
- Focus state: `border-color: var(--gold)`, a 1px inner gold line (`box-shadow: inset 0 0 0 1px var(--gold)` — shadow used structurally, not decoratively). A blinking JetBrains Mono block caret is fine.
- Left of the field, a JetBrains Mono `13px` `--gold` prompt marker `TX>` acts as the instrument prompt.
- Typing here deselects the cards (removes their SELECTED state) and enables Run.

### 2.4 Run affordance

- Primary button, right-aligned under the field. `background: var(--gold)`, `color: #0A0A0A`, Archivo `16px` weight 700, `letter-spacing: 0.08em`, `padding: 16px 40px`, `border-radius: 0`, `border: 0`. Label: `RUN SIMULATION →`.
- Hover: `background: #B4A06E` (lightened gold), no radius change.
- Keyboard: `SPACE` or `Enter` triggers Run when this scene is active. Focus ring is a 2px `--gold` outline offset 3px (never remove focus outlines — demo-safe accessibility).
- On Run: brief 500ms "compiling" state — button label swaps to `TRACING…` with an animated 3-dot ellipsis (JetBrains Mono), then scene transitions to Cascade.

---

## 3. Scene 2 — The Cascade (the wow moment)

A single proposed change fans out downward through five strata. A wave of activation sweeps top-to-bottom over ~9 seconds while a fiscal counter spins up. This is the shot the judges remember. "Grounded before generated" is proven here: every node is clickable and opens its exact source text.

### 3.1 Strata (top → bottom)

```
              [ POLICY ]            ← the proposed change (1 node)
             /    |    \
        [STATUTE][STATUTE][STATUTE] ← amended/affected sections (3–5)
             \    |    /
          [CONFLICT] [CONFLICT]     ← rule collisions, flagged gold (1–3)
             /    |    \
        [AGENCY][AGENCY][AGENCY]    ← implementing bodies (3–5)
             \    |    /
     [BUDGET][BUDGET][BUDGET][BUDGET] ← fiscal lines w/ $ deltas (3–6)
```

Layout is an SVG (`viewBox="0 0 1600 900"`, `preserveAspectRatio="xMidYMid meet"`) that fills the stage. Five horizontal bands, y-centers at 90, 300, 470, 640, 820. Nodes are horizontally distributed within each band with equal gaps; band is centered.

### 3.2 Node geometry

All nodes are rectangles, `border-radius: 0`. Rendered as SVG `<g>` groups: a `<rect>` + `<text>` layers, or as `<foreignObject>` wrapping an HTML card for easier text flow (prefer `<foreignObject>` at 260×88px so we get real text wrapping and the mono/inter mix).

Base node: width 260px, height 88px (policy node 340×104px). `fill: #0C0C0C`, `stroke: var(--hairline)`, `stroke-width: 1`. Inside:
- Top-left kicker, JetBrains Mono `10px` `--text-dim`, the stratum tag: `STATUTE`, `AGENCY`, `BUDGET LINE`, `CONFLICT`.
- Title, Inter `15px` weight 600 `--text`, max 2 lines with ellipsis.
- Citation chip (statute/conflict/agency nodes) OR dollar delta (budget nodes) bottom row.

**Citation chip:** JetBrains Mono `11px`, `padding: 2px 7px`, `border: 1px solid var(--gold-2)`, `color: var(--gold)`, `background: rgba(157,139,94,0.06)`. Text e.g. `Tax Code §11.13(b)`. Chip has a tiny 5px gold square at its left as a "source anchor" mark. Clicking the chip (or node) opens the citation drawer (3.6).

**Policy node** (top): `stroke: var(--gold)`, `stroke-width: 2`, kicker `PROPOSED CHANGE`, title in Archivo `18px` weight 700. Carries a subtle gold underglow via `stroke` only (no blur decoration).

**Conflict node:** the alarm state. `stroke: var(--gold)`, `stroke-width: 2`, kicker `⚠ CONFLICT` rendered as `CONFLICT` in `--gold` (no emoji — use a drawn 12px SVG triangle-with-bang to the left of the word). `background: #0E0D0A`. Title states the collision, e.g. `Exemption change collides with school-funding hold-harmless formula`. On appearance it flashes: opacity 0.3→1 with a single 220ms gold border pulse.

**Budget node:** bottom row. Instead of a citation chip, a dollar delta: JetBrains Mono `18px` weight 600. Negative (cost/loss) in `--gold`; offsetting/positive in `--text`. Format `−$1.62B/yr`, `+$480M/yr`. A 4px-tall CSS bar beneath the number whose width encodes magnitude proportionally (see 3.5) — bar width must be proportional to the real number, never a fixed block.

### 3.3 Connectors

SVG `<path>` cubic Béziers from the bottom-center of each parent node to the top-center of each child it feeds. `stroke: var(--hairline)`, `stroke-width: 1`, `fill: none`. When the activation wave reaches a connector, it "charges": a temporary overlay path with `stroke: var(--gold)`, `stroke-width: 1.5`, animated via `stroke-dasharray`/`stroke-dashoffset` from full-offset to 0 over 420ms (draw-on effect), then the overlay fades to `--gold-2` and stays as a "traced" edge (so the final frame shows the full lit tree). Conflict-feeding edges stay `--gold`, `stroke-width: 2`.

### 3.4 Animation timeline (total ≈ 9200ms)

Driven by JS orchestrating class toggles (not one monolithic CSS animation — we need per-node stagger and the counter sync). Each node starts at `opacity: 0; transform: translateY(12px)` and animates to `opacity: 1; translateY(0)` over 380ms with easing `cubic-bezier(0.16, 1, 0.3, 1)` (a decisive ease-out). Connectors charge 60ms after their parent node settles.

Stagger schedule (ms from scene enter):

| t (ms) | Event |
|-------:|-------|
| 0      | Policy node fades/rises in; fiscal counter mounts at `$0` |
| 500    | Policy→statute connectors charge |
| 900    | Statute nodes appear, staggered 140ms apart (3–5 nodes) |
| 1900   | Statute→conflict connectors charge (gold) |
| 2300   | Conflict nodes appear + flash; counter begins ramp |
| 3100   | Conflict→agency connectors charge |
| 3500   | Agency nodes appear, staggered 120ms |
| 4600   | Agency→budget connectors charge |
| 5000   | Budget nodes appear, staggered 160ms; each budget node's arrival adds its delta to the counter |
| ~7600  | Last budget node settles |
| 7600–9000 | Counter eases to final total; a `SETTLED` stamp fades in over the counter |
| 9000   | Scene fully "lit"; footer hint pulses `SPACE → COUNTY MAP` |

The wave feel comes from each stratum's connectors charging just before its nodes appear, so light visibly travels down. Total is tunable via one `--cascade-speed` multiplier (default 1.0) if the demo needs to be faster; keep between 7000–11000ms.

### 3.5 Running fiscal counter

- Fixed top-right of the cascade scene, inside the stage (not the header). JetBrains Mono, `font-size: clamp(48px, 6vw, 104px)`, weight 700, `--text`, `font-variant-numeric: tabular-nums` so digits don't jitter.
- Label above it, JetBrains Mono `12px` `--text-dim` uppercase: `NET STATEWIDE FISCAL IMPACT · ANNUAL`.
- Sign + magnitude: leading `−` in `--gold` when net cost. Format with thousands separators while spinning, collapse to `−$3.10B/yr` at settle. Show the long form (`−$3,104,880,000`) mid-spin for drama, then morph to abbreviated `−$3.10B/yr` on settle (a 300ms cross-fade between the two text nodes).
- Ramp behavior: not linear. Counter increments as each budget node lands (stepped jumps synced to 3.4), then a final `requestAnimationFrame` ease (cubic ease-out, ~1200ms) closes the gap to the exact card total. Never overshoot; never show a value that contradicts the card teaser.
- Magnitude bars under budget nodes are normalized: `bar_width_px = 8 + (abs(delta) / max_abs_delta) * 172` (min 8, max 180). Proportional to real values — required.

### 3.6 Citation drawer ("grounded before generated")

The single most important proof for these judges. Every statute, conflict, agency, and budget node is clickable; clicking slides in a right-side drawer with the source.

- Drawer: fixed right, width 460px, full stage height, `background: #0B0B0B`, `border-left: 1px solid var(--gold-2)`. Slides in via `transform: translateX(100%)→0` over 260ms `cubic-bezier(0.16,1,0.3,1)`. A 1px gold left edge. `overflow-y: auto` inside.
- Header: node title (Inter `18px` weight 700) + citation chip repeated (JetBrains Mono). A close `×` (drawn, not emoji) top-right, and key hint `C / ESC`.
- Provenance line, JetBrains Mono `11px` `--text-dim`: `SOURCE · Vulcan corpus · TX Tax Code · §11.13(b) · retrieved verbatim`.
- Body: the verbatim statute text in a `blockquote`-styled block — `border-left: 2px solid var(--gold-2)`, `padding-left: 16px`, Inter `15px`, `--text-dim`, line-height 1.6. This is quoted source, so a left rule and quote styling is correct (blockquotes only for verbatim source — matches house style). The queried/changed clause is wrapped in a `<mark>` with `background: rgba(157,139,94,0.16); color: var(--text)` so the exact touched language is highlighted.
- For conflict nodes: two stacked source blocks (Statute A vs Statute B) with a gold `COLLISION` divider between them and one plain-language sentence, Inter `14px` `--text`, explaining the incompatibility. Label it `GROUNDING`, never "AI says" — the sentence cites both sections.
- Footer of drawer: `NEXT STEP` micro-panel — which agency must reconcile this, foreshadowing Scene 4.
- Opening the drawer pauses the cascade animation if still running; closing resumes. Space still advances scenes; `C` toggles drawer on the currently-focused node (focus ring cycles nodes via Tab).

### 3.7 Data contract for a cascade

A scenario resolves to this JSON (pre-baked per card; the free-text path calls the model, falls back to hero card on failure):

```json
{
  "policy": { "title": "...", "citation": "Tax Code §11.13(b)" },
  "statutes":  [{ "id":"s1","title":"...","citation":"Tax Code §11.13(b)","source":"<verbatim>","touchedClause":"$100,000" }],
  "conflicts": [{ "id":"c1","title":"...","a":"s1","b":"Education Code §48.2551","explain":"...","sourceA":"...","sourceB":"..." }],
  "agencies":  [{ "id":"a1","name":"Texas Comptroller","citation":"Gov Code §403","role":"...","clockDays":180 }],
  "budgets":   [{ "id":"b1","line":"School district M&O replacement","delta": -1620000000, "citation":"Education Code §48.2542","source":"..." }],
  "edges":     [["policy","s1"],["s1","c1"],["c1","a1"],["a1","b1"]],
  "totals":    { "net": -3104880000, "netLabel": "−$3.10B/yr" },
  "litigation":{ "score": 72, "band": "HIGH", "vectors":[ ... ] },
  "counties":  { "TX_453": 0.91, "TX_201": 0.64, "...": 0.0 }
}
```

Pre-bake all three cards fully. The counter total (`totals.net`) must equal the card footer teaser.

---

## 4. Scene 3 — The Map (254-county burden)

Statewide abstraction becomes local and visceral: every Texas county shaded by how hard this change hits it.

### 4.1 Layout

- Left ~72%: the Texas choropleth SVG. Right ~28%: the top-10 counties strip + legend + summary stat.
- Scene heading top-left, Archivo `clamp(30px, 3.2vw, 48px)` weight 800: `Where it lands.` Sub, Inter `18px` `--text-dim`: `Per-county change in effective burden. Darker gold = larger shift.`

### 4.2 The choropleth

- Inline SVG of all 254 Texas counties as `<path>` elements, each `id="TX_###"` (FIPS) and `class="county"`. Source the path data from a public-domain Texas counties TopoJSON/SVG converted to a single `viewBox` (roughly `viewBox="0 0 1000 1000"`, `preserveAspectRatio="xMidYMid meet"`). Bundle the path data as a static JS constant so the map never depends on a network fetch at demo time.
- Base county: `fill: #141310`, `stroke: #0A0A0A`, `stroke-width: 0.75` (so counties read as separated tiles, matching the border-radius-0 tile language).
- Fill by intensity `v` in [0,1] via a discrete 6-step gold ramp (discrete reads better at distance than continuous):

| step | v range     | fill      |
|-----:|-------------|-----------|
| 0    | 0.00–0.05   | `#141310` |
| 1    | 0.05–0.20   | `#3A3220` |
| 2    | 0.20–0.40   | `#5A4E2E` |
| 3    | 0.40–0.60   | `#7C6C3E` |
| 4    | 0.60–0.80   | `#9D8B5E` |
| 5    | 0.80–1.00   | `#C7B37A` |

- Counties fill in with a 900ms staggered sweep on scene enter, ordered by intensity descending (hardest-hit counties light first — the eye is drawn to the hot spots). Each county transitions `fill` over 260ms; stagger 4ms per county so the whole map "develops" like film in ~1.1s.

### 4.3 Hover tooltip

- On `mouseenter`/focus of a county: raise its `stroke` to `var(--gold)`, `stroke-width: 1.5`, and lift it visually (`filter: none`, just the stroke — no drop shadow).
- Tooltip follows cursor, `background: #0B0B0B`, `border: 1px solid var(--gold-2)`, `padding: 12px 14px`, `border-radius: 0`, JetBrains Mono:
  - Line 1 (`13px`, `--text`): `HARRIS COUNTY` (uppercase).
  - Line 2 (`11px`, `--text-dim`): `FIPS 48201 · pop 4.73M`.
  - Line 3 (`13px`, `--gold`): the headline number — for the hero scenario, per-county fiscal shift, e.g. `−$412 median homeowner tax · +$0.19B district gap`.
  - A 3px gold intensity bar matching the county's step.
- Keyboard: counties are focusable (`tabindex` on the top-10 only to keep tab order sane); Tab cycles the top-10, showing each tooltip in turn.

### 4.4 Top-10 strip

Right column. Heading JetBrains Mono `12px` `--text-dim`: `HARDEST HIT · TOP 10`. Ten rows, each:
- Rank `01`–`10`, JetBrains Mono `12px` `--text-dim`.
- County name, Inter `15px` weight 600 `--text`.
- A horizontal magnitude bar, height 8px, `background: #141310`, filled to `intensity * 100%` with the county's ramp color. Width proportional to the real number — never equal blocks.
- Trailing value, JetBrains Mono `12px` `--gold`, right-aligned.
Hovering a strip row highlights the matching county on the map (shared `id`), and vice versa.

Below the strip: a legend (the 6 ramp swatches, 22px squares, labeled `LOW → HIGH`) and one summary stat, Archivo `28px`: `183 of 254 counties see a net increase in local burden.`

### 4.5 Data

`counties` map from 3.7: `{ "TX_201": 0.64, ... }`. Any county absent = 0 (base fill). Pre-bake per scenario. Provide a small helper `intensityToStep(v)` and `intensityToFill(v)` per the table.

---

## 5. Scene 4 — The Verdict (litigation + next steps)

The change has consequences and a process cost. This scene is the sober close: how likely you get sued, and the human-gated machinery that must turn before this is real.

### 5.1 Layout

Three columns: left = litigation gauge; center = "what must happen next"; right = one-page brief preview.

Scene heading, Archivo `clamp(30px, 3.2vw, 48px)`: `The verdict.`

### 5.2 Litigation-exposure gauge

- Pure SVG semicircular gauge (180° arc), `viewBox="0 0 400 240"`. Background arc `stroke: #141310`, `stroke-width: 26`, `stroke-linecap: butt` (square ends — no rounded caps). Value arc drawn over it with `stroke: var(--gold)`, `stroke-width: 26`, using `stroke-dasharray` to fill `score/100` of the semicircle; animates from 0 to target over 1100ms `cubic-bezier(0.16,1,0.3,1)` on scene enter.
- Three band ticks at 33 and 66 (thin `--hairline` radial lines).
- Center readout: score `72` in Archivo `clamp(48px, 6vw, 88px)` weight 800 `--text`; below it band label JetBrains Mono `14px`: `LITIGATION EXPOSURE · HIGH` where HIGH is `--gold`. Bands: 0–33 `LOW`, 34–66 `MODERATE`, 67–100 `HIGH` (all rendered in gold text, band word changes; gauge does not go red — palette is gold-only).
- Below gauge: the "vectors" list — 2–4 concrete litigation risks, each a row: JetBrains Mono `11px` tag (`EQUAL PROTECTION`, `SINGLE-SUBJECT`, `UNFUNDED MANDATE`) + Inter `14px` one-liner + a citation chip. E.g. `Edgewood ISD v. Kirby lineage · school-finance equity challenge`.

### 5.3 "What must happen next" panel

Frames Gorgias as decision support with human approval gates — directly answers the judges' "human approval gate" religion.

- Heading JetBrains Mono `12px` `--text-dim`: `PATH TO ENACTMENT · HUMAN GATES`.
- A vertical stepper (SVG or CSS), each step a `border: 1px solid var(--hairline)` tile, `border-radius: 0`, 16px padding:
  1. `LEGISLATIVE` — `88th Legislature · floor vote · single-subject check` — status chip `PENDING`.
  2. `AGENCY RULEMAKING` — lists implementing agencies from cascade (`Comptroller`, `TEA`, `Appraisal Districts`) with a **rulemaking clock**: JetBrains Mono countdown `~180 days` shown as a thin horizontal progress rule (0% filled, gold), label `Texas Register · notice-and-comment`.
  3. `HUMAN APPROVAL GATE` — explicit tile, `border-color: var(--gold)`: `Gorgias recommends. A person decides. No rule enacts without sign-off.` This tile is emphasized (gold border, `background: #0E0D0A`).
  4. `FISCAL NOTE` — `LBB certification required · net −$3.10B/yr` linking back to the counter.
- Each step's citation/authority is a chip; clicking reuses the citation-drawer component from Scene 2 (shared component) so provenance is one interaction everywhere.

### 5.4 One-page brief preview

- Right column shows a scaled-down "printed" brief: a white-on-dark inverted card? No — keep dark. A `#0C0C0C` page, `border: 1px solid var(--hairline)`, aspect ratio 8.5×11 scaled to fit column height, showing:
  - Masthead `GORGIAS IMPACT BRIEF` (Archivo `14px`) + date + scenario title.
  - Three stat lines (net fiscal, counties affected, litigation band).
  - A miniature of the cascade tree (reuse SVG at 0.3 scale, static, traced edges) and a mini county map thumbnail.
  - Footer: `Grounded in the Vulcan statutory corpus · N citations · generated <timestamp>`.
- A button under it: `EXPORT ONE-PAGE BRIEF` (gold, same style as Run). For the hackathon, this calls `window.print()` with a `@media print` stylesheet that lays out the real one-pager (no browser header/footer — set `@page { margin: 0.5in; }` and instruct the user to export to PDF themselves; never auto-generate a PDF with default print chrome). If print is risky mid-demo, the button can instead reveal a full-screen brief overlay — safer. Default to the overlay for the live demo; wire print behind a flag.

### 5.5 Close

Bottom-center, once verdict settles: a restrained call-to-reset, JetBrains Mono `12px` `--text-dim`: `R · RUN ANOTHER POLICY`. No confetti, no celebration — the tone is an instrument reporting a finding.

---

## 6. Interaction model & demo resilience

### 6.1 Keyboard-driven flow

Everything advances without the mouse. Bindings (global unless noted):

| Key        | Action |
|------------|--------|
| `SPACE`    | Advance: Console→run→Cascade→Map→Verdict. On Console, runs the selected scenario. |
| `→` / `←`  | Next / previous scene (no re-run; replays cascade animation if entering Cascade). |
| `1`/`2`/`3`| On Console, select scenario card 1/2/3. |
| `Enter`    | On Console, run current selection (= Space). |
| `C`        | Toggle citation drawer for the focused node (Cascade/Verdict). |
| `Tab`      | Cycle focusable nodes/counties (visible focus ring, 2px gold, offset 3px). |
| `R`        | Reset to Console, clears state, re-selects hero card. |
| `ESC`      | Close drawer if open, else jump to Console. |
| `F`        | Toggle a "presenter" high-contrast mode (bumps type scale +10%, thickens hairlines to 1.5px) for a dim room. |

The presenter can run the entire 90-second demo with Space alone. Design the default focus so Space never does nothing — on each scene it does the single most likely thing.

### 6.2 Reduced network dependence

- All three scenario cards are fully pre-baked as static JSON (section 3.7) shipped in the bundle. The demo's happy path touches zero network.
- Fonts, county SVG path data, and statute source text are all bundled locally. No CDN, no runtime fetch on the critical path.
- The free-text field is the only live-model path. It calls the backend `/simulate`; on success it renders like a card; on any failure it silently falls back to the closest pre-baked scenario and shows a small JetBrains Mono `10px` `--text-dim` note `USING CACHED CORPUS RESULT` — never an error modal mid-demo.

### 6.3 Graceful degradation

- If `/simulate` times out (>3500ms), abort and fall back; the fiscal counter and cascade still play from cached data. A timeout must never leave a blank cascade.
- If web fonts fail: system fallbacks (section 0) hold layout; no FOIT beyond 100ms (`font-display: swap`).
- If the county SVG fails to parse (shouldn't — it's inline): Scene 3 shows the top-10 strip alone, full-width, and the map area shows a `MAP UNAVAILABLE · SEE RANKING` mono note. Demo continues.
- `prefers-reduced-motion`: all sweeps become instant/cross-fade (section 1.4); the story still reads.
- Never show a browser `alert()`, a stack trace, or a spinner that can hang. Every async has a hard fallback within 3.5s.

---

## 7. Tokens, scales, layers, animation reference

### 7.1 CSS custom properties (drop-in)

```css
:root {
  /* palette */
  --bg:            #0A0A0A;
  --bg-raised:     #0C0C0C;
  --bg-gold-tint:  #0E0D0A;
  --gold:          #9D8B5E;
  --gold-2:        #6C6042;   /* secondary gold */
  --gold-hi:       #C7B37A;   /* map hottest / hover lighten */
  --gold-btn-hover:#B4A06E;
  --text:          #EDE9E0;
  --text-dim:      #9A958A;
  --text-faint:    #63605A;
  --hairline:      #24221E;   /* 1px borders / connectors */

  /* map ramp */
  --ramp-0: #141310; --ramp-1: #3A3220; --ramp-2: #5A4E2E;
  --ramp-3: #7C6C3E; --ramp-4: #9D8B5E; --ramp-5: #C7B37A;

  /* type */
  --font-display: "Archivo", "Helvetica Neue", Arial, sans-serif;
  --font-body:    "Inter", -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono:    "JetBrains Mono", "SF Mono", "Menlo", ui-monospace, monospace;

  /* spacing scale (px) */
  --s1: 4px;  --s2: 8px;  --s3: 12px; --s4: 16px; --s5: 20px;
  --s6: 24px; --s7: 32px; --s8: 40px; --s9: 56px; --s10: 72px; --s11: 96px;

  /* radius — always 0 */
  --radius: 0;

  /* motion */
  --ease-out:   cubic-bezier(0.16, 1, 0.3, 1);
  --ease-inout: cubic-bezier(0.65, 0, 0.35, 1);
  --dur-fast:   180ms;
  --dur-base:   260ms;
  --dur-node:   380ms;
  --dur-arc:    1100ms;
  --cascade-speed: 1;  /* multiplier on the 9.2s timeline */
}
```

### 7.2 Type scale (px, at ≥1600px)

| Token          | Font    | Size | Weight | Use |
|----------------|---------|-----:|-------:|-----|
| display-xl     | Archivo | 104  | 800    | fiscal counter, gauge score (clamped) |
| display-l      | Archivo | 68   | 800    | Console headline (clamped) |
| display-m      | Archivo | 48   | 800    | scene headings (clamped) |
| title          | Archivo | 22   | 700    | card / node titles (large) |
| heading        | Inter   | 20   | 600    | subheads |
| body           | Inter   | 18   | 400    | descriptions |
| body-s         | Inter   | 15   | 400/600| node titles, strip rows |
| mono-l         | JBMono  | 18   | 600    | budget deltas |
| mono-m         | JBMono  | 13   | 400    | tags, tooltips |
| mono-s         | JBMono  | 11   | 400    | citation chips, provenance |
| mono-xs        | JBMono  | 10   | 400    | stratum kickers, footer legend |

Kicker/label letter-spacing: `0.14em`–`0.22em` uppercase for mono labels; body/display normal tracking except wordmark `0.14em`.

### 7.3 Z-layers

| z-index | layer |
|--------:|-------|
| 0       | scene background |
| 10      | cascade SVG / map SVG |
| 20      | node cards, county tooltips-anchor |
| 30      | fiscal counter, scene headings |
| 40      | header, footer (fixed chrome) |
| 60      | county tooltip (follows cursor) |
| 80      | citation drawer + its scrim (scrim `rgba(10,10,10,0.5)`) |
| 100     | full-screen brief overlay / presenter notes |

### 7.4 Animation catalogue

| Name              | Props                              | Duration | Easing        | Trigger |
|-------------------|------------------------------------|---------:|---------------|---------|
| node-rise         | opacity 0→1, translateY 12→0       | 380ms    | --ease-out    | stratum stagger |
| edge-charge       | stroke-dashoffset len→0            | 420ms    | linear        | after parent settles |
| conflict-flash    | border/opacity pulse               | 220ms    | ease-out      | conflict node appear |
| counter-step      | numeric increment                  | per-node | stepped       | budget node land |
| counter-settle    | numeric ease to total              | 1200ms   | ease-out      | after last budget |
| county-develop    | fill base→ramp                     | 260ms    | ease          | 4ms/county stagger |
| gauge-fill        | stroke-dasharray 0→v               | 1100ms   | --ease-out    | Verdict enter |
| drawer-in         | translateX 100%→0                  | 260ms    | --ease-out    | node/chip click |
| scene-swap        | opacity+translateY cross-fade      | 320ms    | --ease-inout  | scene change |
| corpus-pulse      | opacity 0.4↔1 (square)             | 2000ms   | ease-inout ∞  | header status |

Reduced-motion: node-rise/edge-charge/county-develop/gauge-fill/counter-* all collapse to a 400ms opacity cross-fade at final state; corpus-pulse stops.

---

## 8. The 90-second demo script (beat-by-beat → UI state)

Presenter drives with Space. Times are cumulative.

| t (s) | Spoken beat | UI state / action |
|------:|-------------|-------------------|
| 0–8   | "Every session, a lawmaker asks: if we change this one number, what actually happens? Nobody can answer. Gorgias is a flight simulator for lawmaking." | **Console** on screen. Hero card `Raise the homestead exemption` pre-selected, pulsing gold top-edge. Wordmark + tagline large. |
| 8–14  | "Texas is considering raising the homestead exemption from a hundred thousand to a hundred forty. Watch." | Presenter hits **Space**. Button → `TRACING…`. |
| 14–24 | "It touches Tax Code 11.13, which collides with the school-funding formula — flagged. That forces four agencies to act, and here's the bill." | **Cascade** plays. Wave sweeps down; statute nodes with citation chips; the gold **conflict** node flashes; agencies appear; budget nodes land as the **counter spins to −$3.10B/yr**. |
| 24–34 | "And it's not a guess. Every node opens its source." | Presenter presses **C** (or clicks the conflict node). **Citation drawer** slides in: verbatim Tax Code §11.13(b) with the `$100,000` clause highlighted, plus the colliding Education Code section. "Grounded before generated." |
| 34–36 | "Close that." | **ESC** closes drawer. |
| 36–46 | "Statewide is abstract. Here's where it actually lands — all 254 counties, shaded by burden." | **Space** → **Map**. Choropleth develops hottest-first in ~1s. |
| 46–56 | "Rural counties with thin appraisal bases get hit hardest — top ten right here. Hover any county for the real number." | Presenter hovers a top county (e.g. **Harris** or a hot rural one); tooltip shows median-homeowner and district-gap figures. Strip row highlights in sync. |
| 56–68 | "So what does it cost you politically? Litigation exposure: high — this echoes Edgewood v. Kirby, the school-finance equity line." | **Space** → **Verdict**. **Gauge fills to 72 · HIGH**. Vectors list shows `EQUAL PROTECTION`, `UNFUNDED MANDATE` with citations. |
| 68–80 | "And critically — Gorgias doesn't enact anything. It recommends. A person decides. Here's the path: legislature, agency rulemaking with a 180-day clock, and an explicit human approval gate." | Presenter gestures to **What-must-happen-next** stepper; the gold **HUMAN APPROVAL GATE** tile is emphasized; rulemaking clock visible. |
| 80–88 | "One page, grounded, exportable — the brief a staffer hands their member." | Presenter clicks **EXPORT ONE-PAGE BRIEF** → full-screen brief overlay: stats, mini-cascade, mini-map, citation count. |
| 88–90 | "That's Gorgias. A flight simulator for lawmaking — grounded in the corpus, gated on a human." | Overlay holds. Presenter can hit **R** to reset for judges' questions (jumps to Console, ready for a backup scenario via `2`/`3`). |

Backup scenarios (`2` = property-tax cap, `3` = ESA vouchers) are one keypress away if a judge asks "what about X" — each produces a fully distinct cascade, map, and verdict from pre-baked data.

---

## 9. Build order (2.5h reality check — informational)

Not required for the spec, but the intended critical path so the builder sequences right:
1. Shell + tokens + fonts + scene switching + keyboard bus (30m).
2. Console with three cards + Run (15m).
3. Cascade SVG + node component + stagger + counter + one hero dataset (45m).
4. Citation drawer (shared component) (15m).
5. County map (inline SVG + ramp + tooltip + strip) with hero data (25m).
6. Verdict gauge + stepper + brief overlay (20m).
7. Bake backup datasets 2 & 3; reduced-motion + fallbacks; presenter mode (20m).

Ship Scenes 1–2 and the drawer first — that is the demo's whole gravity. Map and verdict are the denouement; the cascade + citations are what win.


---

# 8. REUSABLE LOCAL ASSETS
(research: r-local-assets. NOTE: the TCC blocker described below is RESOLVED — the orchestrator copied concepts/06 to research/_ref-statecraft.html (625 lines); builders read the cascade seed from there. County-map question also resolved: no county SVG exists on disk or in concepts/06, so the map is fetched in pipeline step P0 per section 4 item 7 — plotly geojson-counties-fips.json filtered to STATE=="48", converted to SVG paths, embedded in data/.)

# Gorgias — Reusable Local Assets Inventory

Scope: hunt on-disk code to LIFT for Gorgias (dark #0A0A0A / gold #9D8B5E, pure CSS/SVG, FastAPI or static HTML+JS). Readiness scale 1-5 (5 = paste with near-zero edits).

## ACCESS BLOCKER — read this first

This process is TCC-blocked from `/Users/j/Desktop/**` **except** the `gorgias/` subtree (which was granted, so we CAN read/write our own repo and I DID write this file here). Every primary asset the task named lives elsewhere on Desktop and is **unreadable** from here:

- `concepts/06-statecraft-simulator.html` → `Operation not permitted` (EPERM) on read, cat, cp, and osascript. **Could not read a single line.** This is the design starting point — it is currently a black box to me.
- Tribunal / RUSTLING / witness-performance report HTML → same Desktop protection; cannot enumerate Desktop root to even locate them.
- `project-sunrise/` → not present at `/Users/j/Desktop/project-sunrise` (ENOENT); real copy is inside blocked Desktop tree per MEMORY.

**Unblock action (fast, do this):** from a process that HAS Desktop access (the agent/terminal that created `gorgias/` does — it wrote SKELETON.md and vulcan-surfaces.md here), copy the source files INTO our readable subtree, e.g.:

```
cp "/Users/j/Desktop/patriot-games-hackathon/concepts/06-statecraft-simulator.html" \
   "/Users/j/Desktop/patriot-games-hackathon/gorgias/research/_ref-statecraft.html"
```

Once any file sits under `gorgias/`, I can read it fully and catalog its cascade viz / county SVG / CSS vars / animations. Until then items 1-3 of the task are un-inventoried, not absent.

## No Texas county map on disk — anywhere

Searched Downloads, Documents, My Downloads, dev, _working (depth 6) for `*.geojson`, `*counties*`, `*texas*`, `*topojson*`, `us-states`. **Zero real map assets** (only lodash `countBy` / WP `word-count` noise). The county heat map must be sourced at build time (pipeline step): pull TX county TopoJSON from a CDN/Census once, convert to SVG `<path>` d-strings, embed in `data/`. Treat as a build dependency, not a liftable asset. If `concepts/06` already contains a county SVG (likely, per task description), unblocking it above is the difference between "have a map" and "scrape a map."

---

## LIFTABLE ASSETS (accessible)

### 1. Skippy backend — single-file FastAPI + static + SPA catch-all  ★ readiness 5
Path: `/Users/j/My Downloads/Always Allow-Skippy/backend/main.py` (415 lines, readable)
This is the cleanest FastAPI skeleton on disk and maps 1:1 onto SKELETON.md's Tier-2 `api.py`.
Lift verbatim, rename, drop the domain routes:
- App init with title/description/version + `lifespan` (lines 121-126).
- `CORSMiddleware` block, localhost:5173 origins (lines 128-140) — widen or keep for Vite dev.
- **Static + SPA serving (lines 400-415)** — the money block:
  ```python
  _frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
  if _frontend_dist.exists():
      app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="static-assets")
      @app.get("/{path:path}")
      async def serve_spa(path: str):
          index = _frontend_dist / "index.html"
          if index.exists():
              return FileResponse(str(index))
          raise HTTPException(status_code=404, detail="Frontend not built")
  ```
  For Gorgias (Tier 0 is a single self-contained `index.html`, not a Vite build), simplify to
  `app.mount("/", StaticFiles(directory="app", html=True))` OR keep this pattern and point
  `_frontend_dist` at `app/`. Add one `@app.get("/simulate")` handler for Tier 2.
- Route decorator patterns (`@app.get/@app.post` with Pydantic response models) are good copy references for the `/simulate?policy=` endpoint.
- Header docstring even documents the run command: `uvicorn main:app --reload --port 8000`.
Note: pure `python3 + fastapi`, no bun — aligns with SKELETON's "bun-free zone" for pipeline/api.

### 2. Veritas investor deck — exact dark/gold design system, inline SVG  ★ readiness 4
Path: `/Users/j/Documents/GitHub/Veritas/docs/veritas_deck.html` (723 lines, readable)
Same design DNA as Gorgias's non-negotiables. Lift the CSS scaffold wholesale, then strip radii.
- Palette in use: bg `#0a0a0a` / `#0D0B09`, gold `#C5A55A` (rgb 197,165,90 — a brighter cousin of our `#9D8B5E`; swap to spec), cream `#F5F0EB`, ink `#3e3e32`. Gold applied almost entirely as low-alpha `rgba(197,165,90,.04–.5)` for rules, chips, hovers — this is the tasteful restraint the brief wants.
- **Font stacks already correct:** `Inter` (body), `JetBrains Mono` (labels/mono), `Archivo` weight 900 (display/cover). Copy the `@font-face`/`font-family` declarations.
- **Gold grid background (lines 41-42)** — liftable "command-center" texture:
  ```css
  background-image:
    linear-gradient(rgba(197,165,90,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(197,165,90,0.04) 1px, transparent 1px);
  ```
  Add `background-size: 40px 40px;` for the graph-paper look behind the cascade canvas.
- Mono uppercase eyebrow labels, thin 1px gold `.rule` dividers (`rgba(197,165,90,.22)`), gold chip pills (`rgba(197,165,90,.1)` bg) — all reusable node/section chrome.
- Inline stroke SVG icons (`viewBox 0 0 24 24`, `stroke=currentColor`, `stroke-width 1.4`) — lucide-style, no icon lib, CSP-safe. Reuse for node-type glyphs (statute, budget, agency).
- **MUST FIX on lift:** deck uses `border-radius: 12px / 3px` in several places (`.s-icon`, chips). Gorgias mandates `border-radius: 0` everywhere — global-replace to 0. Also 3 theme classes (`.t-dark/.t-black/.t-cream`) — keep only dark.
- No real charts here (bars/gauges/timelines) — it's a slide deck, not a dashboard. Chart primitives still owed by the blocked statecraft/tribunal files.

### 3. Personal site static — inline SVG icon set + keyframe pulse  ★ readiness 3
Path: `/Users/j/Downloads/personal-site-static/index.html` (readable; siblings in `blog/`)
- Lucide-style inline stroke SVGs at small sizes (8/16/24px) for close/expand/chevron/menu — micro-lift for UI controls (`<path d="M18 6 6 18M6 6l12 12"/>` etc.).
- `@keyframes pulse` (line 569) — reusable for "live" node / active-cascade indicator dots.
- Static-site structure (no framework) is a decent reference for Tier-0 self-contained `index.html` discipline, but no cascade/map/chart code. Cosmetic-tier only.

### 4. Other FastAPI scaffolds seen (lower value)
- `/Users/j/dev/reflected/api/main.py` (59 lines) — minimal FastAPI + CORS + `/api/health` + volume-mount check. Good ONLY if you want a barer skeleton than Skippy; no static serving. Readiness 3.
- `/Users/j/Documents/GitHub/Veritas/backend/main.py` — exists, not deeply inspected; Skippy is cleaner. Skip unless needed.

---

## Recommendation for the 2.5h build

1. **Skeleton:** copy Skippy `main.py` → `gorgias/app/api.py`, strip domain routes, keep CORS + static mount, add one `/simulate`. (Tier 2 optional per SKELETON — Tier 0 `index.html` can serve with `python3 -m http.server`, no FastAPI needed at all for the offline demo.)
2. **CSS system:** lift Veritas deck's `:root`/font/grid/rule/chip CSS into `index.html`, fix gold to `#9D8B5E`/`#6C6042`, force `border-radius:0`, keep dark theme only.
3. **Icons/pulse:** pull inline SVGs + `@keyframes pulse` from Veritas + personal-site.
4. **Blocking dependency:** get `concepts/06-statecraft-simulator.html` copied into `gorgias/` so its cascade viz + county SVG can actually be lifted — this is the single highest-leverage unblock. Without it, cascade layout, county heat-map SVG, and animation code must be built from scratch.
5. **County map:** must be fetched in a pipeline step (no local geojson) UNLESS statecraft file already carries one.


---

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


---

# APPENDIX A — HERO SCENARIO NODE GRAPH (SCENARIO_HOMESTEAD)

The exact cascade content for the demo. Every node ships with cite + source excerpt.
Status column: VERIFY = pipeline (T1/T3 jobs) must pull and confirm the operative text
before demo; the cite is believed correct but GLM must string-match the excerpt against
the scraped source. Any node failing verification gets label "modeled" in the UI —
never silently shipped.

## A.1 Policy node
- id: policy-root
- title: "Raise the residence homestead exemption: $100,000 -> $140,000"
- framing: school district ad valorem taxation, Tax Code Title 1
- delta: +$40,000 exemption per homestead
- real-world anchor: HB 9 / SB 4 (89R) lineage — the 89th Legislature literally did
  a version of this; LBB fiscal note at capitol.texas.gov/tlodocs/89R/fiscalnotes/
  html/ is our dollar ground truth. VERIFY via P3.

## A.2 Statute stratum (type: statute)
| id | cite | operative claim | status |
|---|---|---|---|
| st-1113b | Tax Code §11.13(b) | mandatory school-district residence homestead exemption amount — the section the policy amends | VERIFY (P1) |
| st-1113n | Tax Code §11.13(n) | optional percentage exemption interplay — must not conflict with new floor | VERIFY (P1) |
| st-1126 | Tax Code §11.26 | tax ceiling for 65+/disabled — ceiling must be reduced to reflect increased exemption; consequential amendment required | VERIFY (P1) |
| st-2609 | Tax Code §26.09 | assessor calculation of tax — mechanical downstream change | VERIFY (P1) |
| st-4825x | Educ. Code §48.2556 | state compensation to districts for exemption-driven revenue loss (hold harmless) | VERIFY (P1) |
| st-48255 | Educ. Code §48.255 | Foundation School Program funding formulas absorbing the local revenue drop | VERIFY (P1) |
| st-const | Tex. Const. art. VIII §1-b(c) | constitutional amendment prerequisite — exemption amount is constitutionalized; statute alone is insufficient | VERIFY (P1) |

## A.3 Conflict stratum (type: conflict) — the gold-flag nodes
| id | conflict | severity | status |
|---|---|---|---|
| cf-const | Statutory change without art. VIII amendment = facially unconstitutional; requires joint resolution + statewide election (adds 6-18mo to any implementation timeline) | 3 | VERIFY (T2) |
| cf-ceiling | §11.26 ceiling formula, if left unamended, over-taxes 65+ homeowners relative to new exemption — the classic consequential-amendment miss | 2 | VERIFY (T2) |
| cf-tacrule | Comptroller property tax administration rules (34 TAC Ch. 9, Subch. H) reference prior exemption amounts in appraisal-district guidance — rulemaking update required | 1 | HARDCODE (TAC portal is JS-heavy; do not live-scrape; cite rule number from research) |

## A.4 Agency stratum (type: agency)
| id | agency | action required | status |
|---|---|---|---|
| ag-cpa | Comptroller — Property Tax Assistance Division | revise appraisal-district guidance, forms (50-114 application), and 34 TAC Ch.9 rules | VERIFY (T5) |
| ag-tea | Texas Education Agency | recompute FSP entitlements; distribute hold-harmless per §48.2556 | VERIFY (T5) |
| ag-sos | Secretary of State | constitutional-amendment election administration (ballot language, canvass) | VERIFY (T5) |
| ag-cads | 253 county appraisal districts | reprogram exemption in CAMA systems; re-notice affected homesteads | modeled (no single statute; operational reality — label as modeled) |

## A.5 Budget stratum (type: budget) — dollars from LBB fiscal note (P3)
| id | line | direction | status |
|---|---|---|---|
| bd-fsp | Foundation School Program — state hold-harmless cost | UP (state GR) | VERIFY (P3, exact $ from HB9-analog fiscal note) |
| bd-mno | School district M&O local revenue | DOWN (backfilled) | VERIFY (P3) |
| bd-recap | Recapture ("Robin Hood") payments | DOWN | VERIFY (P3) |
| bd-cnty | Per-county levy delta | distributed (map input) | COMPUTED (P2: levy x exemption-base share; methodology note in UI) |

## A.6 County stratum -> map
- Input: 2025-county-rates-levies.xlsx (P2) joined to FIPS via P0 geojson.
- impact_usd per county = school-district levy share attributable to homestead base
  x delta ratio. This is a MODEL — label the map "modeled from Comptroller 2025
  levies"; the per-county number is honest arithmetic on real data, not an official estimate.
- Top-10 strip: Harris, Dallas, Tarrant, Bexar, Travis, Collin, Denton, Fort Bend,
  Hidalgo, Williamson (expected by levy size — P2 confirms order from real data).

## A.7 Verdict inputs
- exposure_pct: driven by cf-const (constitutional prerequisite) — if enacted as
  statute-only: exposure ~90% (facial); with joint resolution: residual exposure from
  ceiling-formula litigation history. Present BOTH paths — that's the simulator flex.
- drivers: cf-const, cf-ceiling, school-finance litigation lineage (Edgewood v. Kirby
  line, cite as narrative not prediction).
- next_steps panel: joint resolution -> 2/3 both chambers -> statewide election ->
  comptroller rulemaking (34 TAC Ch.9) -> TEA FSP recompute. Each step tagged with its
  human approval gate — this panel is aimed straight at the judges' religion.

---

# APPENDIX B — SUB-AGENT BUILD PROMPTS (ready to paste at GO)

Rules: waves of 3-5, never more. Every prompt is self-contained (agents may be
TCC-blocked outside gorgias/ — all reads/writes stay inside gorgias/). All agents
told: no emojis, border-radius 0, no external requests in shipped artifacts, every
number real-or-labeled-modeled.

## B.1 Wave A (fire at GO, 4 agents)

### A1 — shell + tokens + map
Build gorgias/app/index.html shell per §7 (UI spec) exactly: app frame, header
wordmark, scene containers (Console/Cascade/Map/Verdict), CSS custom-property table
from §7.7 verbatim, keyboard scene-advance (Space), file:// clean. Lift CSS scaffold
from research (Veritas deck patterns are described in §8: gold grid background,
mono eyebrows, 1px gold rules, chip pills — implement equivalents; radius 0).
Map: read gorgias/data/tx-counties.svg.json (produced by A4/P0; until it exists, use
a 254-cell placeholder grid with the same data contract) and render the choropleth
with the 6-step gold ramp from §7.4. All scenes render with SCENARIO stub from
gorgias/app/data/scenario-stub.json (write it: 4 nodes/stratum, fake-but-proportional).
Definition of done: file:// open, all 4 scenes reachable by keyboard, zero console errors.

### A2 — cascade engine
Build the Scene-2 cascade as a standalone module (inline <script> section + SVG) in
a working file gorgias/app/_cascade-dev.html against the same stub contract; A-wave
integration merges it into index.html at the 0:45 gate. Follow §7.3 exactly: 5 strata,
node geometry, edge charge-ahead animation, stagger curve, ~9.2s total, fiscal counter
with tabular-nums landing on the scenario teaser total. Read research/_ref-statecraft.html
(625 lines) FIRST — it contains the concept page's cascade design language; upgrade,
don't reinvent. Citation drawer stub: node click emits node id; drawer filled by B1.
Definition of done: stub cascade plays end-to-end at 60fps-ish on a MacBook, replayable (R key).

### A3 — pipeline: statutes + fiscal note (Tier 1, python3 + httpx only, no bun)
Write gorgias/pipeline/p1_statutes.py + p3_fiscal.py per §4: fetch Tax Code Ch.11 HTML
(statutes.capitol.texas.gov/Docs/TX/htm/TX.11.htm), Educ. Code Ch.48, Tex. Const.
art. VIII page, and the HB9-analog 89R LBB fiscal note HTML. Extract raw section text
for every cite in Appendix A.2/A.5 into gorgias/pipeline/out/raw/*.json
({cite, url, fetched_at, raw_html, text}). NO LLM calls in this step — chunking only;
GLM jobs (T1/T3) run in Wave B via herd.py after Josh-confirmed key activation.
Definition of done: every A.2 cite has a raw text file with the section present
(string-check "$100,000" appears in 11.13 text, etc.), sources logged to out/manifest.json.

### A4 — pipeline: county data + map geometry (P0 + P2)
Write gorgias/pipeline/p0_map.py: fetch plotly geojson-counties-fips.json, filter
STATE=="48" (must yield exactly 254), project to SVG path d-strings (simple
equirectangular fit to 900x860 viewBox), write gorgias/data/tx-counties.svg.json
({fips, name, d}). Write p2_levies.py: fetch Comptroller 2025-county-rates-levies.xlsx
(§4 item 2), parse (openpyxl; pip-install into a venv inside gorgias/), extract
school-district levy per county, compute impact model per Appendix A.6, write
gorgias/data/county-impact.json. Definition of done: 254 paths, 254 county rows,
top-10 ordering printed for eyeball check, methodology string included in the JSON.

## B.2 Wave B (fire at ~0:45 gate, 4 agents)

### B1 — citation drawer + real-data merge
Merge pipeline/out + herd/out into gorgias/app/data/scenario-homestead.json per the
SCENARIO contract (§10). Wire the citation drawer (§7.3): node click -> verbatim
source excerpt with touched clause <mark>-highlighted, cite header, source URL line,
Vulcan corpus-type tag (Appendix C taxonomy). Every VERIFY node that passed gets its
real excerpt; failures get visible "modeled" badge. Definition of done: click every
node in the hero scenario — zero empty drawers.

### B2 — verdict scene + map polish
Build Scene 4 per §7.5: semicircle SVG exposure gauge (two-path presentation:
statute-only ~90% vs post-amendment residual), drivers list from A.7, HUMAN APPROVAL
GATE tile, next-steps rail with per-step approval tags. Map polish: hover tooltips,
top-10 strip synced to county-impact.json (order from data, not hardcoded).
Definition of done: verdict renders both paths; map numbers match JSON exactly.

### B3 — audit + README + sanitize
Cross-check EVERY number displayed in index.html against pipeline/out sources; write
the source table into gorgias/app/README.md (cite -> URL -> retrieved-at -> where used).
README voice: product, not hackathon apology; includes Gorgias naming note, GLM-fleet
build story, Vulcan corpus attribution ("taxonomy after vulcan.ai/coverage"). Run
sanitizer pass: no keys (grep sk-or, sk-ant, ghp_), no PII, no .env anywhere in
gorgias/. Definition of done: audit table complete, zero unsourced numbers, sanitizer clean.

### B4 (conditional — only if all gates green) — Tier 2 live query
Copy Skippy main.py -> gorgias/app/api.py per §8 recipe (strip domain routes, static
mount, one GET /simulate?policy=). /simulate calls OpenRouter GLM 5.2 with
WORKER_PROMPT T1+T2+T5 composite over embedded corpus extracts, returns SCENARIO-shaped
JSON, front-end renders it through the same cascade. Feature flag: ?live=1. Demo
NEVER depends on it. Definition of done: one successful live query end-to-end, or
flag stays off and we say nothing.

## B.3 Wave C (2:00, if and only if B complete) — polish pass
Single agent: projector QA at 1920x1080 (type sizes ≥ §7.1 distance-legibility table),
animation timing feel, copy pass (sentence case, no filler), final two-rehearsal
support. No new features. Freeze at 2:20.

---

# APPENDIX C — WORKER_PROMPT.md (the GLM 5.2 brief, embedded in every herd.py job)

Written to gorgias/pipeline/WORKER_PROMPT.md at GO. Version: wp-1.0.

## C.1 Role
You are an extraction worker in a 10-worker fleet building GORGIAS, a policy-impact
simulator, in under 3 hours. You do precise, boring work perfectly. You never invent,
summarize, or improve source text. Your output is machine-validated; deviation from
the schema = your job is discarded and retried.

## C.2 Iron rules
1. NEVER invent a number, cite, date, or quotation. If the input does not contain the
   answer, emit null for that field plus reason in _note.
2. Every "excerpt" field must be a VERBATIM substring of the provided source text
   (validator does string-containment; whitespace-normalized). No ellipses inside
   excerpts; use excerpt_2 for a second span.
3. Cites use canonical format: "Tax Code §11.13(b)", "Educ. Code §48.2556",
   "Tex. Const. art. VIII, §1-b(c)", "34 TAC §9.415". No variants.
4. Output ONLY the JSON object. No prose, no markdown fences, no explanation.
5. If input chunk is truncated mid-sentence at either end, work only with complete
   sentences; note truncation in _note.

## C.3 Task types and schemas

### T1 statute_extract
Input: {"task":"T1","cite_hint":"...","source_url":"...","text":"<raw chunk>"}
Output: {"cite":"...","heading":"...","operative_text":"<verbatim key provision>",
"cross_refs":["cite",...],"defined_terms":[{"term":"...","definition_excerpt":"..."}],
"_note":null}

### T2 conflict_scan
Input: {"task":"T2","proposed_change":"<one paragraph>","rule_cite":"...","rule_text":"<chunk>"}
Output: {"conflict":true|false,"severity":0-3,"rationale":"<=60 words, cites both texts",
"quote":"<verbatim from rule_text showing the conflict>","_note":null}
Severity: 0 none, 1 rulemaking-update needed, 2 consequential statutory amendment
needed, 3 constitutional/blocking.

### T3 ocr_cleanup
Input: {"task":"T3","doc_kind":"fiscal_note|levy_table","text":"<scraped/PDF text>"}
Output: {"rows":[{...doc-kind-specific...}],"low_confidence_cells":[{"row":i,"field":"...",
"reason":"..."}],"_note":null}
fiscal_note rows: {"fiscal_year":2026,"line":"...","amount_usd":-123456789,"fund":"General Revenue"}
levy_table rows: {"county":"...","school_levy_usd":...,"total_levy_usd":...,"rate_per_100":...}

### T4 county_extract
Input: {"task":"T4","text":"<comptroller table chunk>","counties_expected":["..."]}
Output: {"rows":[{"fips":"48###","county":"...","levy":...,"exemption_base":...}],
"missing":["county",...],"_note":null}

### T5 agency_map
Input: {"task":"T5","cites":["..."],"statute_texts":{"cite":"<text>"}}
Output: {"agencies":[{"agency":"...","action_required":"<=25 words","authority_cite":"...",
"deadline_cite":null|"...","approval_gate":"<who signs off>"}],"_note":null}

## C.4 Examples
One worked example per task type ships in the file (input chunk from Tax Code §11.13
+ correct output) — orchestrator writes these from P1 raw output at GO so examples
use REAL fetched text, not invented text.

## C.5 Fleet mechanics (herd.py contract)
- Model: GLM 5.2 via OpenRouter (slug verified at GO with 1-token ping; fallback to
  newest GLM slug if 5.2 naming differs).
- 10 concurrent workers; per-job: temperature 0.1, max_tokens 8000, 2 retries
  (backoff 2s/8s), 60s timeout.
- Every response -> pydantic schema check -> verbatim-containment check -> pass/requeue.
- Cost ledger printed per batch; HARD STOP at $200 cumulative (of $250 credit).
- Job manifest: gorgias/pipeline/out/herd-manifest.jsonl (job id, task, tokens, cost,
  validation result) — this doubles as the audit trail we show judges if asked how
  it was built (it is exactly their religion, applied to ourselves).

---

# APPENDIX D — PITCH COPY (the 30 seconds before the demo)

"Everyone tonight built you a mirror for elections. We built a windshield for
legislation. This is Gorgias — Justinian reads the law as it is, Trajan serves the
citizen as it is, Gorgias asks what happens if you change it. The Greek in the room
keeps the Romans honest. Watch: one policy change, every statute it touches, every
conflict it creates, every agency it wakes up, every dollar it moves, every county
that feels it — every node grounded in the primary source, every consequential step
behind a human approval gate. Built in three hours, on public Texas records, with the
same model you run in production. Pointed at your corpus, it does this for all fifty
states."

(Then: Space bar. Say nothing during the 9.2-second cascade. Let it land.)


---

# APPENDIX E — herd.py (paste-ready fleet harness)

Written to gorgias/pipeline/herd.py at GO. Requires: python3.11+, httpx, pydantic
(venv inside gorgias/). Key read from env ONLY (source the scratchpad env file at
runtime; never copy it into gorgias/).

```python
"""GLM 5.2 extraction fleet for Gorgias. 10 workers, schema-validated, budget-capped."""
import asyncio, json, os, sys, time
from pathlib import Path
import httpx

MODEL = os.environ.get("HERD_MODEL", "z-ai/glm-5.2")  # verified at GO by ping()
KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"
OUT = Path(__file__).parent / "out"
MANIFEST = OUT / "herd-manifest.jsonl"
WORKER_PROMPT = (Path(__file__).parent / "WORKER_PROMPT.md").read_text()
CONCURRENCY = 10
HARD_STOP_USD = 200.0
# GLM 5.2 OpenRouter pricing filled in at GO from the models endpoint:
PRICE_IN, PRICE_OUT = 0.0, 0.0  # $/1M tokens — set from ping() response headers/models API

_spent = 0.0
_lock = asyncio.Lock()

async def ping(client):
    r = await client.post(URL, headers=_hdrs(), json={
        "model": MODEL, "max_tokens": 1,
        "messages": [{"role": "user", "content": "ok"}]})
    r.raise_for_status()
    return r.json()["model"]  # confirms slug resolution

def _hdrs():
    return {"Authorization": f"Bearer {KEY}",
            "HTTP-Referer": "https://github.com/example-user",
            "X-Title": "gorgias-herd"}

async def run_job(client, sem, job):
    global _spent
    async with sem:
        for attempt, backoff in [(1, 2), (2, 8), (3, None)]:
            async with _lock:
                if _spent >= HARD_STOP_USD:
                    return {"id": job["id"], "status": "budget_stop"}
            try:
                r = await client.post(URL, headers=_hdrs(), timeout=60, json={
                    "model": MODEL, "temperature": 0.1, "max_tokens": 8000,
                    "messages": [
                        {"role": "system", "content": WORKER_PROMPT},
                        {"role": "user", "content": json.dumps(job["input"])}]})
                r.raise_for_status()
                data = r.json()
                usage = data.get("usage", {})
                cost = (usage.get("prompt_tokens", 0) * PRICE_IN
                        + usage.get("completion_tokens", 0) * PRICE_OUT) / 1e6
                async with _lock:
                    _spent += cost
                text = data["choices"][0]["message"]["content"]
                parsed = json.loads(text)          # rule C.2.4: bare JSON only
                ok, why = validate(job["input"]["task"], parsed, job["input"])
                rec = {"id": job["id"], "task": job["input"]["task"], "attempt": attempt,
                       "cost": round(cost, 5), "spent": round(_spent, 3),
                       "status": "ok" if ok else "invalid", "why": why}
                with MANIFEST.open("a") as m:
                    m.write(json.dumps(rec) + "\n")
                if ok:
                    (OUT / f"{job['id']}.json").write_text(json.dumps(parsed, indent=1))
                    return rec
            except Exception as e:
                why = f"{type(e).__name__}: {e}"
            if backoff is None:
                return {"id": job["id"], "status": "failed", "why": why}
            await asyncio.sleep(backoff)

def validate(task, parsed, inp):
    # pydantic models per task type (T1-T5) defined in schemas.py; plus the
    # verbatim-containment check: every *excerpt*/quote field must be a
    # whitespace-normalized substring of inp["text"] / inp["rule_text"].
    from schemas import check
    return check(task, parsed, inp)

async def main(jobs_path):
    jobs = [json.loads(l) for l in Path(jobs_path).read_text().splitlines()]
    OUT.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        print("model:", await ping(client))
        results = await asyncio.gather(*[run_job(client, sem, j) for j in jobs])
    bad = [r for r in results if r and r["status"] != "ok"]
    print(f"done: {len(results)-len(bad)}/{len(results)} ok, ${_spent:.2f} spent")
    if bad:
        print("failed/invalid:", json.dumps(bad, indent=1))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
```

Notes:
- PRICE_IN/OUT set at GO from OpenRouter models API so the ledger is real.
- schemas.py (B-wave writes it): pydantic models T1-T5 + `check()` incl. the
  containment rule. ~80 lines.
- Jobs files are jsonl produced by p1/p2/p3 chunkers: one {"id","input"} per line.
- Requeue-once semantics live in the retry loop; invalid-after-3 -> visible failure,
  node becomes "modeled".

---

# APPENDIX F — scenario-stub.json (the data contract, wave A builds against this)

```json
{
  "policy": {"title": "Raise the residence homestead exemption to $140,000",
             "delta_label": "+$40,000 per homestead",
             "teaser_total_usd": -3100000000},
  "nodes": [
    {"id": "policy-root", "type": "policy", "parent": null,
     "label": "Homestead exemption $100k -> $140k", "cite": null},
    {"id": "st-1113b", "type": "statute", "parent": "policy-root",
     "label": "School district homestead exemption", "cite": "Tax Code \u00a711.13(b)",
     "corpus_tag": "State Statutes", "excerpt": "STUB \u2014 replaced by pipeline",
     "source_url": "https://statutes.capitol.texas.gov/Docs/TX/htm/TX.11.htm"},
    {"id": "cf-const", "type": "conflict", "parent": "st-1113b", "severity": 3,
     "label": "Constitutional amendment required", "cite": "Tex. Const. art. VIII, \u00a71-b(c)"},
    {"id": "ag-tea", "type": "agency", "parent": "st-4825x",
     "label": "TEA recomputes FSP entitlements", "approval_gate": "Commissioner of Education"},
    {"id": "bd-fsp", "type": "budget", "parent": "ag-tea",
     "label": "Foundation School Program hold-harmless", "delta_usd": 3100000000}
  ],
  "counties": [{"fips": "48201", "name": "Harris", "impact_usd": 412000000, "impact_pct": 13.3}],
  "verdict": {
    "exposure_statute_only_pct": 90, "exposure_with_amendment_pct": 22,
    "drivers": ["cf-const", "cf-ceiling", "school-finance litigation lineage"],
    "next_steps": [
      {"step": "Joint resolution (2/3 both chambers)", "gate": "Legislature"},
      {"step": "Statewide election", "gate": "Texas voters"},
      {"step": "Comptroller rulemaking, 34 TAC Ch. 9", "gate": "Comptroller"},
      {"step": "TEA FSP recompute", "gate": "Commissioner of Education"}]
  },
  "meta": {"generated": "STUB", "sources": [], "model_note": "stub \u2014 all values fake but proportional"}
}
```

Contract rules: node ids stable across stub->real swap (B1 replaces content, never
ids); every non-policy node eventually carries either a verbatim excerpt + source_url
or "modeled": true; counties array always all 254 in real data (stub may carry 10).

---

# APPENDIX G — backup scenarios (staged data, same UI, only if time allows)

## G.1 "Untangle the braid" — repeal hair-braiding-adjacent license overhead
- Anchor: Texas deregulated hair braiding in 2015 (HB 2717, 84R) — a celebrated
  red-tape win the judges will know. Simulate a NEW analog: repeal an occupational
  license with similar structure (pick from TDLR list at build time).
- Cascade: Occupations Code chapter -> TDLR rules (16 TAC) -> agency (TDLR) ->
  budget (fee revenue loss vs enforcement savings) -> county map by licensee counts.
- Why it's here: pure red-tape-reduction — Jones's Cicero thread; and it shows the
  simulator handles REPEAL as well as expansion. Staged data acceptable; label it.

## G.2 "The broadband match" — raise BDO grant local match requirement
- Anchor: Gov't Code Ch. 490I (Broadband Development Office).
- Cascade: statute -> BDO rules -> comptroller -> federal BEAD interplay (conflict
  node: federal match rules, severity 2) -> rural county map (inverse of homestead:
  impact concentrates in low-population counties — visually distinct map, good for
  showing the ramp isn't hardcoded to metros).
- Only staged if G.1 is done and >20 min remain. Otherwise cut per guillotine.

---

# FINAL NOTE TO EVERY AGENT AND FUTURE SESSION

The demo is 90 seconds. Every decision trades toward: (1) the cascade landing
flawlessly offline, (2) every visible number surviving the question "is that real?",
(3) the words "citation-linked" and "human approval gate" being demonstrably true in
the UI, not just said. If a feature cannot meet all three, it does not ship tonight.
