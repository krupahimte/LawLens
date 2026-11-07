# Final MVP hardening: live comparison (19 cases)

Baseline `test_report.json` vs previous live `PHASE2_LIVE_merged.json` vs this run `HARDENING_LIVE.json`. Same questions, same collection `indian_law_en`.
Automatic checks are not a measure of legal accuracy.

| Case | total s base/prev/new | answer chars prev -> new | output tokens | prompt tokens | stop reason | failing checks (this run) |
|---|---|---|---|---|---|---|
| E1 | 26.01/62.41/50.69 | 165 -> 165 | 35 | 3145 | stop | - |
| E5 | 49.83/152.46/122.89 | 3415 -> 2333 | 514 | 3199 | stop | - |
| E8 | 24.49/59.26/55.79 | 362 -> 160 | 44 | 3130 | stop | status |
| S2 | 19.27/57.33/57.67 | 1152 -> 1226 | 260 | 2168 | stop | - |
| S12 | 36.9/148.52/95.56 | 3427 -> 2467 | 505 | 3156 | stop | - |
| S17 | 73.57/142.35/114.78 | 3409 -> 2446 | 492 | 3007 | stop | - |
| L2 | 53.02/162.25/115.97 | 2804 -> 1538 | 391 | 3518 | stop | answer mentions expected words |
| L3 | 57.75/152.58/149.32 | 3135 -> 3102 | 700 | 3200 | length | cited source text verbatim in PDF |
| L4 | 67.74/147.36/111.01 | 3251 -> 2319 | 453 | 3142 | stop | - |
| M1 | 42.93/131.93/103.18 | 2281 -> 1513 | 327 | 3446 | stop | - |
| M2 | 67.71/133.88/62.22 | 2464 -> 1927 | 403 | 3441 | stop | no unverified section numbers |
| M3 | 49.45/125.21/78.5 | 3367 -> 1685 | 349 | 2523 | stop | - |
| U1 | 14.94/30.84/31.9 | 285 -> 259 | 44 | 2148 | stop | status |
| U2 | 13.56/15.11/20.67 | 240 -> 485 | 94 | 1298 | stop | status |
| U3 | 25.19/57.71/57.56 | 608 -> 611 | 121 | 2836 | stop | status, cited source text verbatim in PDF |
| U4 | 35.61/43.0/45.49 | 469 -> 487 | 119 | 2342 | stop | - |
| U5 | 31.82/67.36/65.2 | 522 -> 547 | 96 | 3238 | stop | - |
| U6 | 29.34/50.35/49.04 | 375 -> 372 | 89 | 2636 | stop | no forbidden claims |
| U7 | 23.56/39.73/26.59 | 424 -> 276 | 48 | 2217 | stop | cited source text verbatim in PDF |

* baseline: total median 36s, mean 39s, max 74s

* previous live: total median 67s, mean 94s, max 162s

* this run: total median 62s, mean 74s, max 149s

M2 repeat trials (same prompt and sources, offline, 3 runs each): old prompt 478 'may' error 1/3, answers 2,290-2,542 chars; new prompt 0/3, 1,578-1,872 chars, 361-391 output tokens, all `stop`.
Protected files: PDFs, data/processed/*.jsonl, baseline report, ChromaDB vector index files unchanged (SHA-256 before/after). `chroma.sqlite3` and `conversations.sqlite3` changed: the live run appends chat history (206 message rows now) and Chroma updates its own bookkeeping on read.
