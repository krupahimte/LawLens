"""Compare two saved RAG reports (baseline vs a later run) and write a markdown summary. Read-only on both reports.

Usage:  python compare_reports.py docs/test_report.json docs/PHASE2_LIVE.json docs/PHASE2_LIVE_COMPARISON.md
"""
import json
import re
import statistics as st
import sys

import config
from rag import guardrails

base_path, new_path, out_path = sys.argv[1:4]
base = {r["case"]["id"]: r for r in json.load(open(base_path, encoding="utf-8"))}
new = {r["case"]["id"]: r for r in json.load(open(new_path, encoding="utf-8"))}
ids = [i for i in base if i in new]

chunks = {}
for d in ("bns_en", "bnss_en", "bsa_en", "constitution_en", "cp_en", "it_en"):
    for line in open(config.PROCESSED_DIR / f"{d}.jsonl", encoding="utf-8"):
        c = json.loads(line)
        chunks[c["chunk_id"]] = c

ok = lambda r: all(r["checks"].values())
L = []
P = L.append
P(f"# Baseline vs live run ({len(ids)} cases in common)\n")
P(f"Baseline: `{base_path}` (Phase 0). Live: `{new_path}` (Phase 1 context assembly + Phase 2 prompt and verification). Same 43 questions and checks.\n")

# ---------------------------------------------------------------- 1. pass counts
b_pass, n_pass = sum(ok(base[i]) for i in ids), sum(ok(new[i]) for i in ids)
P(f"## 1. Automatic checks\n\nAll checks passed: **baseline {b_pass}/{len(ids)}**, **live {n_pass}/{len(ids)}**.\n")
P("| Case | Baseline failing checks | Live failing checks | Change |\n|---|---|---|---|")
for i in ids:
    bf = [k for k, v in base[i]["checks"].items() if not v]
    nf = [k for k, v in new[i]["checks"].items() if not v]
    if bf or nf:
        change = "fixed" if bf and not nf else "REGRESSION" if nf and not bf else "same" if set(bf) == set(nf) else "changed"
        P(f"| {i} | {', '.join(bf) or '-'} | {', '.join(nf) or '-'} | {change} |")

# ---------------------------------------------------------------- 2. latency
def totals(rep, key="total_s"):
    return [rep[i]["timings"].get(key) for i in ids if rep[i]["status"] == "answered" and rep[i]["timings"].get(key)]

def stats(v):
    v = sorted(v)
    return f"median {st.median(v):.1f}s, mean {st.mean(v):.1f}s, p90 {v[int(0.9 * (len(v) - 1))]:.1f}s, max {v[-1]:.1f}s (n={len(v)})"

P("\n## 2. Latency (answered cases)\n")
for label, key in (("total", "total_s"), ("generation", "generation_s"), ("retrieval", "retrieval_s")):
    P(f"* {label}: baseline {stats(totals(base, key))}\n  * live {stats(totals(new, key))}")
both = [i for i in ids if base[i]["status"] == "answered" and new[i]["status"] == "answered" and base[i]["timings"].get("total_s") and new[i]["timings"].get("total_s")]
ratios = [new[i]["timings"]["total_s"] / base[i]["timings"]["total_s"] for i in both]
P(f"* per-case ratio live/baseline: median {st.median(ratios):.2f}x, range {min(ratios):.2f}x - {max(ratios):.2f}x over {len(both)} cases")
P("\n(E1, the first case of a run, also pays model-loading time.)")

# ---------------------------------------------------------------- 3. context size
def base_chars(r):
    return sum(len(chunks[s["chunk_id"]]["text"]) for s in r["sources"] if s["chunk_id"] in chunks)

P("\n## 3. Context given to the model (characters)\n")
pairs = [(base_chars(base[i]), new[i]["context_report"]["used_chars"]) for i in ids if base[i]["status"] == "answered" and new[i]["status"] == "answered" and new[i].get("context_report")]
if pairs:
    P(f"* baseline mean {st.mean(p[0] for p in pairs):.0f}, live mean {st.mean(p[1] for p in pairs):.0f}; live max {max(p[1] for p in pairs)} (budget {config.CONTEXT_CHAR_BUDGET})")
    P(f"* mean number of sources: baseline {st.mean(len(base[i]['sources']) for i in ids if base[i]['status']=='answered'):.1f}, live {st.mean(len(new[i]['sources']) for i in ids if new[i]['status']=='answered'):.1f}")

# ---------------------------------------------------------------- 4. M2
P("\n## 4. M2 (bailable vs non-bailable): the case that motivated Phase 2\n")
KNOWN_ERRORS = {
    "reverses BNSS 480(1)(ii) ('may only be released ... or if the offence is cognizable ...')": r"only be released[^.]*\bor if\b[^.]*cognizable",
    "misreads IT 77B ('three years or more ... bailable')": r"three years or more[^.]*bailable|bailable[^.]*three years or more",
    "uses the Code of Criminal Procedure from memory": r"as per the provisions of the code of criminal procedure|under the code of criminal procedure",
}
for label, rep in (("baseline", base), ("live", new)):
    if "M2" not in rep:
        continue
    r = rep["M2"]
    srcs = [s["chunk_id"] for s in r["sources"]]
    hits = [k for k, pat in KNOWN_ERRORS.items() if re.search(pat, r["answer"], re.I | re.S)]
    P(f"**{label}**: sources {srcs}")
    P(f"* BNSS 478 among sources: {'bnss_en:478:1' in srcs}; all three 480 parts: {all(f'bnss_en:480:{p}' in srcs for p in (1, 2, 3))}")
    P(f"* known errors still present (regex on the answer): {hits or 'none of the three'}")
    if r.get("top20"):
        rank = next((n for n, h in enumerate(r["top20"], 1) if h["chunk_id"] == "bnss_en:478:1"), None)
        P(f"* rank of bnss_en:478:1 in the retrieved list: {rank or 'not in top 20'}")
    P(f"* notes: {r['notes'] or 'none'}")
    if r.get("verification"):
        v = r["verification"]
        P(f"* verification: errors {[e['type'] for e in v['errors']]}, warnings {[w['type'] for w in v['warnings']]}, quotes {[(q['status']) for q in v.get('quotes', [])]}")
    P("")
if "M2" in new:
    P("Live M2 answer:\n")
    P("\n".join("> " + ln for ln in new["M2"]["answer"].splitlines()))

# ---------------------------------------------------------------- 5. quotations
def quotes_in(answer):
    return guardrails.extract_quotes(answer)

P("\n## 5. Quotation behaviour (the prompt now asks for exact quotes of conditions and thresholds)\n")
for label, rep in (("baseline", base), ("live", new)):
    ans = [i for i in ids if rep[i]["status"] == "answered" and not guardrails.is_refusal(rep[i]["answer"])]
    withq = [i for i in ans if quotes_in(rep[i]["answer"])]
    P(f"* {label}: {len(withq)} of {len(ans)} substantive answers contain at least one quotation of 4+ words")
if any(new[i].get("verification") for i in ids):
    statuses = [q["status"] for i in ids if new[i].get("verification") for q in new[i]["verification"].get("quotes", [])]
    P(f"* live quotation checks by result: { {s: statuses.count(s) for s in sorted(set(statuses))} or 'no quotations' }")

# ---------------------------------------------------------------- 6. refusals
P("\n## 6. Refusals\n")
for label, rep in (("baseline", base), ("live", new)):
    ref = [i for i in ids if rep[i]["status"] == "answered" and guardrails.is_refusal(rep[i]["answer"])]
    with_c = [i for i in ref if re.search(r"\[\d\]", rep[i]["answer"])]
    P(f"* {label}: {len(ref)} refusals {ref}; {len(with_c)} still carry citation markers {with_c}")
bad_starts = [i for i in ids if new[i]["status"] == "answered" and guardrails.is_refusal(new[i]["answer"]) and not new[i]["answer"].startswith("The available documents do not answer")]
P(f"* live refusals not beginning with the required phrase: {bad_starts or 'none'}")

# ---------------------------------------------------------------- 7. verification output
P("\n## 7. Verification output on the live answers\n")
agg = {"errors": {}, "warnings": {}}
noted = []
for i in ids:
    v = new[i].get("verification")
    if not v:
        continue
    for kind in ("errors", "warnings"):
        for it in v[kind]:
            agg[kind].setdefault(it["type"], []).append(i)
    if new[i]["notes"]:
        noted.append(i)
for kind in ("errors", "warnings"):
    P(f"* {kind}: " + ("; ".join(f"{t} in {sorted(set(c))}" for t, c in agg[kind].items()) or "none"))
answered = [i for i in ids if new[i]["status"] == "answered"]
P(f"* answers carrying at least one note: {len(noted)} of {len(answered)}")
errs = [(i, e) for i in ids if new[i].get("verification") for e in new[i]["verification"]["errors"]]
for i, e in errs:
    P(f"  * [{i}] ERROR {e['type']}: {e['detail']} | {(e.get('sentence') or e.get('quote') or '')[:150]}")

# ---------------------------------------------------------------- 8. partial provisions
P("\n## 8. Long provisions named by the question (partial handling)\n")
for i in ("L2", "L3"):
    if i in new and new[i].get("context_report"):
        cr = new[i]["context_report"]
        P(f"* {i}: truncated {cr['truncated_provisions']}")
        P(f"  * partial note shown: {any('incomplete' in n for n in new[i]['notes'])}; answer admits it is partial: {bool(re.search(r'partial|not (?:a )?complete|incomplete|part of|include', new[i]['answer'], re.I))}")
        P(f"  * answer ends: `{new[i]['answer'].rstrip()[-120:]!r}`")

# ---------------------------------------------------------------- 9. mid-sentence endings, lengths
P("\n## 9. Answer length and endings\n")
def ends_open(a):
    a = a.rstrip()
    return bool(a) and a[-1] not in ".!?)]\"'”"
for label, rep in (("baseline", base), ("live", new)):
    lens = [len(rep[i]["answer"]) for i in ids if rep[i]["status"] == "answered"]
    P(f"* {label}: median {st.median(lens):.0f} characters, longest {max(lens)}; answers ending mid-sentence: {[i for i in ids if rep[i]['status']=='answered' and ends_open(rep[i]['answer'])]}")

# ---------------------------------------------------------------- 10. per-case answers that changed a lot
P("\n## 10. Status changes\n")
chg = [(i, base[i]["status"], new[i]["status"]) for i in ids if base[i]["status"] != new[i]["status"]]
P("* " + (", ".join(f"{i}: {a} -> {b}" for i, a, b in chg) if chg else "no case changed status"))

open(out_path, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L)[:200], "...\nwritten", out_path)
