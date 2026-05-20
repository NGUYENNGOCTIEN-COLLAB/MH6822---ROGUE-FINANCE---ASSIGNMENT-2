# Module 4: Classification Analysis of Prediction-Market and Event Contracts

**MH6822, Homework 2**
**Asset class:** EventContract / BinaryEventContract
**Trades analysed:** T026 (Bundestagswahl), T027 (US CPI / Polymarket),
T028 (ESMA AI Act), T033 (MAS NEER, team-designed)

---

## 4A. Economic Function Test

The assignment asks three specific questions of each event contract and
requires an explicit answer to all three, per trade, before concluding
whether the instrument performs hedging or price discovery analogous to
a recognised derivative. The three questions are:

1. Is there an identifiable economic actor with a measurable
   contractual exposure to the referenced event?
2. If the contract were freely tradeable, would it let that actor
   manage that exposure?
3. Does the contract provide price discovery beyond existing sources?

The actor identities below are read directly from the
`reporting_counterparty_type` and `underlying_economic_exposure` fields
of the trade records.

### T026: Kalshi binary on the 2025 Bundestagswahl

**Question 1.** Yes. The reporting counterparty is a corporate treasury
(`reporting_counterparty_type = CorporateTreasury`, LEI
`5493001KJTIIGC8Y1R12`) at a German renewable-energy developer. The
`underlying_economic_exposure` field states the firm's renewable-subsidy
regime is materially affected by the election outcome. A Bundestag
majority that scraps EEG subsidy continuity impairs a project-finance
pipeline; a Green-led coalition expands it. The exposure is measurable:
the contract pays USD 1.00 per contract on 50,000 contracts if the
adverse political state occurs, sized to the subsidy at risk.

**Question 2.** Yes. There is no conventional rates, FX or credit
derivative written on German renewable-subsidy regime continuity. If the
Kalshi binary were freely tradeable in size, it is the only instrument
that pays out precisely in the disaster scenario, so it lets the
treasury transfer a real-world political risk it cannot otherwise hedge.

**Question 3.** Partially. The contract price (entry price 0.42) is a
market-implied probability of the political outcome that aggregates more
information than any single poll, but polling and bookmaker odds already
exist for headline elections, so the incremental price-discovery value
is real but not unique.

**Conclusion.** T026 performs a genuine hedging function analogous to a
recognised derivative. It clears legs 1 and 2 cleanly; leg 3 is
supportive but not decisive.

### T027: Polymarket binary on US Q3 2026 CPI > 3.0%

**Question 1.** Yes, but qualified. The reporting counterparty is an EU
asset manager (`reporting_counterparty_type = AssetManager_EU`, LEI
`VGRQXHF3J8VDLUA7XE92`) holding a USD-denominated investment-grade bond
portfolio with inflation sensitivity. The exposure to a US CPI surprise
is real and measurable through the portfolio's duration and carry.

**Question 2.** Yes in principle, but the contract is not the natural
instrument. The manager already has liquid, continuous hedges available
(Treasury futures, inflation swaps). The Polymarket binary is a
discrete-payoff substitute, and the `access_method` field records
`VPN_BYPASS_GGL_BLOCK`, meaning the manager reaches a venue it cannot
legally access from the EU. The `counterparty_exposure_type` field is
`HEDGING_SPECULATIVE_MIXED`, which the record itself flags as mixed
motive.

**Question 3.** Yes. The Polymarket order book produces a tradeable,
real-time probability of the inflation threshold being breached, which
is information not directly available from BLS releases or swap-implied
breakevens at the same granularity.

**Conclusion.** T027 has the form of a hedge but, given a continuous
hedge is available and the access is through a circumvented geoblock,
its economic function is mixed and closest to a wager dressed as a
hedge. It is the trade most exposed to the jurisdictional-arbitrage
problem analysed in 4C.

### T028: Kalshi binary on ESMA AI Act Annex III approval

**Question 1.** Yes. The reporting counterparty is an EU fintech
(`reporting_counterparty_type = FinTechFirm_EU`, LEI
`9695009AXSRNHZE85Y20`) whose credit-scoring product compliance cost is
contingent on whether ESMA approves the Annex III high-risk
classification. The `underlying_economic_exposure` field states the
compliance cost is directly contingent on the decision, an eight-figure
cost shock if the classification lands.

**Question 2.** Yes. There is no conventional derivative on a specific
regulatory-classification decision. The Kalshi binary, if freely
tradeable, is the only instrument that lets the firm transfer the
regulatory-cost risk.

**Question 3.** Yes. The entry price 0.18 is a market-implied
probability of the regulatory decision, information not produced by any
existing instrument or public source.

**Conclusion.** T028 performs a genuine hedging function analogous to a
recognised derivative and clears all three legs.

### T033: Kalshi binary on the MAS NEER policy slope (team-designed)

**Question 1.** Yes. A Singapore corporate with an SGD loan book and USD
revenue (`reporting_counterparty_type = CorporateTreasury_SG`) has a
measurable FX-policy exposure: an unexpected NEER slope adjustment moves
USD/SGD materially overnight.

**Question 2.** Yes. The payoff is economically equivalent to an
at-the-money USD/SGD digital option, but written on a CFTC DCM rather
than the OTC FX-option market. Freely tradeable, it lets the corporate
manage the policy-driven FX exposure.

**Question 3.** Limited. USD/SGD options and forwards already provide
price discovery on the currency; the contract's incremental information
is the market-implied probability of a discrete policy decision.

**Conclusion.** T033 performs a genuine FX-hedging function analogous to
a recognised derivative; it is the cleanest test of whether an APAC
corporate's hedge written on a US DCM should be reportable to MAS, the
CFTC, both, or neither.

The pattern across the four trades: contracts written on regulated DCMs
by entities with an identifiable, balance-sheet exposure to the
underlying event (T026, T028, T033) resemble derivatives in economic
function, not just form, and clear legs 1 and 2 decisively. The single
contract on an unregulated venue accessed through a circumvented
geoblock, by a participant with an available continuous hedge (T027),
fails the spirit of leg 2 and is the case that tempts regulatory
arbitrage.

The market is no longer marginal. The CFTC's March 2026 ANPR notes that
event-contract listings rose from an average of five per year
(2006-2020) to roughly 1,600 in 2025 alone, and that registration
applications for designated contract markets more than doubled in the
year preceding the ANPR. Public reporting on prediction-market growth shows the same direction,
but the ANPR figures are the numbers this report relies on. Whatever
taxonomy is adopted, it must scale.

---

## 4B. Proposed UPI schema extension

The ANNA-DSB UPI taxonomy currently has no AssetClass for event
contracts. Module 2 currently returns `NO_PRODUCT_DEFINITION` for these
trades because no active EventContract template exists. That is correct
given the present taxonomy, but it defeats the purpose of UPI for this
new risk class. The proposal is a minimal schema extension that captures
the classification without forcing event contracts into ill-fitting
existing classes.

```
AssetClass:       EventContract
InstrumentType:   BinaryEventContract | RangeEventContract | ScalarEventContract
UseCase:          PoliticalOutcome | MacroeconomicOutcome
                | RegulatoryDecisionOutcome | MonetaryPolicyOutcome
                | ClimateOutcome | SportsOutcome
DeliveryType:     Cash
```

`DeliveryType` is a designation the existing ANNA-DSB templates carry
(for example a deliverable FX forward versus a non-deliverable forward).
For binary event contracts the value is always `Cash`: the contract
settles in the settlement currency at `ContractSize` per contract on the
YES outcome and zero otherwise. There is no physical delivery analogue,
and an event contract that purported to deliver an asset would fall
outside this class. Making `DeliveryType` an explicit, enumerated
designation rather than an implicit assumption matters for cross-SDR
routing: it lets a repository distinguish a cash-settled event binary
from any future physically-settled event-linked instrument without
re-parsing the payoff description.

Required attributes for `BinaryEventContract`:

| Attribute | Codeset / Type | Source field | Semantic note |
|---|---|---|---|
| EventDescription | string, 16-256 chars | `event_description` | Mandatory; no acronyms without expansion. |
| EventType | enum | `event_type` | Defines the regulatory routing. |
| JurisdictionOfEvent | ISO 3166-1 alpha-2 | `jurisdiction_of_event` | Drives non-CFTC regime applicability. |
| SettlementDate | ISO 8601 date | `settlement_date` | Replaces `maturity_date`; acts as expiry. |
| NumberOfContracts | integer >= 1 | `number_of_contracts` | Replaces NotionalAmount semantics. |
| ContractSize | number > 0 | `contract_size` | In settlement currency. |
| EntryPrice | number, 0 < x < 1 | `entry_price` | Implied probability at execution. |
| **DeliveryType** | enum: Cash | derived / `delivery_type` | **Spec-required designation.** Always `Cash` for binary event contracts; physical delivery is out of class. |
| **HedgingExposureType** | enum: HEDGING / SPECULATIVE / HEDGING_SPECULATIVE_MIXED / MARKET_MAKING | `counterparty_exposure_type` | **New required attribute.** |
| **MustReferenceObservableSource** | boolean (constraint) | derived | **Semantic constraint:** event must be resolvable from a public, named, third-party data source (Bundestag, BLS, ESMA, MAS). Block contracts on unfalsifiable propositions. |
| PlatformType | enum: CFTC_REGULATED_DCM / EU_REGULATED_MTF / MAS_RECOGNISED_VENUE / OFFSHORE_REGULATED / OFFSHORE_UNREGULATED / DECENTRALISED_BLOCKCHAIN | `platform_type` | Drives jurisdictional routing. |

The two starred attributes `DeliveryType` and `HedgingExposureType`
together with the `MustReferenceObservableSource` constraint are the
proposal's substance. `HedgingExposureType` has no analogue in existing
UPI classes because for a conventional swap the hedge-or-speculate
distinction is not actionable and the field is absent. For event
contracts the distinction is actionable: it determines whether the
position should be reported to the SDR with derivatives-like granularity
or routed to the host jurisdiction's gambling authority, as Section 4C
shows. The machine-readable schema is in
`docs/event_contract_upi_template.json`.

---

## 4C. Jurisdictional Arbitrage and Regulatory Design

### (1) The arbitrage: who benefits, who is harmed

The arbitrage is concrete and specific to the actors in T026, T027 and
T028.

**Who benefits.** The EU asset manager in T027. It routes a USD-CPI
inflation position onto offshore Polymarket using the access pattern the
record labels `VPN_BYPASS_GGL_BLOCK`. By doing so it escapes both the
EMIR OTC-derivatives perimeter (the venue is not an EU trading venue and
the instrument is not within the EMIR product scope) and the venue-side
geoblock that is supposed to keep EU residents off Polymarket. The
offshore venue also benefits: it captures order flow that no swap data
repository (SDR) ever sees, with no LEI on its side and no UTI
generated. The position is economically a hedge of a real bond
portfolio, but it lands in a reporting vacuum that is advantageous to
both the manager (no disclosure, no margin) and the venue (unreported
flow).

**Who is harmed.** Regulators lose exposure visibility: there is no
record of the T027 position in any SDR, so aggregate inflation-event
risk concentration is invisible to the CFTC and to ESMA. The German
renewable-energy treasury in T026 and the EU fintech in T028 are harmed
in a different way: their contracts are genuine hedges (Section 4A) but
sit in a taxonomy gap with no UPI, no reportable record, and therefore
no audit trail and no recourse if the venue fails to pay. The honest
hedger is penalised by the same gap the arbitrageur exploits.

### (2) Two of Brandes's five named elements

The lecturer's prompt asks us to pick two of Brandes's five named
elements: **operator neutrality, contract scope limitations, participant
restrictions, market integrity supervision, and position limits and
consumer protection**.[^1] We select **participant restrictions** and
**market integrity supervision** because they map directly onto fields
the engine already carries and onto the gap the T026-T028 actors
exploit.

**Element: Participant restrictions.**

- *Data collected.* For each side of the contract: the counterparty LEI
  (`reporting_counterparty_lei`, `other_counterparty_lei`), the
  counterparty residence implied by `reporting_counterparty_type` and
  the LEI registration jurisdiction, and the venue and access fields
  (`platform`, `platform_type`, `access_method`).
- *Validation logic.* A residence-versus-venue legality cross-check. If
  the counterparty residence and the venue jurisdiction combine into a
  prohibited pairing, the trade is flagged. For example, public Singapore materials frame Polymarket-style activity
  through the Gambling Regulatory Authority and section 20(3) of the
  Gambling Control Act 2022 when a Singapore resident uses an unlawful
  or unlicensed gambling service provider; the official T027 fact
  pattern is an EU resident reaching Polymarket through a circumvented
  geoblock, so the engine treats it as an unauthorised-venue
  participation rather than a MAS OTC-derivatives report. The
  check reads `access_method` and treats `VPN_BYPASS_GGL_BLOCK` as a
  per-se eligibility failure.
- *Reporting infrastructure.* A participant-eligibility flag carried in
  the SDR record alongside the trade, so a repository query can return
  not only the position but whether the participant was eligible to take
  it on that venue.
- *Concrete mechanism.* Detect and flag the `VPN_BYPASS_GGL_BLOCK`
  access pattern, exactly the pattern present in T027, at ingestion, and
  route the flagged trade to the host jurisdiction's eligibility
  authority rather than silently accepting it as reportable derivatives
  data.

**Element: Market integrity supervision.**

- *Data collected.* The position size (`number_of_contracts`,
  `contract_size`, `notional_amount`), the settlement reference and its
  observable source (`event_description`, `settlement_date`), and the
  `event_type` that drives routing.
- *Validation logic.* The `MustReferenceObservableSource` constraint
  drafted in 4B, which requires the event to be resolvable from a
  public, named, third-party source, combined with a position-limit
  check that aggregates a counterparty's exposure per contract.
- *Reporting infrastructure.* CFTC large-trader-style periodic reporting
  to the designated SDR: a recurring submission per counterparty per
  contract that lets the supervisor see concentration build before
  settlement rather than after.
- *Concrete mechanism.* Threshold-triggered reporting. When a
  counterparty's aggregate position in a single event contract exceeds
  USD 1 million per counterparty per contract per quarter (the figure
  4D proposes for Stage 1), the engine raises a mandatory SDR report
  for that position. T027 at USD 200,000 notional sits below the
  threshold individually but the mechanism is what makes a
  Polymarket-scale book visible once positions aggregate.

### (3) If prediction contracts were brought within EMIR

Three concrete changes would be required.

(i) **ANNA-DSB library.** A new `EventContract` UPI class as proposed in
4B, with the `BinaryEventContract` instrument type, the six use-case
codes, and the `DeliveryType = Cash` designation, so that an EMIR-scope
event contract resolves to a real UPI instead of
`NO_PRODUCT_DEFINITION`.

(ii) **UTI generation rules.** Current UTI rules assume both sides hold
an LEI and that one side's LEI forms the namespace. T027 has no LEI on
the venue side and Polymarket settles to pseudonymous wallets. EMIR
inclusion would need a UTI rule for the pseudonymous-wallet or non-LEI
counterparty case, for example assigning the namespace to the reporting
EU counterparty and recording the wallet identifier in a dedicated
counterparty-reference field rather than as an LEI.

(iii) **SDR infrastructure.** EMIR reporting assumes a trade repository
in the DTCC or ICE Trade Vault sense. Polymarket settles on Polygon and
has no such repository. EMIR inclusion would need a DLT-native venue
equivalence or mutual-recognition mechanism that defines what
"equivalent SDR" means when the settlement record is an on-chain smart
contract, so that an on-chain position can be ingested into the EMIR
reporting fabric without re-keying.

[^1]: The phrasing and five-element list follow the lecturer's Module 4C
wording: operator neutrality, contract scope limitations, participant
restrictions, market integrity supervision, and position limits and
consumer protection. This analysis operationalises two of those named
elements: participant restrictions and market integrity supervision.

---

## 4D. Engine limitations and proposed regulatory response

The engine produced verdicts across CFTC, EMIR and MAS for the full
portfolio. Several trades are classified `CONDITIONAL` (T026, T028,
T033), an honest answer for the present rule set, but the conditional
flag has no operational meaning until the CFTC ANPR (RIN 3038-AF65) is
finalised. While that proceeds, the prediction-market industry continues
to grow: 1,600 listings in 2025 versus roughly five per year through
2020, Polymarket's USD 3.2 billion election market, and Kalshi's
clearinghouse operating without reporting to any CFTC-registered SDR.

The absence of a UPI is itself a systemic-risk indicator: an asset class
that has grown by more than two orders of magnitude in five years and
still has no product identifier cannot be aggregated, position-limited
or stress-tested by any supervisor, so the gap is not a cosmetic
taxonomy omission but a measurement blind spot.

The recommended regulatory response is a phased extension. Stage 1
(0-12 months): the CFTC clarifies that DCM-listed event contracts above
a notional threshold (proposed: USD 1 million per counterparty per
contract per quarter) are reportable to a designated SDR using a
provisional UPI. Stage 2 (12-24 months): ANNA-DSB publishes the
EventContract asset class in the production UPI library and ISDA
proposes a CDE field addition for HedgingExposureType. Stage 3
(24-36 months): EMIR Refit and MAS SF(RDC)R extend their perimeters to
event contracts where the reporting counterparty is an EU or Singapore
resident regardless of venue, paired with explicit memoranda of
understanding between MAS, ESMA and the relevant gambling authorities on
the boundary between financial reporting and gambling enforcement to
prevent the dual-classification problem T027 illustrates.

If advising the CFTC on ANPR 91 FR 12516, the two changes to prioritise
are, first, adding the `EventContract` UPI class to the ANNA-DSB library
with the `DeliveryType = Cash` and `HedgingExposureType` designations so
that DCM-listed event contracts carry a real product identifier, and
second, mandating threshold-triggered SDR data submission for those
contracts (the USD 1 million per counterparty per contract per quarter
trigger) so that the supervisor gains aggregate position visibility
before settlement. These two together close the measurement gap without
waiting for the slower EMIR or MAS perimeter extensions.

The engine is built so the Stage-1 transition requires only template
files, not code changes. Four proposed templates, one per UseCase, are
included in `docs/proposed_event_contract_templates/`:

- `EventContract.BinaryEventContract.PoliticalOutcome.UPI.V1.json` (T026)
- `EventContract.BinaryEventContract.MacroeconomicOutcome.UPI.V1.json` (T027)
- `EventContract.BinaryEventContract.RegulatoryDecisionOutcome.UPI.V1.json` (T028)
- `EventContract.BinaryEventContract.MonetaryPolicyOutcome.UPI.V1.json` (T033)

Dropping these into
`data/product_definitions/PROD/OTC-Products/UPI/EventContract/` would
flip the four CONDITIONAL / NO_PRODUCT_DEFINITION trades to either
`FOUND` (if the substantive attributes validate) or `INVALID_ATTRIBUTES`
(surfacing whichever new attribute fails), and let the compliance layer
reason about the trade rather than short-circuit on taxonomy absence.
The single consolidated template at
`docs/event_contract_upi_template.json` is retained as the
machine-readable schema-definition exemplar for ANNA-DSB review.

---

## References

- **CFTC Advance Notice of Proposed Rulemaking, "Prediction Markets,"
  RIN 3038-AF65, 91 FR 12516, Federal Register Document No. 2026-05105
  (16 March 2026)**; comment period closed 30 April 2026.
- **CFTC Press Release No. 9194-26**, announcing the prediction-markets
  ANPR, and **CFTC Press Release No. 9193-26**, announcing the Prediction
  Markets Advisory.
- **CFTC Staff Letter No. 26-08, Prediction Markets Advisory**
  (12 March 2026), Division of Market Oversight.
- 17 CFR section 40.11, Review of event contracts based upon certain
  excluded commodities.
- ESMA EMIR Refit Final Report ESMA70-446-389 (April 2024) on the
  reporting ITS.
- **MAS Guidelines SFA 06A-G01 to the Securities and Futures (Reporting
  of Derivatives Contracts) Regulations 2013** (31 May 2024). MAS Notice
  SFA 04-N18 is not used as an OTC derivatives reporting source because
  it governs cross-border arrangements with foreign offices.
- **Singapore Gambling Control Act 2022, section 20(3)**, as referenced
  in Singapore Police Force enforcement materials on gambling with
  unlawful or unlicensed gambling service providers.
- Public reporting on Singapore blocking access to Polymarket under the
  gambling-law perimeter, including Decrypt, "Singapore Blocks Access to
  Polymarket Over Gambling Law" (January 2025).
- German State Treaty on Gambling 2021 (GlueStV 2021), section 4(1)
  licensing requirement, relevant to the T027 EU/VPN access pattern.
- Brandes (2026), "The Unhedgeable State", required reading for
  Module 4.
- ANNA-DSB Product Definition Library, OTC-Products distribution,
  https://github.com/ANNA-DSB/Product-Definitions.
- ISO 23897:2021, Unique Transaction Identifier; ISO 17442:2020, LEI;
  ISO 7064:2003, MOD 97-10 check character system.
