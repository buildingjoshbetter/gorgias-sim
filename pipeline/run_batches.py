#!/usr/bin/env python3
"""Batch driver for herd.py — runs job files in ~150-job batches at concurrency
24, prints cumulative manifest spend after each batch, and hard-stops at a
global budget read from the authoritative manifest (survives across processes).

Usage: run_batches.py <global_cap_usd> <batch_size> <jobfile> [jobfile ...]
"""
import asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import herd  # noqa: E402

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "out" / "herd-manifest.jsonl"


def cumulative_spend() -> float:
    if not MANIFEST.exists():
        return 0.0
    tot = 0.0
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            tot += json.loads(line).get("cost", 0) or 0
        except Exception:
            pass
    return tot


def load_jobs(path: Path):
    """Load jobs, skipping any whose GLM output already exists (resume-safe)."""
    out = HERE / "out"
    jobs = []
    for l in path.read_text().splitlines():
        if not l.strip():
            continue
        raw = json.loads(l)
        if "input" in raw:
            job = raw
        else:
            jid = raw.pop("job_id")
            raw.pop("worker_version", None)
            job = {"id": jid, "input": raw}
        if (out / f"{job['id']}.json").exists():
            continue
        jobs.append(job)
    return jobs


async def run_batch(jobs):
    herd._lock = asyncio.Lock()
    herd._spent = 0.0  # per-batch; global tracking via manifest
    sem = asyncio.Semaphore(herd.CONCURRENCY)
    res = await asyncio.gather(*[herd.run_job(sem, j) for j in jobs])
    ok = sum(1 for r in res if r and r.get("status") == "ok")
    return ok, len(jobs)


def main():
    cap = float(sys.argv[1])
    bs = int(sys.argv[2])
    files = sys.argv[3:]
    start = cumulative_spend()
    print(f"[driver] start cumulative=${start:.3f} global_cap=${cap:.0f} batch={bs}", flush=True)
    total_ok = total = 0
    for f in files:
        jobs = load_jobs(Path(f))
        print(f"[driver] {f}: {len(jobs)} jobs", flush=True)
        for i in range(0, len(jobs), bs):
            cum = cumulative_spend()
            if cum >= cap:
                print(f"[driver] GLOBAL CAP HIT cumulative=${cum:.3f} — stopping", flush=True)
                print(f"[driver] DONE ok={total_ok}/{total} cumulative=${cum:.3f}", flush=True)
                return
            batch = jobs[i:i + bs]
            ok, n = asyncio.run(run_batch(batch))
            total_ok += ok
            total += n
            cum = cumulative_spend()
            print(f"[driver] batch {i//bs+1} of {f.split('/')[-1]}: {ok}/{n} ok | "
                  f"run_total {total_ok}/{total} | cumulative=${cum:.3f}", flush=True)
    print(f"[driver] DONE ok={total_ok}/{total} cumulative=${cumulative_spend():.3f}", flush=True)


if __name__ == "__main__":
    main()
