"""Legal guardrails applied around the language model.

Before generation: is the retrieved evidence good enough to answer at all?
After generation (``verify_answer``): does the answer stay faithful to the sources it was given?

Findings are split into two kinds, and the difference matters:

* ERRORS are deterministic: a citation to a source that does not exist, a quotation that is not in any source
  (or that changes "shall"/"not"/"or" inside the quotation), a section number that no source contains.
* WARNINGS are heuristics measured on the 43-case baseline: a sentence whose words are mostly absent from the sources,
  a statement cited to a source that matches it only weakly, a number whose qualifier ("more than" versus "and above")
  differs from the source. They can be wrong and are worded as invitations to check.
* INFO is bookkeeping (for example a refusal that still carries citation markers).

What this module cannot do: it works on words, not meaning. If an answer restates a prohibition as a permission using
the source's own words (the M2 baseline failure), no word-level check can see it. That needs a second model pass.
"""
import difflib
import re

import config
from rag import catalog
from rag.preprocessing import normalize_unicode

REF_RE = re.compile(r"(?:sections?|articles?|धारा(?:ओं)?|अनुच्छेद)\s+(\d{1,3}[A-Za-z]{0,2})\b", re.IGNORECASE)
EXTRA_NUMBERS_RE = re.compile(r"(?:,|and|और|तथा|or|या)\s*(\d{1,3}[A-Za-z]{0,2})\b")
CITATION_RE = re.compile(r"\[(\d{1,2})\]")
SCHEDULE_ENTRY_RE = re.compile(r"\b(\d{1,3}[A-Za-z]{0,2})\s?\([a-z]{1,2}\)")      # "263(b)" in a schedule table row


def is_relevant(best_distance: float, has_exact_match: bool) -> bool:
    """Enough evidence to answer? An exact section lookup always counts; otherwise use the distance cut-off."""
    return has_exact_match or best_distance <= config.MAX_DISTANCE


# --------------------------------------------------------------------------- text helpers
LEGAL_WORDS = {"not", "no", "nor", "never", "neither", "cannot", "without", "unless", "except",
               "shall", "may", "must", "and", "or"}
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
QUOTE_RE = re.compile(r"[“\"]([^“”\"\n]{8,}?)[”\"]")
_PUNCTUATION_MAP = (("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-"))

REFUSAL_RE = re.compile(
    r"^(?:the )?(?:available |provided )?(?:legal )?(?:documents|sources)[^.]{0,80}?\b(?:do|does) not (?:answer|contain|address|provide|cover|include)\b", re.I)
# A sentence that merely STATES that something is absent ("Section 999 is not mentioned in the sources") must not be
# flagged for mentioning it. This only ever suppresses a flag; it never creates one.
ABSENCE_RE = re.compile(
    r"\b(?:not (?:been )?(?:mentioned|found|present|included|contained|provided|covered|addressed|specified|listed|referred)"
    r"|(?:does|do) not (?:appear|mention|exist|contain|address|refer|specify|answer)"
    r"|no (?:information|mention|reference|record|source)|cannot be (?:confirmed|determined|verified|found)"
    r"|none of the (?:provided )?sources|(?:is|are) not in|nothing (?:in|about)"
    r"|none (?:of [^.]{0,50}?)?(?:mention|contain|include|address|refer|cover|state|specify|provide)s?)\b", re.I)

# "Not found in the sources" is something this system can know; "does not exist" is not. A sentence that asserts non-existence
# of a law, Act, section or article is therefore an unsupported claim, unless it is scoped to the sources or a source for
# that very provision says it was omitted/repealed.
EXISTENCE_CLAIM_RE = re.compile(
    r"\bno such (?:section|article|act|provision|law|offence|chapter|rule)\b"
    r"|\b(?:does|do|did) not (?:actually |really )?exist\b|\bno longer exists?\b|\bnon-?existent\b"
    r"|\bnever (?:existed|been enacted)\b|\bwas never (?:enacted|passed)\b"
    r"|\bdoes not correspond to any (?:section|provision|article|law)\b", re.I)
SOURCE_SCOPE_RE = re.compile(
    r"\b(?:provided|available|retrieved|given|cited|supplied)\s+(?:sources?|documents?|text|excerpts?|context|passages?)\b"
    r"|\bin (?:the |these |those )?(?:sources?|documents?|excerpts?|retrieved)\b|\b(?:sources?|documents?)\s+(?:do|does) not\b", re.I)
GONE_RE = re.compile(r"\b(?:omitted|repealed|ceased to have effect|deleted)\b", re.I)
# Markers that look like citations but are not the plain [n] form: [4(c)], [4, 5], [1-3].
MALFORMED_CITATION_RE = re.compile(r"\[\d{1,2}\s*[(,;/–-][^\]\[\n]{0,14}\]")

_STOP = set("""this that with from have been were they them their there then than which what when where will would could should shall must such
other also only into upon under over about after before between within without section sections sanhita article articles provided provision provisions
source sources answer available documents following includes include including included means defined defines provides states according therefore thus
however based given listed note relevant relates related question each every both some more most many much very same these those whose whom while
because since although though whether either neither any all can may might does doing done make makes made being""".split())


def _norm(text: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKC", text).lower()
    for a, b in _PUNCTUATION_MAP:
        t = t.replace(a, b)
    return t


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(_norm(text))


def _stem(w: str) -> str:
    if w.endswith("ies") and len(w) > 5: return w[:-3] + "y"
    if w.endswith("ing") and len(w) > 6: return w[:-3]
    if w.endswith("ed") and len(w) > 5: return w[:-2]
    if w.endswith("es") and len(w) > 5: return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 4: return w[:-1]
    return w


def _act_name_words() -> set[str]:
    """Act names are repeated in answers but are not part of a provision's own text, so they are not evidence either way."""
    words: set[str] = set()
    for d in catalog.DOCUMENTS:
        words |= set(re.findall(r"[a-z]{4,}", d.act_name_en.lower()))
    return words


_STOP_STEMS = {_stem(w) for w in _STOP | _act_name_words()}


def content_stems(text: str, exclude: frozenset | set = frozenset()) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z]{4,}", _norm(text))} - _STOP_STEMS - set(exclude)


def sentences(answer: str) -> list[str]:
    out: list[str] = []
    for line in answer.split("\n"):
        line = line.strip()
        if line:
            out += [p.strip() for p in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"(\[])", line) if p.strip()]
    return out


def is_refusal(answer: str) -> bool:
    """True when the answer declines to answer. The prompt tells the model to begin with a fixed phrase."""
    first = answer.strip().split("\n")[0].strip() if answer.strip() else ""
    return bool(REFUSAL_RE.search(first))


# --------------------------------------------------------------------------- section references
def referenced_sections(text: str) -> set[str]:
    """Section/article numbers mentioned in a piece of text (lists like 'sections 3, 4 and 5' included)."""
    text = normalize_unicode(text)
    found: set[str] = set()
    for m in REF_RE.finditer(text):
        found.add(m.group(1).upper())
        tail = text[m.end(): m.end() + 60]
        for extra in EXTRA_NUMBERS_RE.finditer(tail):
            found.add(extra.group(1).upper())
    return found


def allowed_sections(question: str, context: list[dict]) -> set[str]:
    """Numbers the answer may legitimately mention: the cited sections and anything the sources
    themselves cross-reference. Numbers that only the USER mentioned are deliberately NOT allowed: if someone
    asks about a non-existent 'Section 999' and the answer repeats it as if it existed, that must be flagged.
    (A genuine 'Section 103' question is fine: the exact lookup puts Section 103 into the sources.)"""
    allowed: set[str] = set()
    for c in context:
        allowed.add(c["section_number"].upper())
        allowed |= referenced_sections(c["text"])
        if c.get("unit") == "schedule":      # schedule tables list sections bare ("263(b) If charged with ...")
            allowed |= {m.upper() for m in SCHEDULE_ENTRY_RE.findall(c["text"])}
    return allowed


def _unsupported_references(answer: str, allowed: set[str]) -> dict[str, str]:
    """ref -> the sentence that mentions it. Sentences that state a reference is ABSENT are skipped."""
    bad: dict[str, str] = {}
    for sentence in sentences(answer):
        if ABSENCE_RE.search(sentence):
            continue
        for ref in referenced_sections(sentence) - allowed:
            bad.setdefault(ref, sentence)
    return bad


def unverified_references(answer: str, question: str, context: list[dict]) -> list[str]:
    bad = _unsupported_references(answer, allowed_sections(question, context))
    return sorted(bad, key=lambda s: (len(s), s))


# --------------------------------------------------------------------------- citations
def strip_invalid_citations(answer: str, n_sources: int) -> str:
    """Remove [n] markers that point to a source number that does not exist."""
    def fix(m: re.Match) -> str:
        return m.group(0) if 1 <= int(m.group(1)) <= n_sources else ""
    return CITATION_RE.sub(fix, answer)


def uses_citations(answer: str) -> bool:
    return bool(CITATION_RE.search(answer))


# --------------------------------------------------------------------------- quotations
def extract_quotes(answer: str) -> list[dict]:
    """Double-quoted passages of at least QUOTE_MIN_WORDS words, with the citation markers that follow them
    in the same sentence. Shorter quoted terms (a defined word such as "act") are not quotations."""
    found = []
    for line in answer.split("\n"):
        for start, stop in _quoted_spans(line):
            text = line[start:stop].strip()
            if len(tokens(text)) < config.QUOTE_MIN_WORDS:
                continue
            rest = line[stop + 1:]
            end = re.search(r"[.!?](?:\s|$)", rest)
            cited = [int(x) for x in CITATION_RE.findall(rest[: end.end() if end else len(rest)])]
            found.append({"quote": text, "cited": cited})
    return found


def _quoted_spans(line: str) -> list[tuple[int, int]]:
    """(start, stop) of each quoted passage on one line. Quote marks are paired in order (straight quotes alternate
    open/close; a curly opening mark always opens), and short terms are kept in the pairing so that the closing mark of
    "child" can never be mistaken for the opening mark of the next quotation."""
    spans: list[tuple[int, int]] = []
    opened = None
    for m in re.finditer(r"[“”\"]", line):
        mark = m.group()
        if mark == "“" or (mark == '"' and opened is None):
            opened = m.end()
        elif opened is not None:
            spans.append((opened, m.start()))
            opened = None
    return spans


def _legal_changes(quote_tokens: list[str], window: list[str]) -> list[str]:
    changed: set[str] = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, quote_tokens, window).get_opcodes():
        if tag != "equal":
            changed |= (set(quote_tokens[i1:i2]) | set(window[j1:j2])) & LEGAL_WORDS
    return sorted(changed)


def verify_quote(quote: str, context: list[dict]) -> dict:
    """Is this quotation in the sources? Words are compared, so case, punctuation, dashes, curly quotes and line
    breaks do not matter. A near-match is 'approximate', unless the difference touches a legal word
    (not / shall / may / and / or ...), which makes it 'altered_legal_term'."""
    q = tokens(quote)
    segments = [s for s in (tokens(p) for p in re.split(r"…|\.\.\.", quote)) if len(s) >= 2]
    chunk_tokens = [tokens(c["text"]) for c in context]
    joined = [" " + " ".join(t) + " " for t in chunk_tokens]
    exact = [i for i, j in enumerate(joined) if segments and all(" " + " ".join(s) + " " in j for s in segments)]
    if exact:
        return {"status": "verified", "sources": [i + 1 for i in exact]}
    if len(segments) != 1:                       # an ellipsis quotation is only checked piece by piece
        return {"status": "not_found", "sources": [], "ratio": 0.0}
    qset, best = set(q), (0.0, -1, [])
    for i, t in enumerate(chunk_tokens):
        for length in range(max(2, len(q) - 2), len(q) + 3):
            for start in range(0, max(1, len(t) - length + 1)):
                window = t[start:start + length]
                if len(qset & set(window)) < 0.6 * len(qset):
                    continue
                ratio = difflib.SequenceMatcher(None, q, window).ratio()
                if ratio > best[0]:
                    best = (ratio, i, window)
    ratio, idx, window = best
    if ratio >= config.QUOTE_APPROX_RATIO:
        changed = _legal_changes(q, window)
        return {"status": "altered_legal_term" if changed else "approximate", "sources": [idx + 1],
                "ratio": round(ratio, 3), "changed": changed}
    return {"status": "not_found", "sources": [], "ratio": round(ratio, 3)}


# --------------------------------------------------------------------------- numbers and thresholds
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_NUMWORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
             "twelve": 12, "fourteen": 14, "fifteen": 15, "eighteen": 18, **_TENS}
_ONES = "one|two|three|four|five|six|seven|eight|nine"
_NUM = (r"((?:" + "|".join(_TENS) + r")[- ](?:" + _ONES + r")|\d{1,3}|" + "|".join(sorted(_NUMWORDS, key=len, reverse=True)) + r")")
THRESHOLD_RE = re.compile(_NUM + r"(?:\s+|-)(years?|months?|days?|hours?)\b", re.I)
_FILLER = r"(?:(?:a|the|of|first|period of|term of|age of)\s+)*$"        # "above the age of eighteen years" == "above eighteen years"
_POST_QUALIFIERS = [("ge", r"^\s*(?:and above|or more|or above|and upwards)"), ("le", r"^\s*(?:or less|and below)")]
_PRE_QUALIFIERS = [
    ("ge", r"(?:not less than|at least|minimum of)\s+" + _FILLER),
    ("le", r"(?:not exceeding|not more than|up to|upto|extend(?:s|ing)? to|at most|maximum of)\s+" + _FILLER),
    ("gt", r"(?:more than|a longer period than|longer period than|longer than|exceeding|in excess of|greater than|beyond|over|above)\s+" + _FILLER),
    ("lt", r"(?:less than|a shorter period than|shorter period than|below|under|shorter than)\s+" + _FILLER),
]


def _number_value(raw: str) -> int:
    return int(raw) if raw.isdigit() else sum(_NUMWORDS[p] for p in re.split(r"[- ]", raw))


def thresholds(text: str) -> list[tuple[int, str, str]]:
    """(value, unit, qualifier) for every duration in the text. Qualifier: 'ge' (and above / not less than),
    'gt' (more than), 'le' (up to / not exceeding), 'lt' (less than), or '' for a bare number (exactly that)."""
    t = _norm(text)
    out = []
    for m in THRESHOLD_RE.finditer(t):
        qualifier = ""
        post, pre = t[m.end(): m.end() + 20], t[max(0, m.start() - 40): m.start()]
        for name, pattern in _POST_QUALIFIERS:
            if re.search(pattern, post):
                qualifier = name
                break
        if not qualifier:
            for name, pattern in _PRE_QUALIFIERS:
                if re.search(pattern, pre):
                    qualifier = name
                    break
        out.append((_number_value(m.group(1)), m.group(2).rstrip("s"), qualifier))
    return out


# --------------------------------------------------------------------------- modals ("shall" restated as "may")
_MODAL_CLASS = {"shall": "must", "must": "must", "may": "may", "shall not": "must not", "must not": "must not", "may not": "must not"}
MODAL_RE = re.compile(r"\b(shall not|must not|may not|shall|must|may)\s+((?:be |been )?[a-z]+(?: [a-z]+){1,2})\b")


def modal_phrases(text: str) -> dict[str, set[str]]:
    """{words that follow the modal: the modals used with them}, e.g. 'be released on bail' -> {'shall'}."""
    out: dict[str, set[str]] = {}
    for m in MODAL_RE.finditer(re.sub(r"\s+", " ", _norm(text))):
        out.setdefault(m.group(2), set()).add(m.group(1))
    return out


def modal_changes(sentence: str, source_modals: dict[str, set[str]]) -> list[tuple[str, str, str]]:
    """(answer modal, source modal, words) where the answer reuses the source's own words after a modal but changes an
    obligation into a permission or the reverse: 'may be released on bail' against 'shall be released on bail'.
    'shall' and 'must' count as the same. Only wording that appears in both is compared, so a paraphrase is never flagged
    (or caught). Negated forms ('shall not', 'must not') are deliberately NOT judged here: a source that says 'No person
    shall be detained' and an answer that says 'shall not be detained' mean the same, and 'may ... but shall not' provisos
    are routinely paraphrased. On the 41 live answers the unrestricted comparison gave 2 false alarms in 4; this narrower one gave none."""
    changes = []
    for tail, answer_modals in modal_phrases(sentence).items():
        source = source_modals.get(tail)
        if not source:
            continue
        answer_class = {_MODAL_CLASS[m] for m in answer_modals}
        source_class = {_MODAL_CLASS[m] for m in source}
        softened = answer_class == {"may"} and "may" not in source_class            # obligation / prohibition -> permission
        hardened = answer_class == {"must"} and source_class == {"may"}             # permission -> obligation
        if softened or hardened:
            changes.append((sorted(answer_modals)[0], sorted(source)[0], tail))
    return changes


# --------------------------------------------------------------------------- the verification pass
def _issue(kind: str, detail: str = "", **extra) -> dict:
    return {"type": kind, "detail": detail, **extra}


def verify_answer(answer: str, question: str, context: list[dict], n_sources: int | None = None) -> dict:
    """Check an answer against the chunks the model was given. Pass the RAW answer (before invalid markers are stripped).

    Returns {"refusal", "errors", "warnings", "info", "quotes"}; every issue is a dict with a "type" and a "detail".
    """
    n = len(context) if n_sources is None else n_sources
    errors: list[dict] = []
    warnings: list[dict] = []
    info: list[dict] = []
    refusal = is_refusal(answer)

    cited_numbers = sorted({int(x) for x in CITATION_RE.findall(answer)})
    for number in cited_numbers:
        if not 1 <= number <= n:
            errors.append(_issue("invalid_citation", f"[{number}]"))
    if refusal and cited_numbers:
        info.append(_issue("refusal_with_citations", str(cited_numbers)))

    for ref, sentence in _unsupported_references(answer, allowed_sections(question, context)).items():
        errors.append(_issue("unsupported_section_reference", ref, sentence=sentence))

    for marker in dict.fromkeys(MALFORMED_CITATION_RE.findall(answer)):
        warnings.append(_issue("malformed_citation", marker))

    for sentence in sentences(answer):
        if EXISTENCE_CLAIM_RE.search(sentence) and not SOURCE_SCOPE_RE.search(sentence):
            refs = referenced_sections(sentence)
            if not any(c["section_number"].upper() in refs and GONE_RE.search(c["text"]) for c in context):
                errors.append(_issue("unsupported_existence_claim", "", sentence=sentence))

    quotes = []
    reported_through_quote: list[str] = []          # a sentence whose problem is already reported via its quotation
    for q in extract_quotes(answer):
        result = verify_quote(q["quote"], context)
        quotes.append({"quote": q["quote"][:120], "cited": q["cited"], **result})
        entry = {"quote": q["quote"][:120], "cited": q["cited"]}
        if result["status"] == "verified":
            if q["cited"] and not set(q["cited"]) & set(result["sources"]):
                warnings.append(_issue("quote_cited_to_wrong_source", f"found in {result['sources']}, cited {q['cited']}", **entry))
                reported_through_quote.append(q["quote"])
        elif result["status"] == "approximate":
            warnings.append(_issue("quote_not_exact", f"similarity {result['ratio']}", **entry))
        elif result["status"] == "altered_legal_term":
            errors.append(_issue("quote_altered_legal_term", f"changed {result['changed']}", **entry))
        else:
            errors.append(_issue("quote_not_found", f"best similarity {result['ratio']}", **entry))

    if not refusal and context:
        chunk_stems = [content_stems(c["text"]) for c in context]
        all_stems = set().union(*chunk_stems)
        question_stems = content_stems(question)
        chunk_thresholds = [thresholds(c["text"]) for c in context]
        chunk_modals = [modal_phrases(c["text"]) for c in context]
        for sentence in sentences(answer):
            if ABSENCE_RE.search(sentence):
                continue
            cited = [int(x) for x in CITATION_RE.findall(sentence) if 1 <= int(x) <= n]
            source_modals: dict[str, set[str]] = {}
            for i in (cited or range(1, len(context) + 1)):
                for tail, modals in chunk_modals[i - 1].items():
                    source_modals.setdefault(tail, set()).update(modals)
            for answer_modal, source_modal, tail in modal_changes(CITATION_RE.sub("", sentence), source_modals):
                warnings.append(_issue("modal_changed", f"answer '{answer_modal} {tail}'; source '{source_modal} {tail}'", sentence=sentence))
            words = content_stems(CITATION_RE.sub("", sentence), exclude=question_stems)
            if len(words) >= 4:
                ratio_all = len(words & all_stems) / len(words)
                cited_stems = set().union(*(chunk_stems[i - 1] for i in cited)) if cited else set()
                ratio_cited = len(words & cited_stems) / len(words) if cited else None
                if ratio_all < config.SUPPORT_MIN_RATIO:
                    warnings.append(_issue("weak_support", f"{ratio_all:.2f} of its content words are in the sources",
                                           sentence=sentence, missing=sorted(words - all_stems)))
                elif (cited and ratio_cited < config.SUPPORT_MIN_RATIO and ratio_all >= config.MISCITED_ALL_MIN_RATIO
                      and not any(qt in sentence for qt in reported_through_quote)):
                    best = max(range(len(context)), key=lambda i: len(words & chunk_stems[i])) + 1
                    warnings.append(_issue("miscited_claim", f"cited {cited}: {ratio_cited:.2f}; best match [{best}]",
                                           sentence=sentence, missing=sorted(words - cited_stems)))
            for value, unit, qualifier in thresholds(CITATION_RE.sub("", sentence)):
                scope = [chunk_thresholds[i - 1] for i in cited] if cited else chunk_thresholds
                in_scope = [t for lst in scope for t in lst if t[0] == value and t[1] == unit]
                anywhere = [t for lst in chunk_thresholds for t in lst if t[0] == value and t[1] == unit]
                if not anywhere:
                    warnings.append(_issue("number_not_in_sources", f"{value} {unit}", sentence=sentence))
                elif qualifier and in_scope and qualifier not in {t[2] for t in in_scope}:
                    seen = sorted({t[2] or "bare" for t in in_scope})
                    warnings.append(_issue("threshold_qualifier_mismatch", f"answer '{qualifier}' {value} {unit}; sources {seen}", sentence=sentence))
    return {"refusal": refusal, "errors": errors, "warnings": warnings, "info": info, "quotes": quotes}


# --------------------------------------------------------------------------- notes shown to the user
_WARNING_PRIORITY = ["quote_cited_to_wrong_source", "modal_changed", "quote_not_exact", "threshold_qualifier_mismatch", "number_not_in_sources",
                     "malformed_citation", "miscited_claim", "weak_support"]
MAX_WARNING_NOTES = 3


def verification_notes(verification: dict, language: str) -> list[str]:
    """One note per kind of finding. Confirmed errors come first and say 'Verification error'; warnings say 'Check',
    are limited to MAX_WARNING_NOTES, and 'weak_support' is summarised once however many sentences it covers."""
    from rag.language import VERIFICATION_NOTES
    texts = VERIFICATION_NOTES[language]
    notes: list[str] = []
    for kind in dict.fromkeys(i["type"] for i in verification["errors"]):
        first = next(i for i in verification["errors"] if i["type"] == kind)
        notes.append(texts[kind].format(detail=first["detail"]))
    present = {i["type"]: i for i in reversed(verification["warnings"])}      # earliest occurrence wins
    for kind in _WARNING_PRIORITY:
        if kind in present and sum(1 for n in notes if n.startswith(("Check", "जाँचें"))) < MAX_WARNING_NOTES:
            notes.append(texts[kind].format(detail=present[kind]["detail"]))
    return notes


def partial_provision_notes(truncated: list[dict], language: str) -> list[str]:
    """A deterministic note for each provision the question NAMED but that only partly fitted the context budget,
    so a list drawn from it is never presented as complete, whatever the model wrote."""
    from rag.generation import format_parts, provision_label
    from rag.language import PARTIAL_PROVISION_NOTE
    return [PARTIAL_PROVISION_NOTE[language].format(parts=format_parts(t["parts_included"]), total=t["parts_total"],
                                                    label=provision_label(t["provision"]))
            for t in truncated if t.get("exact")]
