#!/bin/bash
set -a && source /private/tmp/claude-501/-Users-j/2fb47d4a-d2c1-43d0-89fd-50578e0c2e66/scratchpad/openrouter.env && set +a
cd /Users/j/Desktop/patriot-games-hackathon/gorgias/pipeline
PY=../.venv/bin/python; BUDGET=120.0
spend(){ $PY -c "import json;print(round(sum((json.loads(l).get('cost',0) or 0) for l in open('out/herd-manifest.jsonl')),4))" 2>/dev/null||echo 0; }
for b in jobs/t2only/t2_*.jsonl; do
  cur=$(spend)
  if [ "$($PY -c "print(1 if float('$cur')>=$BUDGET else 0)")" = "1" ]; then echo "BUDGET STOP \$$cur"; break; fi
  echo "=== $b (cum \$$cur) ==="
  $PY herd.py "$b" 2>&1 | grep -E "done:|PROBLEM" | tail -3
done
echo "FINAL cumulative spend: \$$(spend)"
