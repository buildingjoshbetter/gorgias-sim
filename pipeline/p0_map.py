#!/usr/bin/env python3
"""P0 — Texas county map geometry.

Fetch plotly geojson-counties-fips.json, filter STATE=="48" (must yield exactly
254 Texas counties), project lon/lat to a 900x860 viewBox (equirectangular, fit to
Texas bounds with a 20px margin, Y flipped), emit gorgias/data/tx-counties.svg.json
as [{fips, name, d}] with d-strings rounded to 1 decimal.
"""

import json
import os
from datetime import datetime, timezone

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))
OUT = os.path.join(DATA, "tx-counties.svg.json")

GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)

VIEW_W = 900.0
VIEW_H = 860.0
MARGIN = 20.0


def fetch_geojson():
    with httpx.Client(timeout=60.0, follow_redirects=True) as c:
        r = c.get(GEOJSON_URL)
        r.raise_for_status()
        return r.json()


def iter_rings(geom):
    """Yield each linear ring as a list of [lon, lat] pairs."""
    t = geom["type"]
    coords = geom["coordinates"]
    if t == "Polygon":
        for ring in coords:
            yield ring
    elif t == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                yield ring
    else:
        raise ValueError(f"unexpected geometry type {t}")


def main():
    gj = fetch_geojson()
    feats = [f for f in gj["features"] if f["properties"].get("STATE") == "48"]
    if len(feats) != 254:
        raise SystemExit(f"expected 254 TX counties, got {len(feats)}")

    # First pass: compute lon/lat bounds across all TX rings.
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")
    for f in feats:
        for ring in iter_rings(f["geometry"]):
            for lon, lat in ring:
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)

    span_lon = max_lon - min_lon
    span_lat = max_lat - min_lat
    # Uniform scale to fit inside the margined viewBox, preserving aspect ratio.
    avail_w = VIEW_W - 2 * MARGIN
    avail_h = VIEW_H - 2 * MARGIN
    scale = min(avail_w / span_lon, avail_h / span_lat)
    # Center the projected shape within the viewBox.
    off_x = MARGIN + (avail_w - span_lon * scale) / 2.0
    off_y = MARGIN + (avail_h - span_lat * scale) / 2.0

    def project(lon, lat):
        x = off_x + (lon - min_lon) * scale
        # Flip Y: larger latitude -> smaller y (north at top).
        y = off_y + (max_lat - lat) * scale
        return round(x, 1), round(y, 1)

    out = []
    total_bytes = 0
    for f in feats:
        props = f["properties"]
        fips = props["STATE"] + props["COUNTY"]
        name = props.get("NAME", "")
        parts = []
        for ring in iter_rings(f["geometry"]):
            pts = [project(lon, lat) for lon, lat in ring]
            seg = ["M{:.1f},{:.1f}".format(*pts[0])]
            for x, y in pts[1:]:
                seg.append("L{:.1f},{:.1f}".format(x, y))
            seg.append("Z")
            parts.append("".join(seg))
        d = "".join(parts)
        total_bytes += len(d)
        out.append({"fips": fips, "name": name, "d": d})

    out.sort(key=lambda r: r["fips"])
    with open(OUT, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))

    print(f"counties: {len(out)}")
    print(f"total path d bytes: {total_bytes}")
    print(f"file size: {os.path.getsize(OUT)} bytes")
    print(f"lon bounds: {min_lon:.3f}..{max_lon:.3f}  lat bounds: {min_lat:.3f}..{max_lat:.3f}")
    print(f"scale: {scale:.3f}  offset: ({off_x:.1f},{off_y:.1f})")
    print(f"wrote {OUT}  at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
