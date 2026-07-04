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
