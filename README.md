<p align="center">
  <img src="assets/logo.svg" alt="Gorgias — a flight simulator for lawmaking" width="560"/>
</p>

<p align="center">
  <a href="https://gorgias-one.vercel.app"><b>gorgias-one.vercel.app</b></a> ·
  <a href="https://gorgias-one.vercel.app/sim">open the simulator</a> ·
  <a href="https://gorgias-one.vercel.app/deck">how it works</a>
</p>

---

Type a proposed law. Gorgias shows every statute it touches, every conflict it creates, every agency it wakes, every dollar it moves, and every county that feels it. Every node cites the primary source, verbatim. Before a single vote.

Built in one night at Patriot Games 250 (Austin, hosted by Vulcan Technologies).

## The demo scenario

Raise the Texas residence homestead exemption from $140,000 to $200,000.

Gorgias finds the break: the exemption amount is fixed in the constitution (Tex. Const. art. VIII §1-b(c)), so a bare statute is facially unconstitutional. It needs a joint resolution, a statewide election, comptroller rulemaking, and a TEA school-finance recompute. The simulator shows both futures: roughly 90% litigation exposure as statute-only, roughly 22% with the amendment. The precedent is fresh — Texas walked this exact path for Proposition 13 in November 2025.

## What is under the hood

| Layer | What it is |
|---|---|
| Corpus | 8,111 sections crawled from statutes.capitol.texas.gov across 370 chapters: Tax Code, Education Code, Government Code, Local Government Code, Election Code, Water Code, 34 TAC |
| Conflict graph | 5,175-node citation graph, 4,216 cross-reference edges, 54 conflicts flagged with severity 1-3 — each carrying a verbatim statutory quote |
| Extraction fleet | 5,000+ GLM 5.2 jobs via OpenRouter, schema-validated, with verbatim-containment checks so the model cannot invent a citation. Full audit manifest in `pipeline/out/` |
| County model | Per-county impact for all 254 Texas counties, computed from the Comptroller's 2025 rates and levies workbooks |
| Fiscal ground truth | LBB fiscal notes for HB 9 / SB 4 / SB 23 (89R) — the 2025 exemption increase used as calibration |
| Litigation lineage | Edgewood I-IV and West Orange-Cove v. Neeley, reporter cites verified against multiple sources |

Every number on screen is either traced to a fetched primary source or visibly labeled "modeled." The audit table is in [`AUDIT.md`](AUDIT.md).

## Run it

The site is static — open [gorgias-one.vercel.app](https://gorgias-one.vercel.app) or serve `app/` locally:

```
cd app && python3 -m http.server 8080
```

Keyboard: `Enter` runs the simulation, `Space` advances scenes, `G` jumps to the conflict graph, `C` opens citations, `R` replays the cascade.

Live free-text mode (type any Texas policy, get a grounded cascade in ~30s) needs the API:

```
export OPENROUTER_API_KEY=...
cd app && ../.venv/bin/uvicorn api:app --port 8090
# then open http://127.0.0.1:8090/sim.html?live=1
```

## Repo map

```
app/          the site: landing (index/home), simulator (sim.html), deck, live API
pipeline/     scrapers, GLM fleet harness (herd.py), worker prompts, audit manifest
data/         conflict graph, county impact model, litigation enrichment, TX county geometry
AUDIT.md      number-by-number source audit
```

## Credits

Corpus taxonomy after [vulcan.ai/coverage](https://vulcan.ai/coverage). Statutes from the Texas Legislature. Levies from the Texas Comptroller. Fiscal notes from the LBB. Built by Josh Adler with a fleet of Claude agents orchestrating GLM 5.2 workers.
