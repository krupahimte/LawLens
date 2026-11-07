"""Unit tests for chunking, cleaning and OCR parsing. No models or PDFs needed."""
from rag import catalog
from rag.chunking import (build_chunks, classify, embedding_text, find_events, inline_title, reflow,
                          select_body_events, split_long)
from rag.ocr import parse_tsv
from rag.preprocessing import normalize_unicode, preprocess_page

DOC = catalog.get("bns_en")

TOC = "SECTIONS\n1. Short title.\n2. Definitions.\n3. General explanations.\n"
BODY = (
    "CHAPTER I\nPRELIMINARY\n"
    "1. (1) This Sanhita may be called the Bharatiya Nyaya Sanhita, 2023. (2) It shall come into force on such date as "
    "the Central Government may appoint, and different dates may be appointed for different provisions of this Sanhita.\n"
    "2. Definitions.—In this Sanhita, unless the context otherwise requires, the word 'act' denotes as well a series of acts.\n"
    "CHAPTER II\nOF PUNISHMENTS\n"
    "3. General explanations.—Throughout this Sanhita every definition of an offence is to be understood subject to exceptions.\n"
    "Footnote junk: 2. This year\n"
    "4. Punishments.—The punishments to which offenders are liable are death, imprisonment for life, and fine.\n"
)


def pages_of(*texts):
    return [{"page_number": i + 1, "text": t, "source": "text_layer", "ocr_conf": None,
             "n_words": None, "n_low_conf_words": None} for i, t in enumerate(texts)]


def test_table_of_contents_is_skipped_and_sections_found():
    chunks = build_chunks(DOC, pages_of(TOC, BODY))
    numbers = [c["section_number"] for c in chunks]
    assert numbers == ["1", "2", "3", "4"]          # TOC entries not duplicated, false '2.' ignored
    assert chunks[0]["page_start"] == 2             # section 1 is on page 2, not the TOC page


def test_chapter_and_title_metadata():
    chunks = {c["section_number"]: c for c in build_chunks(DOC, pages_of(TOC, BODY))}
    assert chunks["2"]["section_title"] == "Definitions"
    assert chunks["3"]["chapter"].startswith("CHAPTER II")
    assert chunks["1"]["act_name"] == "Bharatiya Nyaya Sanhita, 2023"
    assert chunks["1"]["language"] == "en" and chunks["1"]["unit"] == "section"


def test_ordering_rejects_numbers_that_jump_backwards_or_too_far():
    text = "1. First section text that is long enough to count as the real start of the body of the Act, " * 3 + "\n2. Second.\n99. Wild jump\n3. Third.\n"
    events = select_body_events(find_events(text), text)
    assert [e["num"] for e in events if e["kind"] == "section"] == ["1", "2", "3"]


def test_inline_title_requires_a_real_heading():
    assert inline_title("Punishment for theft.—Whoever commits theft") == "Punishment for theft"
    assert inline_title("(1) Every report shall be made.—") == ""            # sub-clause is not a title
    assert inline_title("Primary evidence means the document. Explanation 1.—Where") == ""


def test_reflow_joins_wrapped_lines_but_keeps_clauses():
    paras = reflow("(1) first clause that\nwraps here;\n(2) second clause.", 0)
    assert [p[0] for p in paras] == ["(1) first clause that wraps here;", "(2) second clause."]


def test_long_sections_split_with_overlap(monkeypatch):
    import config
    monkeypatch.setattr(config, "MAX_CHUNK_CHARS", 120)
    monkeypatch.setattr(config, "CHUNK_OVERLAP_CHARS", 60)
    paras = [(f"({i}) " + "word " * 8, i * 100, i * 100 + 50) for i in range(1, 7)]
    groups = split_long(paras)
    assert len(groups) > 1
    assert groups[1][1][0] == groups[0][1][-1]      # last paragraph repeated as overlap


def test_illustrations_are_separated_from_operative_text_in_long_sections(monkeypatch):
    import config
    monkeypatch.setattr(config, "MAX_CHUNK_CHARS", 420)   # total text > 420 so it must split; each kind fits one chunk
    texts = ["303. Theft.—(1) Whoever takes property dishonestly commits theft.", "Illustrations",
             "(a) A takes Z's watch from Z's table, dishonestly. " * 3, "(b) A, a servant, runs away with the plate. " * 3,
             "(2) Whoever commits theft shall be punished with imprisonment up to three years, or fine, or both."]
    paras = [(t, i * 1000, i * 1000 + len(t)) for i, t in enumerate(texts)]
    kinds = classify(paras)
    assert kinds == ["operative", "illustration", "illustration", "illustration", "operative"]
    groups = split_long(paras, kinds)
    assert [k for k, _ in groups] == ["operative", "illustration", "operative"]
    assert "punished with imprisonment" in groups[-1][1][0][0]      # punishment clause is its own chunk


def test_short_section_with_illustration_stays_whole():
    paras = [("5. Short rule.—Do not.", 0, 20), ("Illustration", 21, 33), ("(a) A does it.", 34, 48)]
    groups = split_long(paras, classify(paras))
    assert len(groups) == 1 and groups[0][0] == "operative"


def test_embedding_text_carries_act_and_section():
    chunk = build_chunks(DOC, pages_of(TOC, BODY))[1]
    header = embedding_text(chunk, DOC).splitlines()[0]
    assert "Bharatiya Nyaya Sanhita, 2023" in header and "Section 2" in header


def test_hindi_digits_and_junk_are_normalised():
    assert normalize_unicode("धारा १०३­") == "धारा 103"
    assert "" not in normalize_unicode("1[370. Temporary")


def test_ocr_digit_confusion_repaired_only_at_line_start_and_only_for_ocr():
    from rag.preprocessing import repair_ocr_digits
    text = "2i. सिविल मामलों में\ni0i. ऐसी लिपि\ni. जहां कि\n4i3. जब प्रश्न\nइस धारा i34 के अधीन\nI. यह सूची"
    fixed = repair_ocr_digits(text).split("\n")
    assert fixed[:4] == ["21. सिविल मामलों में", "101. ऐसी लिपि", "1. जहां कि", "413. जब प्रश्न"]
    assert fixed[4] == "इस धारा i34 के अधीन"          # digits inside a sentence are never touched
    assert fixed[5] == "I. यह सूची"                     # a lone capital I is a bullet, not '1'
    assert preprocess_page("2i. text here", "text_layer") == "2i. text here"   # text-layer PDFs untouched
    assert preprocess_page("2i. text here", "ocr") == "21. text here"


def test_page_furniture_removed():
    page = "P a g e | 101\nIndiaCode\n134. Assault.—Whoever assaults\n42\n"
    assert preprocess_page(page) == "134. Assault.—Whoever assaults"


def test_parse_tsv_extracts_text_and_confidence():
    header = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
    rows = ["5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t95.0\tधारा", "5\t1\t1\t1\t1\t2\t0\t0\t1\t1\t40.0\t34.",
            "5\t1\t1\t1\t2\t1\t0\t0\t1\t1\t90.0\tकिसी", "4\t1\t1\t1\t2\t0\t0\t0\t1\t1\t-1\t"]
    text, mean, n_words, n_low = parse_tsv("\n".join([header, *rows]))
    assert text == "धारा 34.\nकिसी"
    assert (n_words, n_low) == (3, 1) and round(mean, 1) == 75.0
