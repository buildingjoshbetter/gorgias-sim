# Gorgias

A flight simulator for lawmaking.

Type a proposed Texas policy change and watch it cascade: through the statutes it
amends, the rule conflicts it creates, the agencies it wakes up, the budget lines it
moves, the 254 counties that feel it, and the litigation exposure it carries. Every
node is grounded in a citation from the primary source, and every source is one click
away.

Justinian reads the law as it is. Trajan serves the citizen as it is. Gorgias asks
what happens if you change it — the third Roman in the room. Gorgias is the Greek in
the room, and the Greek keeps the Romans honest.

## Why it exists

Everyone models elections. Nobody models the second-order consequences of a bill
before it is written. A legislator who wants to raise the homestead exemption has no
tool that shows, in one view, that the change is facially unconstitutional without a
statewide vote, over-taxes seniors unless a second section is amended in lockstep,
costs the state roughly half a billion dollars a year in school hold-harmless
payments, and lands hardest on Harris and Dallas counties. Gorgias is that view.

The design target is Vulcan's own stated religion, applied to policy: grounded before
generated, a path from question to source to answer that is real and reviewable, and a
human approval gate on every consequential step. The verdict scene does not end with a
recommendation. It ends with the sequence of human sign-offs any real enactment would
require — joint resolution, two-thirds of both chambers, statewide election,
Comptroller rulemaking, TEA recompute — each tagged with who signs.

## The hero scenario

Raise the residence homestead exemption for school district taxation from its current
**$140,000** to **$200,000**.

The $140,000 floor is real and current: it is what Texas Tax Code §11.13(b) and Texas
Constitution art. VIII §1-b(c) read today, after HB 9 (89R) and the Proposition 13
constitutional amendment ratified in November 2025. The proposed jump to $200,000 is
the counterfactual the simulator runs. Because $200,000 exceeds the $140,000 amount
written into the constitution, the headline finding is not a budget number — it is
that the statute cannot do this alone. It needs a constitutional amendment first.

## Data sources

Every statutory excerpt shown in the app is a verbatim substring of a document we
actually fetched. Every fiscal figure traces to a Legislative Budget Board fiscal note
or is explicitly labeled modeled. Nothing is paraphrased into the source panel.

| # | What it powers | Source | URL | Retrieved (UTC) |
|---|----------------|--------|-----|-----------------|
| 1 | §11.13(b) homestead exemption, §11.26 senior ceiling, §26.09 tax calc | Texas Tax Code Ch. 11 & 26 (full-chapter HTML) | statutes.capitol.texas.gov/Docs/TX/htm/TX.11.htm, TX.26.htm | 2026-07-04T01:56:22Z |
| 2 | Educ. Code §48.255 (state compression), §48.2556 (hold-harmless posting) | Texas Education Code Ch. 48 (full-chapter HTML) | statutes.capitol.texas.gov/Docs/ED/htm/ED.48.htm | 2026-07-04T01:56:22Z |
| 3 | Constitutional ceiling — art. VIII §1-b(c), the $140,000 amount | Texas Constitution art. VIII (full-article HTML) | statutes.capitol.texas.gov/Docs/CN/htm/CN.8.htm | 2026-07-04T01:56:22Z |
| 4 | Budget cascade — school M&O levy loss, Foundation School Fund cost, recapture | LBB fiscal note, SB 4 (89R), introduced | capitol.texas.gov/tlodocs/89R/fiscalnotes/html/SB00004I.htm | 2026-07-04T01:56:23Z |
| 5 | Budget cascade — General Revenue impact calibration | LBB fiscal note, SB 23 (89R), introduced | capitol.texas.gov/tlodocs/89R/fiscalnotes/html/SB00023I.htm | 2026-07-04T01:56:23Z |
| 6 | Budget cascade — ad valorem exemption analog | LBB fiscal note, HB 9 (89R), introduced | capitol.texas.gov/tlodocs/89R/fiscalnotes/html/HB00009I.htm | 2026-07-04T01:56:22Z |
| 7 | Enactment status / effective-date lineage | TLO bill history — HB 9, SB 4, SB 23 (89R) | capitol.texas.gov/BillLookup/History.aspx?LegSess=89R&Bill=HB9 (SB4, SB23) | 2026-07-04T01:56:22Z |
| 8 | 254-county burden map | Comptroller 2025 school district rates & levies (XLSX) | comptroller.texas.gov/taxes/property-tax/docs/2025-school-district-rates-levies.xlsx | 2026-07-04T01:57:42Z |
| 9 | County map denominator — all-units levy | Comptroller 2025 county / city / special-district rates & levies (XLSX) | comptroller.texas.gov/taxes/property-tax/docs/2025-county-rates-levies.xlsx (city, special-district) | 2026-07-04T01:57:42Z |

Bill numbers use the 89th Legislature, Regular Session (89R, 2025). Fiscal notes are
authored by the Legislative Budget Board and hosted on Texas Legislature Online.

## What is actual and what is modeled

We separate the two everywhere, in the UI and here.

**Actual — retrieved verbatim from the primary source:**

- Every statute and constitution excerpt in the citation drawer. Each was
  string-matched against the scraped chapter text before it was allowed into the data
  file; anything that failed the match is labeled "modeled" in the interface rather
  than shown as a quote.
- The 2025 LBB fiscal-note figures. SB 4 (89R) shows a General Revenue impact of
  -$465,483,918 in FY2026; SB 23 (89R) shows -$576,859,000. These are the real
  legislative cost estimates for the $100,000-to-$140,000 exemption increase the 89th
  Legislature actually enacted. We use them as calibration ground truth.
- The Comptroller 2025 per-county school M&O levies that drive the county map's
  relative magnitudes.

**Modeled — honest arithmetic on real data, labeled as such:**

- The $200,000 projection. The demo's headline change ($140k to $200k) is a
  counterfactual, so its dollar impacts are scaled from the calibrated 2025 actuals,
  not quoted from a fiscal note that does not exist yet.
- The per-county `impact_usd`. Computed as county school M&O levy x homestead-base
  share (0.45) x delta ratio ($60,000 / $300,000 average taxable homestead value =
  0.2). The map is labeled "modeled from Comptroller 2025 levies." The magnitude is
  driven entirely by each county's real levy; the two share/average constants are
  stated modeling assumptions. The methodology string ships inside the data file.
- The litigation exposure percentage. Presented as two explicit paths (statute-only
  versus with-amendment), framed against the Edgewood v. Kirby school-finance line as
  narrative, never as a prediction.

The 34 TAC Ch. 9 Comptroller rulemaking node is hardcoded from research rather than
live-scraped: the Texas Administrative Code moved to a JavaScript-heavy Appian portal
that is not cleanly scrapeable in the build window. It is the one node not drawn from a
fetched document, and it is flagged accordingly.

## How it was built

The data pipeline is a small extraction fleet, run once before the demo, never during
it. Claude Fable orchestrated a fleet of GLM 5.2 extraction workers — GLM 5.2 is the
hosts' own production model — over the scraped Texas sources. The division of labor is
deliberate: Fable plans, writes the schemas, and audits; the GLM herd does the precise,
boring, high-volume extraction work.

Every worker output passes two gates before it is allowed into the app:

1. **Schema validation** — a Pydantic check that the JSON has exactly the shape the
   front-end expects.
2. **Verbatim containment** — every `excerpt` and `operative_text` field must be a
   whitespace-normalized substring of the source text the worker was given. If a
   worker paraphrases, invents, or "improves" the statute by a single word, the
   containment check fails and the job is requeued.

`§26.09` is a small monument to this discipline: GLM failed the verbatim check on it
three times in a row, so the operative text was hand-extracted from the source and
re-verified rather than shipped loose.

The whole run is logged to `pipeline/out/herd-manifest.jsonl` — one line per job, with
task id, attempt number, cost, and validation verdict (`ok` / `invalid` with the
reason). That file is the audit trail. It is the same standard Vulcan holds itself to,
turned on ourselves: an inspector general could reconstruct exactly how every number
in this app came to be, including the jobs that failed and why.

## Architecture

Static-first, server-optional.

- **Tier 0 (ships):** a single self-contained page with the hero scenario data
  embedded. Full cascade, map, and verdict work offline — this is what demos even if
  the wifi dies.
- **Tier 1 (ships, in-repo):** the Python pipeline under `pipeline/` (plain
  `python3` + `httpx`, no bundler) that scraped the real sources and emitted the
  embedded data. Run once before the demo to prove the data is real; shown in the repo,
  not executed on stage.
- **Tier 2 (optional):** a thin FastAPI wrapper exposing one live free-text query,
  feature-flagged off by default. The demo never depends on it.

## Source taxonomy

Gorgias groups its authority-chain nodes by corpus type — statute, constitution,
fiscal note, agency rule, county levy table — a taxonomy built after Vulcan's public
`vulcan.ai/coverage` source families. Pointed at a 157-billion-record corpus spanning
all 50 states instead of the handful of Texas sources we scraped in an afternoon, the
same cascade generalizes. We built against public Texas primary sources; the shape is
the same everywhere.

## Repository layout

```
app/
  data/
    scenario-homestead.json   embedded hero-scenario data (nodes, counties, verdict)
    county-impact.json        254-county modeled burden + methodology string
  README.md                   this file
pipeline/
  p0_map.py … p3_fiscal.py    scrapers, numbered in run order
  herd.py                     GLM 5.2 extraction fleet (schema + verbatim gates)
  WORKER_PROMPT.md            the extraction brief embedded in every job
  out/
    raw/                      verbatim scraped sources (statutes, fiscal notes, XLSX)
    *.json                    validated per-node extractions
    manifest.json             every fetch: URL, status, bytes, retrieved-at
    herd-manifest.jsonl       per-job audit trail (task, cost, validation verdict)
```
