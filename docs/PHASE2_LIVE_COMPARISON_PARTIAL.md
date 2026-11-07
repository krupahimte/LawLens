# Baseline vs live run (22 cases in common)

Baseline: `docs/test_report.json` (Phase 0). Live: `docs/PHASE2_LIVE_part1.json` (Phase 1 context assembly + Phase 2 prompt and verification). Same 43 questions and checks.

## 1. Automatic checks

All checks passed: **baseline 17/22**, **live 9/22**.

| Case | Baseline failing checks | Live failing checks | Change |
|---|---|---|---|
| E2 | - | cited source text verbatim in PDF | REGRESSION |
| E5 | - | has citation markers | REGRESSION |
| E6 | - | answer mentions expected words | REGRESSION |
| E7 | - | cited source text verbatim in PDF | REGRESSION |
| E8 | status | status, has citation markers | changed |
| S4 | - | ran without error | REGRESSION |
| S5 | - | cited source text verbatim in PDF | REGRESSION |
| S6 | cited source text verbatim in PDF | - | fixed |
| S9 | - | cited source text verbatim in PDF | REGRESSION |
| S10 | answer mentions expected words, cited source text verbatim in PDF | answer mentions expected words, cited source text verbatim in PDF | same |
| S11 | expected in retrieval top-10, expected in sources given to model, has citation markers, cited source text verbatim in PDF | expected in retrieval top-10, expected in sources given to model, has citation markers, cited source text verbatim in PDF | same |
| S12 | - | ran without error | REGRESSION |
| S13 | cited source text verbatim in PDF | ran without error | changed |
| S14 | - | ran without error | REGRESSION |

## 2. Latency (answered cases)

* total: baseline median 31.1s, mean 31.2s, p90 40.1s, max 49.8s (n=22)
  * live median 61.9s, mean 68.5s, p90 89.8s, max 152.5s (n=18)
* generation: baseline median 28.9s, mean 29.1s, p90 38.0s, max 47.7s (n=22)
  * live median 59.8s, mean 66.3s, p90 87.7s, max 150.3s (n=18)
* retrieval: baseline median 2.1s, mean 2.1s, p90 2.2s, max 2.2s (n=22)
  * live median 2.2s, mean 2.2s, p90 2.2s, max 2.2s (n=18)
* per-case ratio live/baseline: median 2.19x, range 1.25x - 5.64x over 18 cases

(E1, the first case of a run, also pays model-loading time.)

## 3. Context given to the model (characters)

* baseline mean 4298, live mean 7335; live max 9729 (budget 10000)
* mean number of sources: baseline 4.0, live 6.9

## 4. M2 (bailable vs non-bailable): the case that motivated Phase 2

**baseline**: sources ['bnss_en:480:1', 'bnss_en:2:1', 'it_en:77b:1', 'bnss_en:thefirstschedule:39']
* BNSS 478 among sources: False; all three 480 parts: False
* known errors still present (regex on the answer): ["reverses BNSS 480(1)(ii) ('may only be released ... or if the offence is cognizable ...')", "misreads IT 77B ('three years or more ... bailable')", 'uses the Code of Criminal Procedure from memory']
* notes: none


## 5. Quotation behaviour (the prompt now asks for exact quotes of conditions and thresholds)

* baseline: 0 of 20 substantive answers contain at least one quotation of 4+ words
* live: 2 of 16 substantive answers contain at least one quotation of 4+ words
* live quotation checks by result: {'verified': 2}

## 6. Refusals

* baseline: 2 refusals ['E8', 'S11']; 1 still carry citation markers ['E8']
* live: 2 refusals ['E8', 'S11']; 0 still carry citation markers []
* live refusals not beginning with the required phrase: none

## 7. Verification output on the live answers

* errors: unsupported_section_reference in ['E8']
* warnings: weak_support in ['E2', 'E3', 'S1', 'S5', 'S8']; miscited_claim in ['E4']
* answers carrying at least one note: 7 of 18
  * [E8] ERROR unsupported_section_reference: 999 | All the cited sources cover different sections (e.g., 509, 299, 119, 500, 219), but none mention Section 999.

## 8. Long provisions named by the question (partial handling)


## 9. Answer length and endings

* baseline: median 666 characters, longest 1734; answers ending mid-sentence: []
* live: median 834 characters, longest 3415; answers ending mid-sentence: ['E5']

## 10. Status changes

* S4: answered -> ERROR, S12: answered -> ERROR, S13: answered -> ERROR, S14: answered -> ERROR
