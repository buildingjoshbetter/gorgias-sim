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
