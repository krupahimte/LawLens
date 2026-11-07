"""The RAG pipeline: question in, grounded and cited answer out.

    question -> [follow-up rewrite] -> retrieve (BGE-M3 + ChromaDB) -> guardrails
             -> choose sources in the user's language -> Qwen3 generation (streamed)
             -> validate citations -> answer + sources + notes + disclaimer

``answer_stream`` yields events (used by the streaming API); ``answer`` collects them.
"""
import time
from collections.abc import Iterator

import config
from rag import conversation, generation, guardrails, retrieval
from rag.catalog import BY_ID
from rag.chunking import unit_label
from rag.language import (ANSWER_INCOMPLETE_NOTE, DISCLAIMER, FALLBACK_LANGUAGE_NOTE, GREETING, HINDI_PAUSED, NOT_ENOUGH_INFO, OCR_LIMITATION,
                          OCR_NOTE, UNVERIFIED_REFERENCE_NOTE, detect_language, is_greeting)
from rag.preprocessing import normalize_unicode

CONDENSE_PROMPT = (
    "Rewrite the user's LAST message as one standalone question about Indian law, using the earlier "
    "conversation only to resolve references like 'it', 'that section' or 'what about the punishment'. "
    "Keep the same language as the last message. Output only the question, nothing else. "
    "If the last message is already standalone, output it unchanged."
)


def make_source(n: int, chunk: dict) -> dict:
    doc = BY_ID[chunk["doc_id"]]
    return {
        "n": n,
        "chunk_id": chunk["chunk_id"],      # exact chunk behind this citation (additive field)
        "label": generation.source_label(chunk),
        "act_name": chunk["act_name"],
        "act_name_en": chunk["act_name_en"],
        "unit": chunk["unit"],
        "unit_label": unit_label(doc, chunk["unit"]),
        "section_number": chunk["section_number"],
        "section_title": chunk["section_title"],
        "language": chunk["language"],
        "doc_id": chunk["doc_id"],
        "file": doc.filename,
        "page_start": chunk["page_start"],
        "page_end": chunk["page_end"],
        "text_source": chunk["text_source"],
        "ocr_conf": chunk["ocr_conf"],
        "low_quality": chunk["low_quality"],
        "number_verified": chunk["number_verified"],
        "number_inferred": bool(chunk.get("number_inferred", False)),
        "match": chunk.get("match", ""),
        "distance": round(chunk["distance"], 3),
        "snippet": chunk["text"][:400],
    }


def standalone_question(question: str, history: list[dict]) -> str:
    if not history:
        return question
    messages = [{"role": "system", "content": CONDENSE_PROMPT}, *history,
                {"role": "user", "content": question}]
    rewritten = generation.chat_once(messages, max_tokens=120)
    return rewritten.splitlines()[0].strip() if rewritten else question


def _final(status: str, answer: str, language: str, sources: list[dict], notes: list[str],
           conversation_id: str | None, timings: dict, standalone: str, context_report: dict | None = None,
           verification: dict | None = None, generation_report: dict | None = None) -> dict:
    return {
        "type": "final", "status": status, "answer": answer, "language": language,
        "sources": sources, "notes": notes, "disclaimer": DISCLAIMER[language],
        "conversation_id": conversation_id, "standalone_question": standalone, "timings": timings,
        "context_report": context_report,   # which chunks the model saw / did not see, and why (answered turns only)
        "verification": verification,       # confirmed errors, warnings and quotation checks (answered turns only)
        "generation": generation_report,    # why the model stopped, token counts, truncated yes/no (answered turns only)
    }


def answer_stream(question: str, language: str = "auto", conversation_id: str | None = None) -> Iterator[dict]:
    started = time.time()
    timings: dict[str, float] = {}
    question = normalize_unicode(question).strip()
    conversation_id = conversation_id or conversation.new_conversation_id()
    if not config.ENABLE_HINDI:
        # English-only mode: answer language is fixed, and a Hindi question gets a notice instead of an answer.
        if detect_language(question) == "hi":
            yield _final("unsupported_language", HINDI_PAUSED, "en", [], [], conversation_id, timings, question)
            return
        answer_lang = "en"
    else:
        answer_lang = language if language in ("en", "hi") else detect_language(question)

    if is_greeting(question):
        yield _final("greeting", GREETING[answer_lang], answer_lang, [], [], conversation_id, timings, question)
        return

    history = conversation.get_history(conversation_id)
    t = time.time()
    standalone = standalone_question(question, history)
    timings["rewrite_s"] = round(time.time() - t, 2)

    t = time.time()
    result = retrieval.retrieve(standalone)
    timings["retrieval_s"] = round(time.time() - t, 2)

    has_exact = any(h.get("match") == "exact" for h in result.hits)
    relevant_hits = [h for h in result.hits if h.get("match") == "exact" or h["distance"] <= config.MAX_DISTANCE]
    if not relevant_hits or not guardrails.is_relevant(result.best_distance, has_exact):
        message = NOT_ENOUGH_INFO[answer_lang]
        conversation.add_message(conversation_id, "user", question)
        conversation.add_message(conversation_id, "assistant", message)
        yield _final("insufficient", message, answer_lang, [], [], conversation_id, timings, standalone)
        return

    context, flags, context_report = retrieval.assemble_context(relevant_hits, answer_lang)
    if not context:  # relevant provisions exist, but only as unreadable OCR text
        pointers = [make_source(i, c) for i, c in enumerate(flags["unreliable_sources"][:3], start=1)]
        message = OCR_LIMITATION[answer_lang]
        conversation.add_message(conversation_id, "user", question)
        conversation.add_message(conversation_id, "assistant", message)
        yield _final("ocr_limited", message, answer_lang, pointers, [], conversation_id, timings, standalone)
        return

    sources = [make_source(i, c) for i, c in enumerate(context, start=1)]
    yield {"type": "sources", "sources": sources, "language": answer_lang, "conversation_id": conversation_id}

    t = time.time()
    # Long provisions the question NAMED but that only partly fitted the budget: the model is told, and so is the user.
    partial = [p for p in context_report.get("truncated_provisions", []) if p.get("exact")]
    messages = generation.build_messages(standalone, context, answer_lang, partial=partial)  # no history: avoids topic leakage
    pieces: list[str] = []
    stats: dict = {}                                   # filled by stream_chat: why Ollama stopped, token counts
    for piece in generation.stream_chat(messages, stats=stats):
        pieces.append(piece)
        yield {"type": "token", "text": piece}
    timings["generation_s"] = round(time.time() - t, 2)
    truncated = generation.stopped_early(stats)

    raw_answer = "".join(pieces).strip()
    verification = guardrails.verify_answer(raw_answer, standalone, context)      # on the RAW text, so bad markers are seen
    answer = guardrails.strip_invalid_citations(raw_answer, len(context))
    notes: list[str] = [ANSWER_INCOMPLETE_NOTE[answer_lang]] if truncated else []      # most important note: always first
    notes += guardrails.verification_notes(verification, answer_lang)
    notes += guardrails.partial_provision_notes(partial, answer_lang)
    if any(c["text_source"] == "ocr" for c in context):
        notes.append(OCR_NOTE[answer_lang])
    if flags["used_fallback_language"]:
        notes.append(FALLBACK_LANGUAGE_NOTE[answer_lang])

    timings["total_s"] = round(time.time() - started, 2)
    conversation.add_message(conversation_id, "user", question)
    conversation.add_message(conversation_id, "assistant", answer)
    generation_report = {"done_reason": stats.get("done_reason"), "truncated": truncated, "output_tokens": stats.get("eval_count"),
                         "prompt_tokens": stats.get("prompt_eval_count"), "token_limit": stats.get("token_limit")}
    yield _final("answered", answer, answer_lang, sources, notes, conversation_id, timings, standalone, context_report, verification,
                 generation_report)


def answer(question: str, language: str = "auto", conversation_id: str | None = None) -> dict:
    final = None
    for event in answer_stream(question, language, conversation_id):
        if event["type"] == "final":
            final = event
    return final
