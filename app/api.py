"""GORGIAS Tier-2 live query server.

Serves the static app at / and exposes GET /simulate?policy=<text>, which builds a
cascade live from the scraped Texas statute corpus:

  (a) one GLM routing call picks the most relevant sections from a 545-section index,
  (b) parallel GLM calls extract each section (T1, cached where possible) and scan it
      for conflict against the typed policy (T2, always live),
  (c) one GLM assembler call frames the header / agencies / budgets / verdict.

Statute and conflict nodes carry verbatim excerpts + cites + source URLs and are
validated server-side (whitespace-normalized containment, same as herd.py); anything
that fails verbatim is demoted to modeled. Agencies and budgets are modeled by design.

Run:  set -a && source <openrouter.env> && set +a
      .venv/bin/uvicorn app.api:app --host 0.0.0.0 --port 8090
"""
import asyncio
import json
import os
import re
import time
import urllib.request
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).resolve().parent          # gorgias/app
ROOT = HERE.parent                              # gorgias
PIPE_OUT = ROOT / "pipeline" / "out"
APP_DATA = HERE / "data"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("GORGIAS_MODEL", "z-ai/glm-5.2")
KEY = os.environ.get("OPENROUTER_API_KEY", "")

MAX_PICKS = 5            # cap sections routed -> keeps the parallel fan-out fast
CONCURRENCY = 24
MAX_SECTION_CHARS = 7000  # truncate very long statute texts before extraction/scan
PIPELINE_BUDGET = int(os.environ.get("GORGIAS_BUDGET", "43"))  # wall-clock ceiling (s); FE times out at 45s
CALL_TIMEOUT = 40        # per-GLM-call HTTP timeout (s)

STAT_TAG = "State Statutes"
FISC_TAG = "Public Finance Records · 26.6B records"


# ---------------------------------------------------------------------------
# corpus load (once, at import)
# ---------------------------------------------------------------------------
def _load_json(p):
    with open(p) as f:
        return json.load(f)


CRAWL = _load_json(PIPE_OUT / "crawl-nodes.json")
SECTIONS = CRAWL["nodes"]                        # slug -> {cite, heading, text, source_url, ...}
INDEX_LINES = {slug: f"{slug}\t{v['cite']}\t{v['heading']}" for slug, v in SECTIONS.items()}

# lexical index for routing prefilter: a lowercase word bag per section (heading + cite + body).
STOP = set("the a an of to and or for in on at by is are be as with that this from which "
           "any all not no if it its their his her they them may must shall than then per "
           "each such other into out up down over under more less most least".split())
_word = re.compile(r"[a-z0-9]{3,}")


def _bag(text):
    return set(_word.findall((text or "").lower())) - STOP


SECTION_BAG = {slug: _bag(v["heading"] + " " + v["cite"] + " " + v["text"])
               for slug, v in SECTIONS.items()}
SHORTLIST_N = 90                                 # candidates handed to the GLM router


def prefilter(policy):
    """Lexically score sections against the policy and return the top-N slugs for routing."""
    terms = _bag(policy)
    if not terms:
        return list(SECTIONS.keys())
    scored = []
    for slug, v in SECTIONS.items():
        bag = SECTION_BAG[slug]
        hits = terms & bag
        if not hits:
            continue
        # weight heading/cite matches higher than body-only matches
        head = _bag(v["heading"] + " " + v["cite"])
        score = len(hits) + 2 * len(terms & head)
        scored.append((score, slug))
    scored.sort(reverse=True)
    shortlist = [s for _, s in scored[:SHORTLIST_N]]
    return shortlist or list(SECTIONS.keys())

# cached T1 extractions (t1c-<slug>.json) so we skip a live extraction where we can
T1_CACHE = {}
for p in PIPE_OUT.glob("t1c-*.json"):
    T1_CACHE[p.name[len("t1c-"):-len(".json")]] = _load_json(p)

WORKER_PROMPT = (ROOT / "pipeline" / "WORKER_PROMPT.md").read_text()

# hero scenario supplies a modeled county distribution + a teaser baseline for scaling
try:
    HERO = _load_json(APP_DATA / "scenario-homestead.json")
    HERO_COUNTIES = HERO.get("counties", [])
    HERO_TEASER = abs(HERO.get("policy", {}).get("teaser_total_usd") or 0) or 1
except Exception:
    HERO_COUNTIES, HERO_TEASER = [], 1


# ---------------------------------------------------------------------------
# verbatim validation (mirrors pipeline/herd.py)
# ---------------------------------------------------------------------------
def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def verbatim_in(excerpt, source):
    return bool(excerpt) and norm(excerpt) in norm(source)


# ---------------------------------------------------------------------------
# GLM plumbing
# ---------------------------------------------------------------------------
def _post(messages, max_tokens):
    payload = {
        "model": MODEL, "temperature": 0.1, "max_tokens": max_tokens,
        "reasoning": {"effort": "low"},        # keep reasoning from eating the token budget
        "provider": {"sort": "latency"},       # route to the lowest-latency provider for this model
        "messages": messages,
    }
    req = urllib.request.Request(
        OPENROUTER_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "X-Title": "gorgias-live"})
    with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as r:
        data = json.load(r)
    msg = data["choices"][0]["message"]
    content = msg.get("content") or msg.get("reasoning") or ""
    return content.strip()


async def glm(messages, max_tokens=4000):
    return await asyncio.to_thread(_post, messages, max_tokens)


def parse_json(text):
    """Strip markdown fences and parse the first JSON object/array."""
    t = re.sub(r"^```(json)?|```$", "", text, flags=re.M).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"[\{\[].*[\}\]]", t, re.S)
        if m:
            return json.loads(m.group(0))
        raise


# ---------------------------------------------------------------------------
# pipeline stages
# ---------------------------------------------------------------------------
ROUTER_SYS = (
    "You are the routing stage of GORGIAS, a Texas policy-impact simulator. Given a proposed "
    "policy change and an INDEX of available statute sections (one per line: slug<TAB>cite<TAB>heading), "
    "select the sections whose text is most likely DIRECTLY altered by, or in conflict with, the change. "
    "Prefer sections that fix dollar amounts, rates, or percentages; define governing terms; or impose "
    "duties the change would shift. Return ONLY JSON: {\"picks\":[\"slug\", ...], \"why\":\"<=12 words\"}. "
    f"Pick between 4 and {MAX_PICKS} slugs, most relevant first. Use slugs exactly as they appear in the INDEX."
)


async def route(policy):
    shortlist = prefilter(policy)
    index_text = "\n".join(INDEX_LINES[s] for s in shortlist)
    out = await glm([
        {"role": "system", "content": ROUTER_SYS},
        {"role": "user", "content": f"PROPOSED CHANGE:\n{policy}\n\nINDEX:\n{index_text}"},
    ], max_tokens=2500)
    picked = parse_json(out).get("picks", [])
    seen, clean = set(), []
    for s in picked:
        if s in SECTIONS and s not in seen:
            seen.add(s)
            clean.append(s)
    return clean[:MAX_PICKS]


def section_text(slug):
    """Section body, truncated at a sentence boundary so verbatim excerpts still match."""
    t = SECTIONS[slug]["text"]
    if len(t) <= MAX_SECTION_CHARS:
        return t
    cut = t[:MAX_SECTION_CHARS]
    dot = cut.rfind(". ")
    return cut[:dot + 1] if dot > 1000 else cut


async def extract_t1(slug):
    """Return a T1 extraction for a section — from cache if available, else live."""
    if slug in T1_CACHE:
        return T1_CACHE[slug]
    sec = SECTIONS[slug]
    inp = {"task": "T1", "cite_hint": sec["cite"], "source_url": sec.get("source_url", ""),
           "text": section_text(slug)}
    out = await glm([{"role": "system", "content": WORKER_PROMPT},
                     {"role": "user", "content": json.dumps(inp)}], max_tokens=4500)
    return parse_json(out)


async def scan_t2(slug, policy):
    """Live conflict scan of a section against the typed policy."""
    sec = SECTIONS[slug]
    inp = {"task": "T2", "proposed_change": policy, "rule_cite": sec["cite"],
           "rule_text": section_text(slug)}
    out = await glm([{"role": "system", "content": WORKER_PROMPT},
                     {"role": "user", "content": json.dumps(inp)}], max_tokens=3500)
    return parse_json(out)


ASSEMBLER_SYS = (
    "You are the framing stage of GORGIAS. You receive a proposed Texas policy change and the statute + "
    "conflict nodes GORGIAS already extracted (with real cites). Produce ONLY the MODELED framing around "
    "them. Do NOT restate statute text. Return ONLY JSON of the form:\n"
    "{\n"
    '  "policy": {"title": "<=9 words", "delta_label": "<the concrete change, e.g. +$60,000 per homestead>"},\n'
    '  "agencies": [{"label","cite","authority_cite","approval_gate","action_required (<=24 words)","clock_days":int,"parent":"<node id from the list>"}],\n'
    '  "budgets": [{"label","cite","delta_usd":int,"parent":"<node id from the list>"}],\n'
    '  "verdict": {"exposure_statute_only_pct":int,"exposure_with_amendment_pct":int,"drivers":["<node id or short phrase>"],"next_steps":[{"step","gate"}]}\n'
    "}\n"
    "Rules: 2-5 agencies, 2-4 budget lines. budget delta_usd is the annual dollar impact (NEGATIVE for a "
    "cost or revenue loss, POSITIVE for a gain), a realistic modeled magnitude for Texas. Every agency/budget "
    "parent MUST be one of the provided node ids. exposure percentages 0-100. 2-4 next_steps. All of this is "
    "modeled analysis, so keep it defensible but do not invent statute quotations."
)


async def assemble(policy, spine):
    node_list = [{"id": n["id"], "type": n["type"], "label": n["label"], "cite": n.get("cite"),
                  "severity": n.get("severity")} for n in spine]
    out = await glm([
        {"role": "system", "content": ASSEMBLER_SYS},
        {"role": "user", "content": "PROPOSED CHANGE:\n" + policy + "\n\nEXTRACTED NODES:\n"
         + json.dumps(node_list, indent=1)},
    ], max_tokens=3000)
    return parse_json(out)


# ---------------------------------------------------------------------------
# scenario assembly + validation
# ---------------------------------------------------------------------------
def fmt_usd(n):
    a = abs(n)
    if a >= 1e9:
        body = f"${a/1e9:.2f}B/yr"
    elif a >= 1e6:
        body = f"${round(a/1e6)}M/yr"
    else:
        body = f"${a:,.0f}"
    return ("−" if n < 0 else "+") + body


def build_scenario(policy, picks, t1s, t2s, framing):
    nodes = [{"id": "policy-root", "type": "policy", "parent": None,
              "label": framing.get("policy", {}).get("title", policy)[:60],
              "cite": (t1s[picks[0]].get("cite") if picks else None)}]
    drops = []
    valid_ids = {"policy-root"}

    # statutes (verbatim spine) ----------------------------------------------
    for slug in picks:
        t1 = t1s.get(slug) or {}
        sec = SECTIONS[slug]
        excerpt = t1.get("operative_text") or ""
        nid = "st-" + slug
        node = {
            "id": nid, "type": "statute", "parent": "policy-root",
            "label": (t1.get("heading") or sec["heading"]).title(),
            "cite": t1.get("cite") or sec["cite"], "heading": t1.get("heading") or sec["heading"],
            "corpus_tag": STAT_TAG, "excerpt": excerpt,
            "source_url": sec.get("source_url"), "verbatim": True,
        }
        if excerpt and not verbatim_in(excerpt, sec["text"]):
            node["verbatim"] = False
            node["modeled"] = True
            drops.append(nid)
        nodes.append(node)
        valid_ids.add(nid)

    # conflicts (verbatim quote spine) ---------------------------------------
    for slug in picks:
        t2 = t2s.get(slug) or {}
        if not t2.get("conflict"):
            continue
        sec = SECTIONS[slug]
        quote = t2.get("quote") or ""
        nid = "cf-" + slug
        node = {
            "id": nid, "type": "conflict", "parent": "st-" + slug,
            "label": (t2.get("rationale") or "Statutory conflict")[:80],
            "cite": sec["cite"], "corpus_tag": STAT_TAG,
            "severity": int(t2.get("severity") or 1), "excerpt": quote,
            "rationale": t2.get("rationale"), "source_url": sec.get("source_url"),
            "verbatim": True,
        }
        if quote and not verbatim_in(quote, sec["text"]):
            # a conflict without a valid verbatim quote is not trustworthy — demote to modeled
            node["verbatim"] = False
            node["modeled"] = True
            drops.append(nid)
        nodes.append(node)
        valid_ids.add(nid)

    def resolve_parent(hint, fallback):
        return hint if hint in valid_ids else fallback

    stat_fallback = ("st-" + picks[0]) if picks else "policy-root"
    conflict_ids = [n["id"] for n in nodes if n["type"] == "conflict"]

    # agencies (modeled) -----------------------------------------------------
    for i, a in enumerate(framing.get("agencies", [])[:5]):
        nid = "ag-" + str(i + 1)
        nodes.append({
            "id": nid, "type": "agency",
            "parent": resolve_parent(a.get("parent"), conflict_ids[0] if conflict_ids else stat_fallback),
            "label": a.get("label", "Agency action"), "cite": a.get("cite"),
            "authority_cite": a.get("authority_cite"), "corpus_tag": STAT_TAG,
            "approval_gate": a.get("approval_gate"),
            "clock_days": a.get("clock_days"), "action_required": a.get("action_required"),
            "modeled": True,
        })
        valid_ids.add(nid)

    # budgets (modeled) ------------------------------------------------------
    agency_ids = [n["id"] for n in nodes if n["type"] == "agency"]
    total = 0
    for i, b in enumerate(framing.get("budgets", [])[:4]):
        nid = "bd-" + str(i + 1)
        try:
            delta = int(b.get("delta_usd") or 0)
        except (TypeError, ValueError):
            delta = 0
        total += delta
        nodes.append({
            "id": nid, "type": "budget",
            "parent": resolve_parent(b.get("parent"), agency_ids[0] if agency_ids else stat_fallback),
            "label": b.get("label", "Budget line"), "cite": b.get("cite"),
            "corpus_tag": FISC_TAG, "delta_usd": delta, "basis": "modeled projection",
            "modeled": True,
        })
        valid_ids.add(nid)

    # counties: reuse the hero modeled distribution, scaled to this teaser -----
    counties = []
    if HERO_COUNTIES and total:
        scale = abs(total) / HERO_TEASER
        for c in HERO_COUNTIES:
            counties.append({"fips": c["fips"], "name": c["name"],
                             "impact_usd": round(c["impact_usd"] * scale),
                             "impact_pct": c.get("impact_pct")})

    n_conf = sum(1 for n in nodes if n["type"] == "conflict")
    n_ag = sum(1 for n in nodes if n["type"] == "agency")
    teaser_b = abs(total) / 1e9
    verdict = framing.get("verdict", {})

    scenario = {
        "policy": {
            "title": framing.get("policy", {}).get("title", policy),
            "delta_label": framing.get("policy", {}).get("delta_label", ""),
            "teaser_total_usd": total,
            "teaser_label": f"{fmt_usd(total).replace('+', '').replace('−', '−')}"
                            f" · {n_ag} agencies · {n_conf} statutory conflicts",
        },
        "nodes": nodes,
        "counties": counties,
        "verdict": {
            "exposure_statute_only_pct": verdict.get("exposure_statute_only_pct", 60),
            "exposure_with_amendment_pct": verdict.get("exposure_with_amendment_pct", 25),
            "drivers": verdict.get("drivers", []),
            "next_steps": verdict.get("next_steps", []),
        },
        "meta": {
            "live": True, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": policy, "routed_slugs": picks,
            "verbatim_nodes": [n["id"] for n in nodes if n.get("verbatim")],
            "modeled_nodes": [n["id"] for n in nodes if n.get("modeled")],
            "verbatim_drops": drops,
            "counties_modeled": bool(counties),
            "note": ("Live GLM build. Statute + conflict excerpts are verbatim from the scraped Texas "
                     "corpus and validated server-side; agencies, budget magnitudes, and the county "
                     "distribution are modeled."),
        },
    }
    return scenario, drops


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="GORGIAS live")


@app.get("/health")
async def health():
    return {"ok": True, "sections": len(SECTIONS), "cached_t1": len(T1_CACHE),
            "model": MODEL, "key": bool(KEY)}


@app.get("/simulate")
async def simulate(policy: str):
    policy = (policy or "").strip()
    if not policy:
        return JSONResponse({"error": "empty policy"}, status_code=400)
    if not KEY:
        return JSONResponse({"error": "OPENROUTER_API_KEY not set on server"}, status_code=503)

    t0 = time.time()
    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded(coro):
        async with sem:
            return await coro

    async def pipeline():
        picks = await route(policy)
        if not picks:
            return JSONResponse({"error": "router found no relevant sections"}, status_code=422)
        t_route = time.time() - t0

        # T1 (extract) + T2 (conflict scan) fan out together — one parallel wave
        t1_tasks = [guarded(extract_t1(s)) for s in picks]
        t2_tasks = [guarded(scan_t2(s, policy)) for s in picks]
        results = await asyncio.gather(*t1_tasks, *t2_tasks, return_exceptions=True)
        n = len(picks)
        t1_res, t2_res = results[:n], results[n:]
        t1s = {s: (r if not isinstance(r, Exception) else {}) for s, r in zip(picks, t1_res)}
        t2s = {s: (r if not isinstance(r, Exception) else {}) for s, r in zip(picks, t2_res)}
        t_extract = time.time() - t0

        framing = await assemble(policy, [
            {"id": "st-" + s, "type": "statute",
             "label": (t1s[s].get("heading") or SECTIONS[s]["heading"]).title(),
             "cite": t1s[s].get("cite") or SECTIONS[s]["cite"]} for s in picks
        ] + [
            {"id": "cf-" + s, "type": "conflict",
             "label": (t2s[s].get("rationale") or "conflict")[:70],
             "cite": SECTIONS[s]["cite"], "severity": t2s[s].get("severity")}
            for s in picks if t2s[s].get("conflict")
        ])

        scenario, drops = build_scenario(policy, picks, t1s, t2s, framing)
        scenario["meta"]["timing_s"] = {
            "route": round(t_route, 2), "extract": round(t_extract, 2),
            "total": round(time.time() - t0, 2),
        }
        return JSONResponse(scenario)

    try:
        return await asyncio.wait_for(pipeline(), timeout=PIPELINE_BUDGET)
    except asyncio.TimeoutError:
        return JSONResponse({"error": f"pipeline exceeded {PIPELINE_BUDGET}s budget",
                             "elapsed_s": round(time.time() - t0, 2)}, status_code=504)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}",
                             "elapsed_s": round(time.time() - t0, 2)}, status_code=500)


# static app LAST so /health and /simulate win; html=True serves index.html at /
app.mount("/", StaticFiles(directory=str(HERE), html=True), name="app")
