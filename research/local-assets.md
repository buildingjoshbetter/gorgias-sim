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
