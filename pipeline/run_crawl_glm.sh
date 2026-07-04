#!/bin/bash
# Driver: run all crawl GLM batches, budget-gated at $120 cumulative.
set -e
set -a && source /private/tmp/claude-501/-Users-j/2fb47d4a-d2c1-43d0-89fd-50578e0c2e66/scratchpad/openrouter.env && set +a
cd /Users/j/Desktop/patriot-games-hackathon/gorgias/pipeline
PY=../.venv/bin/python
BUDGET=120.0

spend() {
  $PY -c "import json;print(round(sum((json.loads(l).get('cost',0) or 0) for l in open('out/herd-manifest.jsonl')),4))" 2>/dev/null || echo 0
}

for b in jobs/batches/t1_*.jsonl jobs/batches/t2_*.jsonl; do
  cur=$(spend)
  over=$($PY -c "print(1 if float('$cur')>=$BUDGET else 0)")
  if [ "$over" = "1" ]; then echo "BUDGET STOP at \$$cur before $b"; break; fi
  echo "=== batch $b (cumulative \$$cur) ==="
  $PY herd.py "$b" 2>&1 | tail -3
done
echo "FINAL cumulative spend: \$$(spend)"
