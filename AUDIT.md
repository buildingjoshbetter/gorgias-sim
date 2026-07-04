# Gorgias data audit

Scope: every number and excerpt displayed by the hero scenario
(`app/data/scenario-homestead.json`), cross-checked against the raw scrapes
(`pipeline/out/raw/*.json`), the validated extractions (`pipeline/out/*.json`), and the
county model (`data/county-impact.json`).

Verdict method: statute and conflict excerpts are checked by whitespace-normalized
string containment against the raw source text (the same test the extraction fleet
applied). Budget figures are traced to the Legislative Budget Board fiscal-note text.
County figures are summed and matched to the teaser total.

## Result

**Zero unresolved discrepancies.** Every quoted excerpt is a verbatim substring of a
fetched source. Every actual dollar figure traces to a fiscal note. Every modeled
number is labeled modeled in the data file. The 254-county map sums exactly to the
statewide teaser. Three items are disclosed below as analytical/modeled rather than
sourced — none is an error, each is correctly non-verbatim by design.

The one high-risk node cleared: for the $140k → $200k scenario, `cf-const` is
correctly **severity 3** (a $200,000 statute exceeds the $140,000 amount written into
art. VIII §1-b(c), so it needs a constitutional amendment first). The automated T2
conflict scan had returned severity 0 / conflict:false — but that scan was run against
the historical $100k→$140k change, which matched the existing constitution. B1 did not
ship the stale value; it re-derived the conflict from the constitutional ceiling. This
was the audit's primary trap and it is clean.

## Node-by-node

Legend: VERIFIED = excerpt is a verbatim substring of the cited source; MODELED-LABELED
= non-verbatim by design and flagged as such in the data; ANALYTICAL = an
severity/authority judgment, not a quoted fact.

| Node | Value audited | Source | URL | Verdict |
|------|---------------|--------|-----|---------|
| st-1113b | "$140,000 of the appraised value…" | Tax Code §11.13(b) | statutes.capitol.texas.gov/Docs/TX/htm/TX.11.htm | VERIFIED (365-char substring) |
| st-1113n | optional %-exemption subsection (n)/(n-1) | Tax Code §11.13(n) | TX.11.htm | VERIFIED (880 chars) |
| st-1126 | 65+/disabled tax-ceiling operative text | Tax Code §11.26 | TX.11.htm | VERIFIED (803 chars) |
| st-2609 | §26.09(c) tax-calculation steps | Tax Code §26.09 | TX.26.htm | VERIFIED (536 chars) — hand-extracted after 3 GLM verbatim failures; re-verified |
| st-4825x | §48.2556 hold-harmless posting | Educ. Code §48.2556 | ED.48.htm | VERIFIED (1204 chars) |
| st-48255 | state compression percentage | Educ. Code §48.255 | ED.48.htm | VERIFIED (890 chars) |
| st-const | full art. VIII §1-b(c), $140,000 + $60,000 | Tex. Const. art. VIII §1-b(c) | CN.8.htm | VERIFIED (2413 chars) |
| cf-const | "$140,000 … cannot take effect until voters ratify" | Tex. Const. art. VIII §1-b(c) | CN.8.htm | VERIFIED excerpt; severity 3 ANALYTICAL (correct for $200k) |
| cf-ceiling | §11.26(a-10) cross-reference formula quote | Tax Code §11.26 | TX.11.htm | VERIFIED excerpt; **severity 2 ANALYTICAL — see flag 1** |
| cf-tacrule | 34 TAC Ch. 9 Subch. H rulemaking | 34 TAC Ch. 9 | — (TAC portal is JS/Appian, not scraped) | MODELED-LABELED (`modeled:true`) |
| ag-cpa | Comptroller PTAD action | Gov. Code §403 (authority cite) | — | ANALYTICAL — see flag 2 |
| ag-tea | TEA FSP recompute | Educ. Code §48.255 (authority cite) | — | ANALYTICAL — see flag 2 |
| ag-sos | SOS amendment-election admin | Election Code §274 (authority cite) | — | ANALYTICAL — see flag 2 |
| ag-cads | 254 CADs reprogram CAMA | — | — | MODELED-LABELED (`modeled:true`) |
| bd-fsp | actual −$465,216,000; modeled −$697,824,000 | LBB fiscal note SB4 (89R) | capitol.texas.gov/tlodocs/89R/fiscalnotes/html/SB00004I.htm | actual VERIFIED in fiscal note; projection MODELED-LABELED (×1.5) |
| bd-mno | actual −$1,481,778,000; modeled −$2,222,667,000 | LBB fiscal note SB4 (89R) | SB00004I.htm | actual VERIFIED; projection MODELED-LABELED (×1.5) |
| bd-recap | actual −$337,033,000; modeled −$505,549,500 | LBB fiscal note SB4 (89R) | SB00004I.htm | actual VERIFIED; projection MODELED-LABELED (×1.5) |
| bd-cnty | per-county school M&O levy delta | Comptroller 2025 school-district rates & levies | comptroller.texas.gov/…/2025-school-district-rates-levies.xlsx | MODELED-LABELED (methodology string in file) |
| counties[254] | impact_usd per county + `impact_pct` | derived from Comptroller 2025 levies | same XLSX | MODELED-LABELED; 0/254 mismatch vs `county-impact.json` |
| policy.teaser_total_usd | −$2,673,098,745 | sum of 254 county `impact_usd` | computed | VERIFIED sum (matches $2,673,098,744.76 rounded) |
| verdict exposure | 90% statute-only / 22% with-amendment | — | — | ANALYTICAL (modeled verdict outputs) |

## Cross-cutting checks

- **Verbatim containment:** all 7 statute excerpts and both quoted conflict excerpts
  pass whitespace-normalized substring match against the raw chapter scrapes. The
  extraction-layer `operative_text` for all 7 T1 jobs also passes, including the
  hand-extracted §26.09.
- **Fiscal actuals:** all three budget-node calibration figures ($465,216,000 /
  $1,481,778,000 / $337,033,000) are verbatim in the SB4 89R fiscal-note text. All 45
  fiscal rows across the SB4 and SB23 extractions were separately confirmed verbatim
  against their raw notes (0 missing).
- **Modeled scaling:** each budget projection is exactly 1.5× its 2025 actual
  (465,216,000×1.5 = 697,824,000; 1,481,778,000×1.5 = 2,222,667,000; 337,033,000×1.5 =
  505,549,500). The 1.5 factor is the $60k/$40k ratio of the new increment to the 2025
  actual increment; disclosed in `meta.calibration` and in each excerpt.
- **County sum:** Σ impact_usd over 254 counties = $2,673,098,744.76 →
  `teaser_total_usd` = −2,673,098,745. Consistent. Per-county values match
  `county-impact.json` exactly (0 mismatches).
- **Top-10 order:** real data yields Harris, Dallas, Travis, Tarrant, Collin, Bexar,
  Denton, Williamson, Fort Bend, Montgomery. This differs from the build-prompt A.6
  *prediction* (which listed Hidalgo and a different mid-order). The data is
  authoritative and A.6 anticipated this ("P2 confirms order from real data"); the
  map/strip must read order from the JSON, not the A.6 list. Not a discrepancy.
- **Framing:** no residual "$100,000" (old-scenario) text anywhere in the data file;
  every node uses the $140k→$200k framing.
- **Source provenance:** all 11 `meta.sources` URLs and retrieved-at timestamps match
  `pipeline/out/manifest.json`.

## Flags (disclosed, not fixed — analytical judgments, ambiguous by nature)

1. **cf-ceiling severity 2 vs automated scan severity 1.** The excerpt (the §11.26(a-10)
   formula) is verbatim. The severity is an analytical rating. The build-prompt A.3
   design assigns cf-ceiling severity 2 ("the classic consequential-amendment miss");
   the automated T2 conflict scan returned severity 1, and B1's own rationale notes the
   formula "auto-incorporates the $200,000 amount" (a severity-1 mechanism) while the
   frozen-ceiling gap widening supports the higher rating. Defensible either way; left
   at the design value 2 and disclosed here. Severity is presented as the simulator's
   assessment, not a quoted fact, so this is not a sourcing error.

2. **Agency nodes ag-cpa / ag-tea / ag-sos have authority cites but no verbatim
   excerpt and are not `modeled`-flagged.** No T5 agency-map extraction was run; these
   three are structural/analytical nodes hardcoded from A.4, each pointing at a real
   authority statute (Gov. Code §403, Educ. Code §48.255, Election Code §274). They are
   not presented as quoted source text. Recommendation for polish (non-blocking): give
   these an "analytical" drawer treatment distinct from the verbatim-sourced statute
   nodes so a judge clicking them does not expect a highlighted quote. `ag-cads` is
   already correctly `modeled`-flagged.

3. **§26.09 was hand-extracted.** GLM failed the verbatim check three times
   (`herd-manifest.jsonl` records all three `invalid` attempts); the operative text was
   then hand-pulled from the source and re-verified. It passes containment. Noted for
   transparency — the manifest's failed attempts are part of the honest audit trail,
   not something to hide.

## Bottom line

The hero scenario is safe to demo and safe to open to inspection. Anything a judge
clicks that shows a quotation is a verbatim quotation; anything that shows a projected
dollar figure is labeled modeled with its calibration source one line away.
