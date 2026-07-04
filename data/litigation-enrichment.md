# Litigation & rulemaking enrichment (D4)

Research pass to make the verdict scene cite-hard. Every fact below was fetched and cross-checked against at least two sources (case reporters / NCES lawsuit PDFs / the Neeley opinion text / Ballotpedia + LRL Texas / Cornell LII + Texas Administrative Code / comptroller.texas.gov).

## 1. School-finance litigation lineage (Edgewood I -> West Orange-Cove)

The through-line the verdict needs: Texas has an affirmative constitutional duty to fund an *efficient* school system, and it may **not** discharge that duty by (a) simply adding state money without fixing structure, or (b) squeezing local property-tax discretion until the local tax is a de facto statewide tax. A homestead-exemption increase that erodes the local base — while spending mandates hold — lands squarely on both theories.

| Case | Cite | Year | Holding (one line) |
|------|------|------|--------------------|
| Edgewood ISD v. Kirby (**Edgewood I**) | 777 S.W.2d 391 (Tex. 1989) | 1989 | System violated Art. VII §1 "efficiency"; districts must have *substantially equal access to similar revenues per pupil at similar tax effort*. |
| Edgewood ISD v. Kirby (**Edgewood II**) | 804 S.W.2d 491 (Tex. 1991) | 1991 | SB 1 fix still failed — adding state money without structural change does not cure the defect. |
| Carrollton-Farmers Branch ISD v. Edgewood ISD (**Edgewood III**) | 826 S.W.2d 489 (Tex. 1992) | 1992 | An ad valorem tax becomes an unconstitutional **statewide** property tax (Art. VIII §1-e) when the State so controls levy/assessment/disbursement that districts have *no meaningful discretion*; County Education District tax struck. |
| Edgewood ISD v. Meno (**Edgewood IV**) | 917 S.W.2d 717 (Tex. 1995) | 1995 | SB 7 (incl. recapture / "Robin Hood") upheld, but "minimally acceptable only when viewed through the prism of history." |
| **Neeley v. West Orange-Cove** Consolidated ISD | 176 S.W.3d 746 (Tex. 2005) | 2005 | Local taxes had become an unconstitutional state property tax — State left districts "no meaningful discretion to tax below maximum rates." Structural warning renewed. |

Note on numbering: the Texas Supreme Court's own *Neeley* opinion labels Carrollton-Farmers Branch (826 S.W.2d 489) as **Edgewood III** and quotes its ad valorem test directly — that numbering is used here.

## 2. Prop 13 / the 2025 legislative record (the "last walked Nov 2025" precedent)

- Joint resolution: **SJR 2**, 89th Legislature R.S. (2025). Enabling statute: **SB 4**.
- Ballot: **Proposition 13**, statewide constitutional-amendment election **Nov 4, 2025**.
- Result: **Yes 2,348,815 (79.41%)** / No 609,203 (20.59%). Officially certified.
- Effect: raised the school-district homestead exemption **$100,000 -> $140,000**.

## 3. 34 TAC property-tax rules (Title 34, Part 1, Chapter 9) — homestead administration

All verified against the Texas Administrative Code (txrules.elaws.us) and, for §9.415, Cornell LII.

- **§9.415 — Applications for Property Tax Exemptions** (Subch. C). Governs the residence-homestead exemption application and the forms the Comptroller prescribes; §9.415(b) ties district forms to the most recently prescribed Comptroller form — i.e. the one that states the exemption amount. This is the rule that goes stale the moment the constitutional amount changes.
- **§9.416 — Continuation of Residence Homestead Exemption While Replacement Structure is Constructed** (Subch. C).
- **§9.3010 — Partial Exemption Lists** (Subch. H). Appraisal-record rule covering partial exemptions such as the homestead.
- **§9.3034 — Notice of Exemption Application Requirement** (Subch. H).

The app's `cf-tacrule` node previously cited "34 TAC Ch. 9, Subch. H" generically; the precise homestead-form rule is **§9.415**.

## 4. Comptroller forms affected

- **Form 50-114 — Application for Residence Homestead Exemption** (comptroller.texas.gov/forms/50-114.pdf).
- **Form 50-114-A — Residence Homestead Exemption Affidavits** (comptroller.texas.gov/forms/50-114-a.pdf).

## Unverifiable / caveats

- Nothing material was left unverified. Ballotpedia's page failed one fetch path (Exa) but scraped cleanly via Firecrawl; the vote totals were confirmed against the LRL Texas certified-amendment source it cites.
- Edgewood III's 826 S.W.2d 489 pinpoint holding is quoted from the Neeley opinion (the Court quoting itself) plus the St. Mary's "Texas School Finance Litigation Saga" reporter list; I did not open a standalone full text of the 1992 opinion, but two independent sources carry the citation and holding.
