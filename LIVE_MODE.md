# GORGIAS — Live Query Mode (Tier 2)

Type any Texas policy change into the console and GORGIAS builds the cascade live from
the scraped statute corpus: it routes to the relevant sections, extracts them, scans
each for conflict against your typed policy, validates every excerpt as verbatim, and
renders the result through the exact same cascade → map → verdict path as the staged
scenarios.

The staged demo is **completely unaffected**: live mode only activates on `?live=1`
*and* a reachable backend. On `file://`, on Vercel, or with the server down, the app
behaves exactly as before.

---

## Start it (one command)

```bash
cd gorgias
set -a && source /private/tmp/claude-501/-Users-j/2fb47d4a-d2c1-43d0-89fd-50578e0c2e66/scratchpad/openrouter.env && set +a
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8090
```

Then open **http://127.0.0.1:8090/?live=1**

The `OPENROUTER_API_KEY` env var must be set (the source line above does it). The key is
never copied into `gorgias/` — it lives only in the scratchpad env file and the process
environment.

Health check: `curl http://127.0.0.1:8090/health` →
`{"ok":true,"sections":545,"cached_t1":...,"model":"z-ai/glm-5.2","key":true}`

Optional env: `GORGIAS_BUDGET=<seconds>` (server-side wall-clock ceiling, default 40),
`GORGIAS_MODEL=<openrouter-model>` (default `z-ai/glm-5.2`).

---

## Demo flow

1. Open `http://127.0.0.1:8090/?live=1`. A gold `● LIVE — 545 sections indexed` badge
   appears next to the input once the backend health probe succeeds.
2. Type a policy in the `TX>` field, e.g.
   - `repeal the franchise tax`
   - `double the rural broadband grant match`
   - `cap local property-tax growth at two percent`
3. Press **Enter** (or click **RUN SIMULATION**). A mono/gold status line animates:
   `TRACING THE CORPUS… routing · extracting · validating verbatim · 12.4s`.
4. When the server returns, the built scenario is fed straight into the cascade engine
   and the view advances to the cascade. Map and verdict scenes work off the same data.
5. Leaving the input empty and clicking RUN (or picking a card) runs the **staged**
   scenario as always — live mode never intercepts an empty query.

---

## What is real vs modeled (honest labeling)

Every node the UI draws is labeled at the source:

- **Statute nodes** (`st-*`) — real. Cite, heading, and excerpt come from the scraped
  Texas corpus (`pipeline/out/crawl-nodes.json`, 545 sections). The excerpt is a
  **verbatim** substring of the section text, validated server-side with the same
  whitespace-normalized containment check as `pipeline/herd.py`. Carries `verbatim: true`
  plus the real `source_url` to statutes.capitol.texas.gov.
- **Conflict nodes** (`cf-*`) — real. Emitted only when the T2 conflict scan returns
  `conflict: true` with a verbatim quote from the rule text (validated). Severity 0–3
  comes from the scan. No conflict is fabricated — a spending-only change legitimately
  yields zero conflicts.
- **Agency nodes** (`ag-*`) and **budget nodes** (`bd-*`) — **modeled**. Carry
  `modeled: true`. These are the GLM assembler's analytical framing (which agencies act,
  approximate fiscal magnitude). Defensible, but not scraped.
- **Counties** — modeled geographic distribution reused from the hero scenario, scaled
  to the live teaser total. `meta.counties_modeled: true`.

`meta` records it all: `routed_slugs`, `verbatim_nodes`, `modeled_nodes`,
`verbatim_drops` (any excerpt that failed verbatim and was demoted to modeled), and
per-stage `timing_s`.

---

## Pipeline (server-side, `app/api.py`)

1. **Route** — one GLM 5.2 call (temp 0.1). A cheap lexical prefilter narrows the
   545-section index to ~40–140 candidates, and GLM picks the 4–6 most relevant slugs.
2. **Extract + scan** — one parallel wave: T1 statute extraction (served from the
   `t1c-*.json` cache where available, else live) **and** T2 conflict scan (always live,
   since it depends on the typed policy) for every picked section. Reuses the
   `WORKER_PROMPT.md` schemas.
3. **Assemble** — one GLM 5.2 call frames the modeled header, agencies, budget lines,
   and verdict around the real statute/conflict spine.
4. **Validate + build** — Python assembles the `SCENARIO_REAL`-shaped JSON, runs the
   verbatim check on every excerpt-bearing node, demotes failures to `modeled`, wires
   parents, and scales the county distribution.

---

## Failure behavior (graceful, no dead ends)

- **Backend unreachable / no `?live=1` / `file://`** — live mode stays inert. Staged
  scenarios and free-text-to-staged behavior are unchanged. No badge, no interception.
- **Front-end timeout (45s)** — the fetch aborts and the status line shows
  `TRACE TIMED OUT — corpus too deep for a live run. Try one of the staged scenarios
  above.` The staged hero dataset stays loaded; the user can run any card immediately.
- **Server error / budget exceeded (504 after `GORGIAS_BUDGET`s) / bad policy (422)** —
  the status line shows `LIVE TRACE UNAVAILABLE — <reason>. Staged scenarios still work.`
  and the app stays on the console with the staged data intact.
- **Router finds nothing relevant** — 422 with a clear message; same graceful fallback.

The server's own wall-clock ceiling (`GORGIAS_BUDGET`, default 40s) sits just under the
front-end's 45s abort, so a slow run returns a clean 504 rather than hanging.

---

## Files

- `app/api.py` — FastAPI server: `/`, `/health`, `/simulate`.
- `app/index.html` — one scoped `<script id="live-js">` block (after the GORGIAS IIFE)
  adds the `?live=1` gating, tracing UI, and the fetch → `GORGIAS.scenario` +
  `showScene(1)` handoff. Nothing else in the file changed.
