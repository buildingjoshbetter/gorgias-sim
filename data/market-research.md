# Market research — why pre-vote policy-impact simulation wins (F2)

Date: 2026-07-03. Researcher: F2. Companion data: `market-research.json`.

Product being justified: type a proposed law, and before a vote see every statute
touched, every conflict created, every agency triggered, every dollar moved, every
county affected, and litigation exposure. The status quo produces a narrow cost
estimate *after* filing, or pays consultants six figures to read the code by hand.

Verification convention: **[deep-fetch]** = pulled from the full page. **[search-result]**
= from the fetched search result (title+snippet) for that URL; re-open before publishing
if exact precision matters. No numbers invented.

---

## 1. The cost of bad legislation (sourced)

**Texas HB2 — the flagship example.** [deep-fetch]
The U.S. Supreme Court struck down Texas's HB2 abortion-clinic restrictions 5-3 in
*Whole Woman's Health v. Hellerstedt* (June 2016) as unconstitutional. Texas spent
almost three years defending it. The state's own AG-office defense cost **$768,722**;
a related earlier case (*Planned Parenthood v. Abbott*) cost another **$311,355**; and
the prevailing plaintiffs then filed to recover about **$4.5 million** in attorney's
fees the state could be ordered to pay.
Sources: Texas Tribune, Texas Monthly, San Antonio Report.

**Unfunded consequences move real money.** [search-result]
A Congressional Research Service review of the Unfunded Mandates Reform Act cites that
Congress shifted **at least $131 billion** in costs onto states over a five-year window;
hearing testimony documents **Ohio absorbing ~$1.7 billion** in unfunded mandates
1992-1995. This is the "every dollar moved" axis, unmodeled at passage.
Sources: congress.gov CRS R40957; GovInfo hearing record.

**Losing is not free — fee-shifting.** [search-result]
A Washington court ordered the state AG to pay **$4.3 million** in fees and costs after
an unsuccessful action against a thrift-store chain. Second concrete data point that a
bad legal theory ends with the government paying the winner's lawyers.
Source: Consumer Financial Services Law Monitor.

**The market leader's own framing.** [deep-fetch]
Vulcan Technologies (YC S25, Austin) states agencies "spend millions of dollars and
years hiring consultancies and law firms just to double-check that their proposed
implementation of laws and executive orders is actually lawful," and that each step
"wastes taxpayer dollars," because a change that doesn't cohere with existing state law,
federal law, and case law "risks litigation and the loss of their budgets."
Sources: YC company page; Fondo launch writeup.

---

## 2. The status-quo tooling gap

**What Texas actually uses: the LBB fiscal note.** [search-result]
State statute requires the Legislative Budget Board to prepare a fiscal note to
accompany a bill *as it moves through* the process (after filing/referral). The LBB has
**up to 15 days** after receiving a bill to produce it. By definition it is only "a
written estimate of the costs, savings, revenue gain, or revenue loss." It does **not**
map statutory conflicts, constitutionality, agency triggers, county-level effects, or
litigation exposure. Late, narrow, slow, human-produced.
Sources: lbb.texas.gov fiscal-note pages and committee/agency guides.

**The manual-review cost anchor (Vulcan / Virginia).** [deep-fetch]
Vulcan's Virginia engagement was a **$150,000, three-month pilot** (May 1 - Aug 1, 2025)
that stood in for a **manual, line-by-line human review of ~24 million words** of
regulation. Vulcan's CEO called Virginia's by-hand review "the gold standard" — the
alternative to software is people reading the entire code by hand. A five-figure
software line replacing what consultancies bill six-to-seven for is consistent with the
"~10% of legacy consultancy quotes" framing.
Source: Reason, 2025-07-23.

**The upside is measured in billions.** [deep-fetch]
Virginia's regulatory-reduction effort (now AI-powered) streamlined **26.8%** of
regulatory requirements and, per the governor's office, saves citizens **over $1.2
billion per year** — roughly **$700 million** of it from housing-code changes that shave
about **$24,000** off a new house. Getting impact right is worth billions in one
mid-size state.
Sources: Reason; GovTech.

**Consulting is the expensive, unpopular incumbent.** [search-result]
A GSA Inspector General audit found improper pricing on a single McKinsey contract that
"may cost the United States an estimated **$69 million**." The budget line the product
displaces is large and already politically toxic.
Sources: GSA IG audit; ProMarket.

---

## 3. Market size anchors (name / year / number)

- **US government tech**: 12.3% of $2.9 trillion total US tech spend in 2026 — Forrester, 2026. [search-result]
- **AI in government & public services**: $19.7B in 2025, ~19.4% CAGR through 2035 — GM Insights. A separate house (Future Market Insights) says $26.4B in 2025. [search-result]
- **Global govtech**: $825.49B in 2026 → $3,090.93B by 2035 — Business Research Insights. [search-result]
- **State + local split**: ~$78B from states, ~$75B from city/county — VistaPoint Advisors, GovTech Quarterly Q3 2025. [search-result]
- **Legal AI**: $1.45B (2024) → $3.90B (2030) at 17.3% CAGR — Grand View Research; LegalTech-AI segment $2.82B (2025) → $3.7B (2026) at 31.4% CAGR — Research and Markets. [search-result]
- **Legal technology (total)**: $33.97B (2025) → $77.93B (2034) — Fortune Business Insights. [search-result]

Ranges where sources disagree are shown; each number is attributed to its house.

---

## 4. Buyer map (one line each)

- **Legislative councils / legislative counsel** — draft and legally vet bills by hand today; the sim is a force-multiplier on their core job.
- **Fiscal/budget analysts (Texas LBB)** — already owe a fiscal note; the product does dollars-moved faster and adds the axes the note omits.
- **Attorney General / solicitor offices** — they defend enacted statutes and eat litigation cost and fee awards; pre-vote litigation scoring is priceable loss-avoidance.
- **Government efficiency / regulatory offices (Texas TREO, Virginia ORM)** — chartered to cut red tape and cost; Virginia already put this AI category into an executive order.
- **Lobbying / advocacy / trade associations** — want a bill's full footprint before spending to push or kill it; commercial WTP, no procurement cycle.
- **Litigation / public-interest shops** — a conflict/precedent map is offense: find the constitutionally weakest provisions to challenge.
- **Municipal-bond insurers & rating agencies (hypothesis)** — a law that moves dollars/triggers mandates changes issuer fiscal health; novel underwriting input. Unvalidated.

---

## 5. Landing-page copy blocks (stat/claim, each with source)

1. **$768,722 to lose.** Texas spent nearly three years and $768,722 defending HB2 — then the Supreme Court struck it down and the winners billed $4.5 million in fees. *(Texas Tribune / Texas Monthly)*
2. **The fiscal note comes too late.** Texas law only requires a cost estimate *after* a bill is filed — and it never checks whether the bill is even legal. *(Legislative Budget Board)*
3. **$150,000 replaced reading 24 million words by hand.** Virginia's AI regulatory review cost a fraction of the manual, line-by-line review it replaced. *(Reason, 2025)*
4. **$1.2 billion a year.** Getting regulatory impact right saved Virginians over $1.2 billion annually — $700 million from housing rules alone. *(Reason / GovTech)*
5. **$131 billion, shifted quietly.** Congress moved at least $131 billion in costs onto states in five years. Nobody modeled it before the vote. *(Congressional Research Service)*
6. **Agencies pay millions to ask "is this legal?"** They "spend millions of dollars and years hiring consultancies and law firms" just to check a rule is lawful. *(Vulcan Technologies, YC)*
7. **$69 million overcharge — for one consulting contract.** The incumbent you're replacing is expensive and already under audit. *(GSA Inspector General)*
8. **A $2.9 trillion tech budget, 12.3% of it government.** This isn't a niche. *(Forrester, 2026)*
9. **Fee-shifting cuts both ways.** Washington's AG was ordered to pay $4.3 million after losing. A bad legal theory has a price. *(Consumer Financial Services Law Monitor)*
10. **See the blast radius before the vote.** Every statute touched, every conflict, every agency, every dollar, every county, every lawsuit waiting to happen.

### Hero-line candidates
1. See the whole blast radius of a law — before it's a law.
2. Every statute it touches. Every dollar it moves. Every lawsuit it invites. Before the vote.
3. The fiscal note tells you what a bill costs. We tell you what it breaks.
4. Simulate the law before you pass the law.
5. Stop finding out in court.

### Why now
The category just got validated at the state level: in 2025 Virginia signed AI
regulatory review into an executive order and Texas stood up a public AI legal
explorer (SAM/TREO). The market leader (Vulcan, YC S25) proved governments will pay
for AI that reads the entire legal corpus — but its wedge is redlining rules *after*
they're proposed. The open lane is the *pre-vote* simulation: showing a legislator, in
seconds, the full footprint of a bill while it can still be changed. The cost of not
doing this is on the public record — years-long defenses, seven-figure fee awards, and
billions in unmodeled cost shifts — and the govtech and legal-AI budgets funding the
fix are measured in the tens to hundreds of billions and growing double digits a year.

---

## 6. Strongest 5 facts & what could not be substantiated

**Strongest 5 (all deep-fetched or authoritative):**
1. Texas HB2: ~3 years defended, $768,722 own cost + $311,355 prior case, $4.5M fee request, struck 5-3. *(deep-fetch, 3 sources)*
2. Vulcan/Virginia: $150,000 three-month pilot replacing manual review of ~24M words; "gold standard" quote. *(deep-fetch, Reason)*
3. Virginia savings: 26.8% of requirements streamlined, >$1.2B/yr, $700M from housing, $24K/house. *(deep-fetch, Reason + GovTech)*
4. Vulcan's own problem statement: agencies "spend millions of dollars and years" checking legality. *(deep-fetch, YC + Fondo)*
5. Unfunded mandates: at least $131B shifted to states over five years (CRS). *(search-result, CRS)*

**Could NOT fully substantiate / caveats:**
- **The specific "Vulcan Virginia deal ran at ~10% of legacy consultancy quotes" claim** — I could not find a source stating the legacy consultancy quote it was compared against. What I *can* corroborate: the deal was $150K for 3 months, it replaced manual line-by-line review, and government regulatory-consulting contracts routinely run into the millions-to-hundreds-of-millions (Deloitte federal contracts cited at $200M+ and $372M in aggregate; McKinsey single-contract $69M overcharge). The "10%" ratio is plausible but not directly sourced — present it as an estimate, not a cited fact.
- **Municipal-bond insurer / rating-agency buyer** — logical but I found no evidence any such buyer purchases policy-impact tooling today. Flagged as hypothesis.
- **Market-size figures** are from research-firm search results, not deep-fetched reports, and the firms disagree (e.g., AI-in-government at $19.7B vs $26.4B for 2025). Use ranges and attribute by house; re-open the specific report before quoting a single number as definitive.
- **A clean, Texas-specific total for "money wasted on struck-down statutes"** does not exist as a single published figure; the case is best made by stacking named examples (HB2, unfunded mandates, fee awards) rather than one aggregate number.
