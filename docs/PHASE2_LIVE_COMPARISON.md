# Baseline vs live run (43 cases in common)

Baseline: `docs/test_report.json` (Phase 0). Live: `docs/PHASE2_LIVE_merged.json` (Phase 1 context assembly + Phase 2 prompt and verification). Same 43 questions and checks.

## 1. Automatic checks

All checks passed: **baseline 30/43**, **live 25/43**.

| Case | Baseline failing checks | Live failing checks | Change |
|---|---|---|---|
| E2 | - | cited source text verbatim in PDF | REGRESSION |
| E5 | - | has citation markers | REGRESSION |
| E6 | - | answer mentions expected words | REGRESSION |
| E7 | - | cited source text verbatim in PDF | REGRESSION |
| E8 | status | status, has citation markers | changed |
| S5 | - | cited source text verbatim in PDF | REGRESSION |
| S6 | cited source text verbatim in PDF | - | fixed |
| S9 | - | cited source text verbatim in PDF | REGRESSION |
| S10 | answer mentions expected words, cited source text verbatim in PDF | answer mentions expected words, cited source text verbatim in PDF | same |
| S11 | expected in retrieval top-10, expected in sources given to model, has citation markers, cited source text verbatim in PDF | expected in retrieval top-10, expected in sources given to model, has citation markers, cited source text verbatim in PDF | same |
| S13 | cited source text verbatim in PDF | cited source text verbatim in PDF | same |
| S18 | cited source text verbatim in PDF | cited source text verbatim in PDF | same |
| L3 | cited source text verbatim in PDF | cited source text verbatim in PDF | same |
| M2 | expected in sources given to model | - | fixed |
| U1 | status, has citation markers | status, has citation markers | same |
| U2 | status | status | same |
| U3 | status, cited source text verbatim in PDF | status, cited source text verbatim in PDF | same |
| U5 | - | has citation markers | REGRESSION |
| U6 | no forbidden claims | no forbidden claims, has citation markers | changed |
| U7 | cited source text verbatim in PDF | cited source text verbatim in PDF | same |

## 2. Latency (answered cases)

* total: baseline median 33.9s, mean 36.3s, p90 57.8s, max 73.6s (n=41)
  * live median 67.4s, mean 82.4s, p90 147.4s, max 162.2s (n=41)
* generation: baseline median 31.8s, mean 34.1s, p90 55.6s, max 71.5s (n=41)
  * live median 65.2s, mean 80.3s, p90 145.2s, max 160.0s (n=41)
* retrieval: baseline median 2.1s, mean 2.1s, p90 2.2s, max 2.2s (n=41)
  * live median 2.2s, mean 2.2s, p90 2.2s, max 2.2s (n=41)
* per-case ratio live/baseline: median 2.18x, range 1.11x - 5.64x over 41 cases

(E1, the first case of a run, also pays model-loading time.)

## 3. Context given to the model (characters)

* baseline mean 4410, live mean 7388; live max 9994 (budget 10000)
* mean number of sources: baseline 3.9, live 6.8

## 4. M2 (bailable vs non-bailable): the case that motivated Phase 2

**baseline**: sources ['bnss_en:480:1', 'bnss_en:2:1', 'it_en:77b:1', 'bnss_en:thefirstschedule:39']
* BNSS 478 among sources: False; all three 480 parts: False
* known errors still present (regex on the answer): ["reverses BNSS 480(1)(ii) ('may only be released ... or if the offence is cognizable ...')", "misreads IT 77B ('three years or more ... bailable')", 'uses the Code of Criminal Procedure from memory']
* notes: none

**live**: sources ['bnss_en:480:1', 'bnss_en:480:2', 'bnss_en:480:3', 'bnss_en:2:1', 'it_en:77b:1', 'bnss_en:478:1', 'bnss_en:thefirstschedule:33']
* BNSS 478 among sources: True; all three 480 parts: True
* known errors still present (regex on the answer): ["misreads IT 77B ('three years or more ... bailable')"]
* rank of bnss_en:478:1 in the retrieved list: 9
* notes: ['Check: a statement is cited to a source that matches it only weakly (cited [1]: 0.25; best match [2]).', 'Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.']
* verification: errors [], warnings ['miscited_claim', 'weak_support', 'weak_support'], quotes []

Live M2 answer:

> The difference between bail in bailable and non-bailable offences lies in the availability and conditions of bail, as defined in the Bharatiya Nagarik Suraksha Sanhita, 2023.
> 
> A "bailable offence" is one that is shown as bailable in the First Schedule or made bailable by any other law in force. A "non-bailable offence" means any other offence not specified as bailable [4(c)].
> 
> According to Section 478(1), when a person is not accused of a non-bailable offence, they may be released on bail if they are prepared to give bail, and if they are indigent, they may be discharged on a bond for appearance [6]. However, this provision does not apply to persons accused of non-bailable offences.
> 
> Section 480(1)(ii) states that a person accused of a non-bailable offence shall not be released on bail if the offence is a cognizable offence and the person had been previously convicted of an offence punishable with death, imprisonment for life, or imprisonment for seven years or more, or on two or more occasions of a cognizable offence punishable with imprisonment for three years or more but less than seven years [1].
> 
> Additionally, Section 480(3) imposes conditions on bail for offences punishable with imprisonment extending to seven years or more, or offences under Chapters VI, VII, or XVII of the Bharatiya Nyaya Sanhita, 2023, or abetment, conspiracy, or attempt to commit such offences. These conditions include attendance as per bond conditions, not committing a similar offence, and not making inducements or threats to witnesses or tampering with evidence [1].
> 
> In contrast, for bailable offences, the law allows release on bail without stringent conditions, and the offence is not subject to the restrictions on prior convictions or the requirement of a bond [4(c)].
> 
> The Information Technology Act, 2000, Section 77B, states that offences punishable with imprisonment of three years and above are cognizable and that the offence punishable with imprisonment of three years shall be bailable [5]. However, this does not override the non-bailable nature of offences under the Bharatiya Nagarik Suraksha Sanhita, 2023, as per the First Schedule.
> 
> Thus, the key difference is that bailable offences allow release on bail without stringent conditions or prior conviction checks, while non-bailable offences require strict conditions and are subject to prior conviction thresholds and higher penalties, as per Section 480(1) and the First Schedule [1][4][5].

## 5. Quotation behaviour (the prompt now asks for exact quotes of conditions and thresholds)

* baseline: 0 of 32 substantive answers contain at least one quotation of 4+ words
* live: 6 of 32 substantive answers contain at least one quotation of 4+ words
* live quotation checks by result: {'altered_legal_term': 1, 'not_found': 1, 'verified': 14}

## 6. Refusals

* baseline: 9 refusals ['E8', 'S11', 'U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7']; 7 still carry citation markers ['E8', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7']
* live: 9 refusals ['E8', 'S11', 'U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7']; 4 still carry citation markers ['U2', 'U3', 'U4', 'U7']
* live refusals not beginning with the required phrase: none

## 7. Verification output on the live answers

* errors: unsupported_section_reference in ['E8']; quote_not_found in ['M3']; quote_altered_legal_term in ['M3']
* warnings: weak_support in ['E2', 'E3', 'L1', 'L2', 'M1', 'M2', 'S1', 'S13', 'S5', 'S8']; miscited_claim in ['E4', 'L2', 'M2']; threshold_qualifier_mismatch in ['M1']
* answers carrying at least one note: 14 of 41
  * [E8] ERROR unsupported_section_reference: 999 | All the cited sources cover different sections (e.g., 509, 299, 119, 500, 219), but none mention Section 999.
  * [M3] ERROR quote_not_found: best similarity 0.818 | no person who is arrested shall be denied the right to consult, and to be defended by, a legal practitioner of his choic
  * [M3] ERROR quote_altered_legal_term: changed ['and'] | no such person shall be detained in custody beyond the said period of twenty-four hours without the authority of a magis

## 8. Long provisions named by the question (partial handling)

* L2: truncated [{'provision': 'bns_en:section:2', 'parts_included': [1, 2, 3], 'parts_total': 7, 'exact': True}, {'provision': 'bnss_en:section:2', 'parts_included': [3], 'parts_total': 4, 'exact': False}, {'provision': 'cp_en:section:2', 'parts_included': [6], 'parts_total': 13, 'exact': False}, {'provision': 'bsa_en:section:2', 'parts_included': [6], 'parts_total': 6, 'exact': False}]
  * partial note shown: True; answer admits it is partial: True
  * answer ends: `'rnment or a State Government; [1]  \n(13) "harbour" includes supplying a person with shelter, food, drink, money, clothes'`
* L3: truncated [{'provision': 'cp_en:section:2', 'parts_included': [1, 2, 3], 'parts_total': 13, 'exact': True}, {'provision': 'cp_en:section:18', 'parts_included': [2], 'parts_total': 2, 'exact': False}, {'provision': 'cp_en:section:39', 'parts_included': [1], 'parts_total': 2, 'exact': False}]
  * partial note shown: True; answer admits it is partial: True
  * answer ends: `'unsafe to the public;  \n(vi) the services which are hazardous or likely to be hazardous to life and safety of the public'`

## 9. Answer length and endings

* baseline: median 1008 characters, longest 2472; answers ending mid-sentence: []
* live: median 1335 characters, longest 3427; answers ending mid-sentence: ['E5', 'S12', 'S17', 'L2', 'L3', 'L4', 'M3']

## 10. Status changes

* no case changed status
