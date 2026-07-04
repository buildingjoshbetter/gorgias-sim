#!/usr/bin/env python3
"""Inline real data + DrawerEngine into app/index.html before </body>.
Idempotent: strips any prior B1 block (between the marker comments) first, then re-injects.
Embeds scenario-homestead.json as window.SCENARIO_REAL and tx-counties.svg.json as
window.COUNTY_PATHS so file:// works with real data and real county geometry.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "app", "index.html")
SCEN = os.path.join(ROOT, "app", "data", "scenario-homestead.json")
GEOM = os.path.join(ROOT, "app", "data", "tx-counties.svg.json")
DRAWER_JS = os.path.join(ROOT, "pipeline", "drawer_engine.js")
DRAWER_CSS = os.path.join(ROOT, "pipeline", "drawer.css")

START = "<!-- B1-INLINE-START: real data + citation drawer (do not hand-edit; regen via pipeline/inject_drawer.py) -->"
END = "<!-- B1-INLINE-END -->"


def safe_json(path):
    # embed JSON in a <script>; neutralize any "</" that could close the tag early
    with open(path) as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


scenario_js = safe_json(SCEN)
county_js = safe_json(GEOM)
with open(DRAWER_JS) as f:
    drawer_js = f.read()
with open(DRAWER_CSS) as f:
    drawer_css = f.read()

block = (
    START + "\n"
    "<style>\n" + drawer_css + "</style>\n"
    "<script>\n"
    '"use strict";\n'
    "window.SCENARIO_REAL = " + scenario_js + ";\n"
    "window.COUNTY_PATHS = " + county_js + ";\n"
    + drawer_js +
    "</script>\n"
    + END
)

with open(INDEX) as f:
    html = f.read()

# strip prior injected block if present
html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.DOTALL).rstrip() + "\n"

if "</body>" not in html:
    raise SystemExit("no </body> in index.html")
html = html.replace("</body>", block + "\n</body>", 1)

with open(INDEX, "w") as f:
    f.write(html)

print("Injected B1 block into", INDEX)
print("  scenario bytes:", len(scenario_js), "| county-geom bytes:", len(county_js))
print("  drawer JS bytes:", len(drawer_js), "| CSS bytes:", len(drawer_css))
print("  index.html total bytes:", len(html))
