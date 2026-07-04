"""GLM extraction fleet for Gorgias. Schema-validated, budget-capped."""
import asyncio, json, os, re, sys
from pathlib import Path
import urllib.request

KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"
HERE = Path(__file__).parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
MANIFEST = OUT / "herd-manifest.jsonl"
WP = (HERE / "WORKER_PROMPT.md").read_text()
CONCURRENCY, HARD_STOP = int(os.environ.get("HERD_CONCURRENCY", "24")), 200.0
MODEL = os.environ.get("HERD_MODEL", "z-ai/glm-5.2")
_spent = 0.0
_lock = None

def norm(s): return re.sub(r"\s+", " ", s or "").strip().lower()

REQ = {"T1": ["cite","heading","operative_text"], "T2": ["conflict","severity","rationale","quote"],
       "T3": ["rows"], "T5": ["agencies"]}

def validate(task, p, inp):
    for k in REQ.get(task, []):
        if k not in p: return False, f"missing {k}"
    src = norm(inp.get("text","") + inp.get("rule_text","") + json.dumps(inp.get("statute_texts",{})))
    for field in ("operative_text","quote"):
        v = p.get(field)
        if v and norm(v) not in src: return False, f"{field} not verbatim"
    if task == "T2" and p.get("conflict") and not p.get("quote"): return False, "conflict without quote"
    return True, "ok"

async def post(payload):
    def _do():
        req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                     "X-Title": "gorgias-herd"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    return await asyncio.to_thread(_do)

async def run_job(sem, job):
    global _spent
    async with sem:
        why = "?"
        for attempt, backoff in [(1,2),(2,8),(3,None)]:
            async with _lock:
                if _spent >= HARD_STOP: return {"id": job["id"], "status": "budget_stop"}
            try:
                data = await post({"model": MODEL, "temperature": 0.1, "max_tokens": 8000,
                    "usage": {"include": True},
                    "messages": [{"role":"system","content":WP},
                                 {"role":"user","content":json.dumps(job["input"])}]})
                cost = float(data.get("usage",{}).get("cost") or 0)
                async with _lock: _spent += cost
                text = data["choices"][0]["message"]["content"].strip()
                text = re.sub(r"^```(json)?|```$", "", text, flags=re.M).strip()
                parsed = json.loads(text)
                ok, why = validate(job["input"]["task"], parsed, job["input"])
                rec = {"id": job["id"], "task": job["input"]["task"], "attempt": attempt,
                       "cost": round(cost,5), "spent": round(_spent,3),
                       "status": "ok" if ok else "invalid", "why": why}
                with MANIFEST.open("a") as m: m.write(json.dumps(rec)+"\n")
                if ok:
                    (OUT / f"{job['id']}.json").write_text(json.dumps(parsed, indent=1))
                    return rec
            except Exception as e:
                why = f"{type(e).__name__}: {e}"
            if backoff is None: return {"id": job["id"], "status": "failed", "why": why}
            await asyncio.sleep(backoff)

async def main(paths):
    global _lock; _lock = asyncio.Lock()
    jobs = []
    for p in paths:
        for l in Path(p).read_text().splitlines():
            if not l.strip(): continue
            raw = json.loads(l)
            if "input" in raw: jobs.append(raw)
            else:
                jid = raw.pop("job_id"); raw.pop("worker_version", None)
                jobs.append({"id": jid, "input": raw})
    sem = asyncio.Semaphore(CONCURRENCY)
    res = await asyncio.gather(*[run_job(sem, j) for j in jobs])
    ok = [r for r in res if r and r["status"]=="ok"]
    print(f"done: {len(ok)}/{len(jobs)} ok, ${_spent:.3f} spent")
    for r in res:
        if r and r["status"] != "ok": print("PROBLEM:", json.dumps(r))

if __name__ == "__main__": asyncio.run(main(sys.argv[1:]))
