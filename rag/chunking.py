"""Legal-structure-aware chunking.

Instead of cutting text every N characters, we cut at legal boundaries:
one section/article = one chunk (split further only if it is very long).
Each chunk keeps its Act, section number, title, chapter, page range,
language and OCR provenance, so answers can cite the real source.

Pipeline for one document:
  pages -> clean -> one long text + page offsets -> find section starts
        -> keep a monotonically increasing sequence (drops false matches)
        -> attach bold headings -> split long sections -> chunk dicts
"""
import bisect
import functools
import re

import config
from rag.catalog import Document
from rag.extraction import BOLD_MARK
from rag.preprocessing import preprocess_page

# "  1[6A. Heading..." / "134. Assault" / "\x01362. ..."; group 'num' is 1-3 digits + optional letters.
#   after the number: spaces ("134. Assault"), a dash ("255.—Public"), or a line break ("174.\nSessions")
SECTION_RE = re.compile(
    r"^(?P<mark>\x01)?[ \t]*(?:\d{1,2}\[)*(?P<num>\d{1,3}[A-Z]{0,2})\."
    r"(?:[ \t]+|[ \t]*[—–][ \t]*|[ \t]*\n[ \t\x01]*)"
    r"(?=(?:\d{1,2}\[)*[A-Z“\"'(\[ऀ-ॿ\x01])",
    re.M,
)
CHAPTER_RE = re.compile(r"^\x01?[ \t]*(?:CHAPTER|PART|अध्याय|भाग)\s+[IVXLC0-9A-Zऀ-ॿ]{1,8}\b.*$", re.M)
SCHEDULE_RE = re.compile(
    r"^\x01?[ \t]*(?:THE\s+)?(?P<ord>FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH"
    r"|पहली|दूसरी|तीसरी|चौथी|पाँचवीं|पांचवीं|छठी|सातवीं|आठवीं|नौवीं|दसवीं|ग्यारहवीं|बारहवीं)\s+(?:SCHEDULE|अनुसूची)\b",
    re.M,
)
INLINE_TITLE_RE = re.compile(r"^(?:\d{1,2}\[)*(?P<title>.{3,250}?)\]?\s*\.\s*[—–-]", re.S)  # "Title.—Body"


def inline_title(text_after_number: str) -> str:
    """'Title.—Body' -> 'Title'. Empty if there is no real heading (e.g. the first sentence is body text)."""
    m = INLINE_TITLE_RE.match(text_after_number)
    if not m:
        return ""
    title = " ".join(m.group("title").replace(BOLD_MARK, "").split())
    if title.startswith("(") or re.search(r"\.\s", title):
        return ""
    return title

MAX_JUMP = 12          # a valid next section number is at most this far ahead
MIN_BODY_START = 150   # chars after "1." for it to count as the real start (not the table of contents)
MAX_TITLE_LINES = 4


def _key(num: str) -> tuple[int, str]:
    m = re.match(r"(\d+)([A-Z]*)", num)
    return int(m.group(1)), m.group(2)


def unit_label(doc: Document, unit: str | None = None) -> str:
    unit = unit or doc.unit
    labels = {
        "en": {"section": "Section", "article": "Article", "schedule": "Schedule", "page": "Page"},
        "hi": {"section": "धारा", "article": "अनुच्छेद", "schedule": "अनुसूची", "page": "पृष्ठ"},
    }
    return labels[doc.language][unit]


def find_events(full: str) -> list[dict]:
    """All possible boundaries in the text, in order, each with its start offset."""
    events = []
    for m in SECTION_RE.finditer(full):
        events.append({"kind": "section", "pos": m.start(), "num": m.group("num"), "key": _key(m.group("num"))})
    for m in CHAPTER_RE.finditer(full):
        if len(m.group(0)) <= 120:
            events.append({"kind": "chapter", "pos": m.start(), "label": m.group(0).lstrip(BOLD_MARK).strip()})
    for m in SCHEDULE_RE.finditer(full):
        events.append({"kind": "schedule", "pos": m.start(), "label": m.group(0).lstrip(BOLD_MARK).strip()})
    events.sort(key=lambda e: e["pos"])
    return events


def _edit_distance_le1(a: str, b: str) -> bool:
    """True if a and b differ by at most one inserted, deleted or substituted character."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    short, long_ = sorted((a, b), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


POSITION_TOLERANCE = 0.10   # a section may sit this far (fraction of the document) from where the English Act has it


@functools.lru_cache(maxsize=None)
def english_profile(act_name_en: str) -> dict[int, float]:
    """section number -> relative position (0..1) of that section inside the English text of the Act.

    Used as a reference when reading OCR'd Hindi headings: the same section sits at about the same
    relative position in both languages, whatever garbage OCR made of its number.
    """
    from rag.extraction import load_pages  # local import: extraction does not depend on chunking
    english = next((d for d in catalog_documents() if d.act_name_en == act_name_en and d.language == "en"), None)
    if english is None:
        return {}
    pages = load_pages(english)
    full = "\n".join(preprocess_page(p["text"], p["source"]) for p in pages)
    events = [e for e in select_body_events(find_events(full), full) if e["kind"] == "section"]
    if not events:
        return {}
    start, span = events[0]["pos"], max(len(full) - events[0]["pos"], 1)
    return {e["key"][0]: (e["pos"] - start) / span for e in events}


def catalog_documents():
    from rag import catalog
    return catalog.DOCUMENTS


def _read_ocr_number(token_key: tuple[int, str], fraction: float, last: int, profile: dict[int, float]) -> int | None:
    """Best reading of a possibly garbled heading number: the candidate (the number itself or anything one
    character away) that is greater than the previous section and sits closest to the right place."""
    number = token_key[0]
    readings = {m for m in profile if m > last and (m == number or _edit_distance_le1(str(m), str(number)))}
    if not readings:
        return None
    best = min(readings, key=lambda m: (abs(profile[m] - fraction), m != number))
    return best if abs(profile[best] - fraction) <= POSITION_TOLERANCE else None


def select_body_events(events: list[dict], full: str, profile: dict[int, float] | None = None) -> list[dict]:
    """Drop the table of contents and false matches; keep real sections in order.

    ``profile`` (OCR documents only) turns on position-aware reading of garbled numbers."""
    sections = [e for e in events if e["kind"] == "section"]
    start_pos = None
    for i, e in enumerate(sections):
        nxt = sections[i + 1]["pos"] if i + 1 < len(sections) else len(full)
        if e["key"] == (1, "") and nxt - e["pos"] >= MIN_BODY_START:
            start_pos = e["pos"]
            break
    if start_pos is None:
        start_pos = sections[0]["pos"] if sections else 0

    kept, last_key, in_schedule = [], (0, ""), False
    for e in events:
        if e["pos"] < start_pos:
            continue
        if e["kind"] == "schedule":
            in_schedule = True
            kept.append(e)
        elif e["kind"] == "chapter":
            kept.append(e)
        elif in_schedule:
            continue
        elif profile:
            fraction = (e["pos"] - start_pos) / max(len(full) - start_pos, 1)
            number = e["key"][0]
            if number == last_key[0] + 1 and not e["key"][1]:
                reading = number                                   # simply the next section: trust it
            else:
                reading = _read_ocr_number(e["key"], fraction, last_key[0], profile)
                if reading is None and last_key < e["key"] and number - last_key[0] <= MAX_JUMP:
                    reading = number                               # fits the sequence even if the position is off
            if reading is not None:
                suffix = e["key"][1] if reading == e["key"][0] else ""
                kept.append({**e, "key": (reading, suffix), "num": f"{reading}{suffix}",
                             "inferred": reading != e["key"][0]})
                last_key = (reading, suffix)
        elif last_key < e["key"] and e["key"][0] - last_key[0] <= MAX_JUMP:
            last_key = e["key"]
            kept.append(e)
    return kept


def reflow(text: str, base_offset: int) -> list[tuple[str, int, int]]:
    """Join hard-wrapped lines into paragraphs. Returns (paragraph, start, end) with absolute offsets."""
    paras: list[list] = []
    offset = base_offset
    new_para = re.compile(r"^(?:\(\S{1,6}\)|\d{1,3}[A-Z]?\.\s|Provided|Explanation|Illustration|परन्तु|परंतु|स्पष्टीकरण|दृष्टांत)")
    for line in text.split("\n"):
        stripped = line.strip()
        line_start = offset
        offset += len(line) + 1
        if not stripped:
            continue
        if paras and not new_para.match(stripped) and not paras[-1][0].endswith((":", "—")):
            paras[-1][0] += " " + stripped
            paras[-1][2] = offset - 1
        else:
            paras.append([stripped, line_start, offset - 1])
    return [(p[0], p[1], p[2]) for p in paras]


_ILLUSTRATION_HEADER = re.compile(r"^(?:Illustrations?|दृष्टांत|उदाहरण)\b[.:\s]*$")
_LETTER_ITEM = re.compile(r"^\([A-Za-zऀ-ॿ]{1,3}\)\s")          # "(a) A takes..." / "(क) ..."
_OPERATIVE_START = re.compile(r"^(?:\(\d+[A-Za-z]?\)|Explanation|Exception|Provided|स्पष्टीकरण|अपवाद|परन्तु|परंतु)")


def classify(paras: list[tuple[str, int, int]]) -> list[str]:
    """'illustration' for worked examples under an 'Illustration(s)' heading, else 'operative'.

    Illustrations are long and full of 'A' and 'Z'; mixed into a chunk they dilute the embedding of
    the operative law (e.g. the punishment clause of Section 303), so they are kept apart.
    """
    kinds, in_illustration = [], False
    for text, _, _ in paras:
        if _ILLUSTRATION_HEADER.match(text):
            in_illustration = True
        elif in_illustration and _OPERATIVE_START.match(text):
            in_illustration = False
        elif in_illustration and not _LETTER_ITEM.match(text):
            in_illustration = False
        kinds.append("illustration" if in_illustration else "operative")
    return kinds


def split_long(paras: list[tuple[str, int, int]], kinds: list[str] | None = None) -> list[tuple[str, list[tuple[str, int, int]]]]:
    """Group paragraphs into pieces <= MAX_CHUNK_CHARS. Returns [(kind, paragraphs)].

    A section that fits in one chunk stays whole. A longer one is cut at paragraph boundaries,
    also whenever operative text switches to illustrations (or back). The tail paragraph is
    repeated as overlap, but never across a kind change.
    """
    max_chars, overlap = config.MAX_CHUNK_CHARS, config.CHUNK_OVERLAP_CHARS
    kinds = kinds or ["operative"] * len(paras)
    expanded: list[tuple[str, int, int, str]] = []
    for (text, s, e), kind in zip(paras, kinds):  # break one oversized paragraph at sentence ends
        if len(text) <= max_chars:
            expanded.append((text, s, e, kind))
            continue
        buf = ""
        for piece in re.split(r"(?<=[.;।])\s+", text):
            if buf and len(buf) + len(piece) + 1 > max_chars:
                expanded.append((buf, s, e, kind))
                buf = piece
            else:
                buf = f"{buf} {piece}".strip()
        if buf:
            expanded.append((buf, s, e, kind))

    if sum(len(p[0]) + 1 for p in expanded) <= max_chars:
        kind = "operative" if any(p[3] == "operative" for p in expanded) else "illustration"
        return [(kind, [p[:3] for p in expanded])]

    groups, current, size, cur_kind = [], [], 0, None
    for para in expanded:
        too_big = current and size + len(para[0]) + 1 > max_chars
        switched = current and para[3] != cur_kind
        if too_big or switched:
            groups.append((cur_kind, [p[:3] for p in current]))
            tail = current[-1]
            keep_tail = too_big and not switched and len(tail[0]) <= overlap
            current = [tail] if keep_tail else []
            size = sum(len(p[0]) for p in current)
        current.append(para)
        cur_kind = para[3]
        size += len(para[0]) + 1
    if current:
        groups.append((cur_kind, [p[:3] for p in current]))
    return groups


def _clean_marks(text: str) -> str:
    return text.replace(BOLD_MARK, "")


def build_page_chunks(doc: Document, pages: list[dict]) -> list[dict]:
    """For documents that are not structured as numbered sections (the Hindi BNS booklet):
    one chunk per page (split if long). The 'section number' is the booklet page number."""
    chunks = []
    for p in pages:
        text = preprocess_page(p["text"], p["source"])
        if len(text) < 40:
            continue
        lines, offset = [], 0
        for line in text.split("\n"):
            if line.strip():
                lines.append((line.strip(), offset, offset + len(line)))
            offset += len(line) + 1
        groups = split_long(lines)
        conf = p.get("ocr_conf")
        low = p.get("n_low_conf_words") or 0
        words = p.get("n_words") or 0
        for part, (kind, group) in enumerate(groups, start=1):
            chunks.append({
                "chunk_id": f"{doc.doc_id}:p{p['page_number']}:{part}", "doc_id": doc.doc_id,
                "act_name": doc.act_name, "act_name_en": doc.act_name_en, "language": doc.language,
                "unit": "page", "section_number": str(p["page_number"]), "section_title": "", "chapter": "",
                "page_start": p["page_number"], "page_end": p["page_number"], "part": part, "parts_total": len(groups),
                "chunk_kind": "operative", "number_inferred": False, "text_source": p["source"],
                "ocr_conf": conf if conf is not None else -1.0,
                "low_quality": bool(conf is not None and (conf < 80 or (words and low / words > 0.25))),
                "text": "\n".join(g[0] for g in group),
            })
    return chunks


def build_chunks(doc: Document, pages: list[dict]) -> list[dict]:
    if doc.unit == "page":
        return build_page_chunks(doc, pages)
    # 1. one long text + a map from offsets to page numbers
    parts, page_starts, pos = [], [], 0
    for p in pages:
        cleaned = preprocess_page(p["text"], p["source"])
        page_starts.append(pos)
        parts.append(cleaned)
        pos += len(cleaned) + 1
    full = "\n".join(parts)

    def page_of(offset: int) -> dict:
        return pages[max(0, bisect.bisect_right(page_starts, offset) - 1)]

    # 2. boundaries
    profile = english_profile(doc.act_name_en) if doc.text_source == "ocr" else None
    events = select_body_events(find_events(full), full, profile)

    # 3. segment start (pull preceding bold heading lines into the section they belong to)
    def heading_start(pos: int) -> tuple[int, list[str]]:
        lines, cursor = [], pos
        for _ in range(MAX_TITLE_LINES):
            prev_end = cursor - 1
            if prev_end <= 0:
                break
            prev_start = full.rfind("\n", 0, prev_end) + 1
            line = full[prev_start:prev_end]
            if not line.startswith(BOLD_MARK):
                break
            lines.insert(0, line.lstrip(BOLD_MARK).strip())
            cursor = prev_start
        return cursor, lines

    chunks, chapter = [], ""
    segments = []
    for i, e in enumerate(events):
        if e["kind"] == "chapter":
            title_extra = ""
            nxt = full[full.find("\n", e["pos"]) + 1: full.find("\n", e["pos"]) + 150].split("\n")[0].lstrip(BOLD_MARK).strip()
            if nxt and nxt.upper() == nxt and len(nxt) < 100 and not SECTION_RE.match(nxt):
                title_extra = " — " + nxt
            chapter = e["label"] + title_extra
            segments.append({"kind": "chapter", "start": e["pos"]})
            continue
        if e["kind"] == "section":
            start, bold_lines = heading_start(e["pos"])
        else:
            start, bold_lines = e["pos"], []
        segments.append({"kind": e["kind"], "start": start, "pos": e["pos"], "event": e,
                         "bold_lines": bold_lines, "chapter": chapter})

    # a section ends where the next segment (of any kind) starts
    for i, seg in enumerate(segments):
        seg["end"] = segments[i + 1]["start"] if i + 1 < len(segments) else len(full)

    # 4. segment -> chunks
    for seg in segments:
        if seg["kind"] == "chapter":
            continue
        e = seg["event"]
        raw = full[seg["start"]:seg["end"]]
        paras = reflow(raw, seg["start"])
        if not paras:
            continue
        if seg["kind"] == "section":
            number, unit = e["num"], doc.unit
            after_number = SECTION_RE.sub("", full[e["pos"]:e["pos"] + 260], count=1)
            # "134. Title.—Body" (BNS, Constitution, IT Act), else BNSS style: bold lines before the number
            title = inline_title(after_number) or " ".join(seg["bold_lines"])
        else:
            number, unit, title = e["label"].title() if doc.language == "en" else e["label"], "schedule", ""
        key = re.sub(r"\W+", "", number).lower() or "x"
        groups = split_long(paras, classify(paras))
        for part, (chunk_kind, group) in enumerate(groups, start=1):
            first_page = page_of(group[0][1])
            last_page = page_of(max(group[-1][2] - 1, group[0][1]))
            span_pages = [p for p in pages if first_page["page_number"] <= p["page_number"] <= last_page["page_number"]]
            confs = [p["ocr_conf"] for p in span_pages if p.get("ocr_conf") is not None]
            low = sum(p.get("n_low_conf_words") or 0 for p in span_pages)
            words = sum(p.get("n_words") or 0 for p in span_pages)
            ocr_conf = round(sum(confs) / len(confs), 1) if confs else -1.0
            low_quality = bool(confs) and (ocr_conf < 80 or (words and low / words > 0.25))
            text = _clean_marks("\n".join(g[0] for g in group))
            chunks.append({
                "chunk_id": f"{doc.doc_id}:{key}:{part}",
                "doc_id": doc.doc_id,
                "act_name": doc.act_name,
                "act_name_en": doc.act_name_en,
                "language": doc.language,
                "unit": unit,
                "section_number": number,
                "section_title": title,
                "chapter": seg["chapter"],
                "page_start": first_page["page_number"],
                "page_end": last_page["page_number"],
                "part": part,
                "parts_total": len(groups),
                "chunk_kind": chunk_kind,
                "number_inferred": bool(e.get("inferred", False)),   # OCR garbled the heading; number taken from the sequence
                "text_source": first_page["source"],
                "ocr_conf": ocr_conf,
                "low_quality": low_quality,
                "text": text,
            })
    return chunks


def embedding_text(chunk: dict, doc: Document) -> str:
    """Text actually sent to the embedding model: a context header + the chunk text.

    The header repeats the Act and section so a query like "BNS section 103" or
    "murder punishment" matches even when the body text alone never says the Act name.
    """
    label = f"{unit_label(doc, chunk['unit'])} {chunk['section_number']}"
    header = f"{chunk['act_name']} | {label}"
    if chunk["section_title"]:
        header += f" | {chunk['section_title']}"
    return f"{header}\n{chunk['text']}"
