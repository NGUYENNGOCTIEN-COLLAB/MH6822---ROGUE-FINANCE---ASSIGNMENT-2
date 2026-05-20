# Regulatory Source Checklist

This checklist documents the source hygiene used by the engine notes and Module 4 analysis.

## Assignment source

- MH6822 Homework 2 assignment page: https://stanleyyong.github.io/MH6822/index_hw2.html
- Official portfolio hash: `adae82e81b9bbcf61cecf2d1541bf238599468a58dea2c2c043df3fcc4bec299` for `trades.json`.

## ANNA-DSB / UPI

- ANNA-DSB Product-Definitions repository: https://github.com/ANNA-DSB/Product-Definitions
- The active repository fixture is deterministic and homework-sized; proposed EventContract templates remain in `docs/proposed_event_contract_templates/` and are not active registered UPI templates.

## CFTC prediction-market materials

- CFTC ANPR, Prediction Markets: RIN 3038-AF65, 91 FR 12516, Federal Register Document No. 2026-05105, 16 March 2026; comment period closed 30 April 2026.
- CFTC Press Release 9194-26: ANPR on prediction markets.
- CFTC Press Release 9193-26 and CFTC Staff Letter No. 26-08: Prediction Markets Advisory.
- Engine usage: these sources support the `CFTC_EVENT_NOTE` and the CFTC `CONDITIONAL` status for Kalshi / CFTC-regulated DCM event contracts T026, T028 and T033.

## Singapore / MAS source correction

- Correct OTC derivatives reporting source: MAS Guidelines SFA 06A-G01 to the Securities and Futures (Reporting of Derivatives Contracts) Regulations 2013, May 2024.
- Wrong source explicitly avoided: MAS Notice SFA 04-N18, which concerns cross-border arrangements with foreign offices and is not the OTC derivatives reporting source.
- Singapore gambling-law framing: Singapore Police Force materials refer to Gambling Control Act 2022 section 20(3) for gambling with unlawful or unlicensed gambling service providers; public reporting described Polymarket access in Singapore as blocked under the gambling-law perimeter.
- Engine usage: these sources support `MAS_EVENT_NOTE`. The engine does not claim MAS made a formal Polymarket jurisdiction decision.

## EU / EMIR framing

- EMIR Refit reporting ITS and ESMA reporting guidance provide the conventional-derivatives field-set model.
- T027 is treated as an EU/offshore/VPN jurisdictional-scope gap under the assignment model; the engine does not force it into EMIR OTC derivatives reporting.

## Brandes / Module 4C

- Module 4C follows the lecturer's exact wording: pick two of Brandes's five named elements — operator neutrality, contract scope limitations, participant restrictions, market integrity supervision, and position limits and consumer protection.
- The report operationalises two elements: participant restrictions and market integrity supervision.
