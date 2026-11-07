"""Answer generation with Qwen3 4B through Ollama, grounded in retrieved sources.

The model sees ONLY the numbered sources we give it and is told to cite them as [1], [2].
The visible citation list (Act, section, page, file) is built by our code from chunk
metadata, never by the model, so a citation cannot be invented.
"""
import json
from collections.abc import Iterator

import httpx

import config
from rag.catalog import BY_ID
from rag.chunking import unit_label
from rag.embeddings import OllamaError
from rag.language import LANGUAGE_NAMES

# NOTE: these instructions make faithful answers more likely; they do not guarantee them. A small local model can
# still misread a condition. rag/guardrails.py therefore verifies quotations, citations and numbers afterwards, and
# says plainly which of its findings are confirmed errors and which are only warnings.
SYSTEM_PROMPT = """You are an assistant that explains Indian law using ONLY the numbered SOURCES provided. You give legal information, not legal advice: do not tell the user what they personally should do in a dispute.

GROUNDING
1. Use only facts that appear in the SOURCES. Do not use outside knowledge, other laws or memory, even to fill a gap. If the SOURCES lack something needed, say what is missing instead of guessing.
2. Never mention an Act, section or article number that does not appear in the SOURCES.
3. After each sentence, cite the number of the source that states it, like [1] or [2][3]. Cite a source only for what it actually says. Write only plain numbers such as [4], never [4(c)] or [4, 5]. Do not cite anything when you decline to answer.
4. If the SOURCES do not answer the question, begin your reply with exactly: "The available documents do not answer" and then say briefly why.
5. A provision that is missing from the SOURCES is not the same as a provision that does not exist. Never say that a law, Act, section or article "does not exist", "was never enacted" or "has no such section". Say only that the SOURCES provided do not contain it. If the question names a law that is not among the SOURCES (for example the IPC or CrPC), say that the SOURCES do not cover it; do not say what that law does or does not contain.

LEGAL ACCURACY (the commonest mistakes; check each against the SOURCES before you answer)
6. Keep every condition, exception, proviso ("Provided that ...") and explanation. Never drop or soften one.
7. Keep "shall", "shall not", "may" and "must" exactly as written, in summaries too: if a source says "shall be released", do not write "may be released". A prohibition must never be restated as a permission. Example: if a source says "a licence shall not be granted if the applicant is under eighteen or has a prior conviction", the licence is refused if EITHER applies; never write that it may be granted when one of them applies.
8. Keep AND and OR exactly. Conditions joined by "and" must all hold; conditions joined by "or" need only one. Say which.
9. Copy numbers, durations, amounts and qualifiers exactly. "three years and above", "more than three years", "not less than three years", "up to three years" and a bare "three years" are all different. When a source gives different consequences for different thresholds, keep them separate.
10. When you state a condition, exception, threshold or punishment, put the source's own words in double quotation marks, copied exactly (about 30 words at most), and cite them.
11. Do not say that something is not required, not allowed or does not apply unless a source says so in words. If the SOURCES are silent, say that they are silent.
12. A source labelled "part k of N", or a note about partial provisions, means the full text was NOT supplied. Never present a list or definition taken from it as complete; say that it is partial.

STYLE
13. Keep the answer under about 300 words. Give a short direct answer first, then the key details. When a provision has a long list of clauses or definitions, give the opening words and the main items, say how many further clauses there are and cite the source for them; do not copy the whole list. Do not add explanations, opinions or conclusions that the SOURCES do not state.
14. A source marked "OCR" may contain reading errors: do not quote it; describe it generally and tell the user to check the original page.
15. Write the whole answer in {language}. Keep section numbers and Act names recognisable."""


def source_label(chunk: dict) -> str:
    doc = BY_ID[chunk["doc_id"]]
    label = f"{chunk['act_name']}, {unit_label(doc, chunk['unit'])} {chunk['section_number']}"
    if chunk["section_title"]:
        label += f" ({chunk['section_title']})"
    return label


def provision_label(provision: str) -> str:
    """'cp_en:section:2' -> 'The Consumer Protection Act, 2019, Section 2'."""
    doc_id, unit, number = provision.split(":", 2)
    doc = BY_ID[doc_id]
    return f"{doc.act_name}, {unit_label(doc, unit)} {number}"


def format_parts(parts: list[int]) -> str:
    """[1, 2, 3] -> '1-3'; [1, 2, 4] -> '1-2, 4'."""
    runs, start, prev = [], None, None
    for p in sorted(parts):
        if start is None:
            start = prev = p
        elif p == prev + 1:
            prev = p
        else:
            runs.append((start, prev))
            start = prev = p
    if start is not None:
        runs.append((start, prev))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)


def build_context(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks, start=1):
        doc = BY_ID[c["doc_id"]]
        note = ""
        if c["text_source"] == "ocr":
            note = " | OCR text (may contain errors)"
        part = f" | part {c['part']} of {c['parts_total']}" if int(c.get("parts_total", 1)) > 1 else ""
        blocks.append(
            f"[{i}] {source_label(c)} | {'Hindi' if c['language'] == 'hi' else 'English'} text, "
            f"page {c['page_start']} of {doc.filename}{part}{note}\n{c['text']}"
        )
    return "\n\n".join(blocks)


def partial_block(partial: list[dict] | None) -> str:
    """Tell the model which long provisions it only received in part (from the context report)."""
    lines = [f"PARTIAL PROVISIONS: {provision_label(p['provision'])} is long and only parts {format_parts(p['parts_included'])} of "
             f"{p['parts_total']} are included in the SOURCES, so it is INCOMPLETE. Any list or definitions you give from it are partial: "
             f"say so, and do not describe it as complete." for p in (partial or [])]
    return ("\n\n" + "\n".join(lines)) if lines else ""


def build_messages(question: str, chunks: list[dict], answer_language: str, history: list[dict] | None = None,
                   partial: list[dict] | None = None) -> list[dict]:
    system = SYSTEM_PROMPT.format(language=LANGUAGE_NAMES[answer_language])
    messages = [{"role": "system", "content": system}]
    for turn in (history or [])[-4:]:  # recent turns only, for follow-up context
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({
        "role": "user",
        "content": (f"SOURCES:\n{build_context(chunks)}{partial_block(partial)}\n\nQUESTION: {question}\n\n"
                    f"Answer in {LANGUAGE_NAMES[answer_language]}, citing sources like [1]. "
                    f"Before answering, check every condition, negation and number against the SOURCES."),
    })
    return messages


def stopped_early(stats: dict) -> bool:
    """True when the answer was cut off: Ollama hit the output-token limit ("length"), or the stream ended without
    ever sending its final "done" message. An empty dictionary (nothing recorded) is not treated as a truncation."""
    return stats.get("done_reason") == "length" or stats.get("done") is False


def stream_chat(messages: list[dict], max_tokens: int = 700, stats: dict | None = None) -> Iterator[str]:
    """Yield the model's answer piece by piece.

    If ``stats`` is given it is filled in as the stream is read: ``done`` (did Ollama send its final message),
    ``done_reason`` ("stop" = finished by itself, "length" = hit ``max_tokens``), ``eval_count`` (answer tokens),
    ``prompt_eval_count`` (prompt tokens) and ``token_limit``. Ollama's own account of why it stopped is the only
    reliable sign of a truncated answer; guessing from the last character is not.
    """
    payload = {
        "model": config.CHAT_MODEL, "messages": messages, "stream": True,
        "options": {"temperature": 0.1, "num_ctx": 8192, "num_predict": max_tokens},
    }
    if stats is not None:
        stats.update({"done": False, "done_reason": None, "token_limit": max_tokens})
    try:
        with httpx.stream("POST", f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=config.OLLAMA_TIMEOUT) as r:
            if r.status_code == 404:
                raise OllamaError(f"Model not found. Run: ollama pull {config.CHAT_MODEL}")
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                piece = data.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if data.get("done"):
                    if stats is not None:
                        stats.update({"done": True, "done_reason": data.get("done_reason"), "eval_count": data.get("eval_count"),
                                      "prompt_eval_count": data.get("prompt_eval_count")})
                    break
    except httpx.ConnectError as exc:
        raise OllamaError(f"Cannot reach Ollama at {config.OLLAMA_URL}. Is it running?") from exc


def chat_once(messages: list[dict], max_tokens: int = 200) -> str:
    return "".join(stream_chat(messages, max_tokens)).strip()
