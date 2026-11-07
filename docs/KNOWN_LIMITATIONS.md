# Known limitations

Recorded so that they are not forgotten. Each entry says what was observed, where, and what is *not* being done about it yet.

## KL-1: Exact provisions can be cut while unrelated chunks are included (Phase 1)

**Where:** `rag/retrieval.py`, `assemble_context` (pass 1 versus pass 2), setting `EXACT_BUDGET_FRACTION` (default 0.6).

**What happens:** when a question names a provision (for example "Section 2 of the Consumer Protection Act"), that provision
may use at most 60% of the 10,000-character budget. The remaining 40% is given to semantic matches. If the named provision
is long, its later parts are excluded while semantically ranked but unrelated chunks stay in.

**Evidence (real chunk text, saved baseline hits, no live run):**
* L3, CP Act section 2 (13 parts, 25,076 characters): parts 1-3 included, parts 4-13 excluded as `budget`;
  CP sections 1, 18 and 39 (about 3.7k characters, unrelated to the question) included.
* L2, BNS section 2 (7 parts, 13,151 characters): parts 1-3 included, parts 4-7 excluded; BNSS 2 part 3 and CP 2 part 6 included.

**Not done:** the ratio and the "suppress semantic extras when an exact provision is truncated" option are left as they are.
Options when this is revisited: raise `EXACT_BUDGET_FRACTION` (for example to 0.8), or skip semantic provisions entirely when an
exact provision is truncated. Either needs the full 43-case comparison because context size and latency change.

**Mitigation in place:** Phase 2 tells the model which provisions are partial and adds a deterministic note to the answer, so a
truncated list is not presented as complete. This does not restore the missing text.

## Other Phase 1 observations (unchanged)
* The rank of BNSS 478 in the M2 baseline is unknown (only the top 6 hits were saved); the M2 simulation assumes 7th.
* Context size grows 22-70% against the baseline; latency has not been measured.
* `context_report.truncated_provisions` also lists partly shown semantic provisions, which is noisy.

---

# Final MVP hardening: what is still not solved (2026-11-07)

Evidence: `docs/HARDENING_LIVE.json/.md` (19 live cases), `docs/hardening_scratch/` (M2 repeat trials), `docs/HARDENING_REPORT.md`.
None of this was established by automated tests alone, and passing tests do **not** show that answers are legally accurate.

## KL-2: M2 (bailable vs non-bailable) is still unreliable
* The model still produces unsupported or wrong statements about it. In the latest live run: "bailable offences ... without such restrictions" (no source says so),
  an offence "punishable with imprisonment of three years or less" is bailable (misreads IT Act 77B; flagged as a threshold warning),
  and malformed markers `[4(c)]`, `[1(3)]` (the prompt now forbids them; the model still wrote them; they are flagged, not prevented).
* The 478(1) "shall" -> "may" error is **intermittent**: 1 of 3 identical runs on the old prompt, 0 of 3 on the new one, and 478(1) was not mentioned at all in the latest live run.
  Three runs cannot show the prompt fixed it. `modal_changed` flags it when it happens and the answer reuses the source's wording.
* Undetectable by the checks (pinned as strict xfail tests): a negative claim whose words all occur in the sources ("no requirement of a bond"), and a dropped
  condition inside a paraphrase. Only entailment checking (a second model pass, out of scope) could catch these.

## KL-3: `modal_changed` is narrow and was tuned on the data it was measured on
* It only compares the wording after a modal that appears in both answer and cited source, and only for obligation/prohibition -> "may" and "may" -> "shall/must".
  Negated forms are not judged ("No person shall be detained" vs "shall not be detained" would false-alarm). A paraphrase is neither flagged nor caught.
* It was narrowed after the first version raised 2 false alarms out of 4 flags on the 41 saved live answers. Its false-positive rate on unseen answers is unknown.

## KL-4: "does not exist" detection is phrase-based
* `unsupported_existence_claim` recognises a fixed set of phrases ("no such section", "does not exist", "does not correspond to any section", ...). Other wordings get through.
  The prompt rule is the first line of defence; the latest live U4 answer complied (no existence claim, no note).
* The answer text is not rewritten when the check fires; the user sees a "Verification error" note.

## KL-5: truncation
* A cut-off is now detected from Ollama's `done_reason == "length"` (or a stream that ends without `done`) and reported with an "Incomplete answer" note plus `generation.truncated`.
  The partial text is kept, not hidden. Latest live run: 1 of 19 cases still hit the 700-token cap (L3, the 13-part Consumer Protection Act s.2 definitions); the other 6 formerly truncated answers finished by themselves.
* The cap stayed 700. Making answers shorter (prompt rule 13) was preferred to raising it; shorter answers cost accuracy in list questions (e.g. L2 now names definitions but gives fewer of them).
* Interrupted streams (Ollama stopping or the connection dropping) are treated as incomplete, but an Ollama *error* still raises as before.

## KL-6: verification noise and the new prompt
* The prompt grew from 2,533 to 3,529 characters (about 250 more prompt tokens).
* `weak_support` still produces notes on explanatory sentences (6 of 19 re-run answers carried notes, same as before).
* Quote extraction used to mis-pair quote marks around short defined terms (6 false "quotation not found" errors in L2). Fixed and tested; the saved
  `HARDENING_LIVE.json` was produced *before* that fix, so its L2 verification block still shows those 6 errors (re-verified offline: none).
* Schedule tables list section numbers bare ("263(b)"); numbers written that way in schedule chunks are now accepted (was a false "unsupported section" error in M2).

## Carried over, not touched in this task
Chunk contamination (running headers / Gazette fragments inside chunks, failing verbatim checks E2/E7/S5/S9), exact-provision priority (KL-1), S11 retrieval miss,
refusals returning status `answered` (E8, U1-U3), the first-schedule table text quality, and latency (about 1.7x the baseline median, driven by longer prompts and answers).

## KL-7: follow-up rewriting (found by a user, 2026-11-07) and broad "overview" questions
* The follow-up rewriter once turned a complete question ("Give me an overview of the BNSS, 2023") into a false statement about the IT Act, using an
  earlier answer, and the assistant then "refuted" it. Fixed: a message is rewritten only if it looks like a follow-up (short, or "it/that/what about..."),
  the rewriter sees only the user's earlier questions (never earlier answers), and an implausibly long rewrite is discarded. The heuristic can miss a
  follow-up that has no reference word and is longer than five words (it is then answered as typed, which is the safe failure). Verified on the
  reported conversation replayed against a copy of the chat database; not re-evaluated across the 43 cases.
* A broad "overview of an Act" question is only answered from a handful of sections (preamble-type provisions); the assistant says it cannot describe the
  Act's overall structure. In the replay it also abbreviated the BNSS as "BNS" and called BNSS 396 "the BNS": the model confuses the two similarly named
  Acts. Nothing checks Act abbreviations.
