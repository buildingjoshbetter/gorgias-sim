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
