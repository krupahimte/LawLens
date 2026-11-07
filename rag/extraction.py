"""PDF text extraction.

Two sources of page text:
* ``text_layer`` - selectable text read directly from the PDF with PyMuPDF.
* ``ocr``        - text produced earlier by rag/ocr.py (JSON per page).

``load_pages`` hides that difference: it returns the same list of page dicts
for any document in the catalog.
"""
import json

import pymupdf

import config
from rag.catalog import Document

# Marker put at the start of lines that are entirely bold in the PDF. Legal
# headings are bold, and the chunker uses them to attach titles to the right
# section. It is stripped before any text is stored.
BOLD_MARK = "\x01"


def extract_text(pdf_path):
    """Plain page-by-page text (original function, kept as is)."""
    doc = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text("text")

        pages.append({
            "page_number": page_number,
            "text": text
        })

    doc.close()

    return pages


def _is_bold(span: dict) -> bool:
    return bool(span["flags"] & 16) or "bold" in span["font"].lower()


EMPTY_PAGE_CHARS = 30       # a page with fewer characters than this has no usable text layer
FOOTNOTE_SIZE_RATIO = 0.95  # lines set smaller than this fraction of the page's body font are footnotes


def _body_font_size(blocks: list[dict]) -> float:
    """The font size that carries the most characters on the page."""
    chars: dict[float, int] = {}
    for block in blocks:
        for line in block.get("lines", []):
            for s in line["spans"]:
                size = round(s["size"], 1)
                chars[size] = chars.get(size, 0) + len(s["text"].strip())
    return max(chars, key=chars.get) if chars else 0.0


def extract_text_marked(pdf_path) -> list[dict]:
    """Like extract_text, but prefixes fully-bold lines with BOLD_MARK and drops footnote lines.

    Footnotes are detected by font size (smaller than the page's body text), which is
    far more reliable than guessing from the words ("Subs. by ...").
    """
    pages = []
    with pymupdf.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            out_lines = []
            blocks = page.get_text("dict")["blocks"]
            body_size = _body_font_size(blocks)
            for block in blocks:
                for line in block.get("lines", []):
                    spans = [s for s in line["spans"] if s["text"].strip()]
                    if not spans:
                        continue
                    if max(s["size"] for s in spans) < body_size * FOOTNOTE_SIZE_RATIO:
                        continue  # footnote or tiny running text
                    text = "".join(s["text"] for s in line["spans"]).rstrip()
                    if all(_is_bold(s) for s in spans):
                        text = BOLD_MARK + text
                    out_lines.append(text)
            pages.append({"page_number": page_number, "text": "\n".join(out_lines)})
    return pages


def load_ocr_pages(doc: Document, total_pages: int) -> list[dict]:
    folder = config.OCR_DIR / doc.doc_id
    pages, missing = [], []
    for n in range(1, total_pages + 1):
        f = folder / f"page_{n:04d}.json"
        if not f.exists():
            missing.append(n)
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        pages.append({
            "page_number": n, "text": rec["text"], "source": "ocr",
            "ocr_conf": rec["mean_conf"], "n_words": rec["n_words"],
            "n_low_conf_words": rec["n_low_conf_words"],
        })
    if missing:
        raise RuntimeError(
            f"{doc.doc_id}: OCR incomplete, {len(missing)} pages missing "
            f"(e.g. {missing[:5]}). Run: python -m rag.ocr --doc {doc.doc_id}"
        )
    return pages


def load_pages(doc: Document) -> list[dict]:
    """Return [{page_number, text, source, ocr_conf, ...}] for one catalog document."""
    if doc.text_source == "text_layer":
        pages = [
            {**p, "source": "text_layer", "ocr_conf": None, "n_words": None, "n_low_conf_words": None}
            for p in extract_text_marked(doc.path)
        ]
        empty = sum(1 for p in pages if len(p["text"].strip()) < EMPTY_PAGE_CHARS)
        if pages and empty / len(pages) > 0.5:
            # A scanned PDF has no text layer: without this check it would be indexed as zero chunks, silently.
            raise RuntimeError(
                f"{doc.doc_id}: {empty} of {len(pages)} pages have no selectable text. This looks like a scanned "
                f"PDF; set text_source='ocr' in rag/catalog.py and run: python -m rag.ocr --doc {doc.doc_id}"
            )
        return pages
    with pymupdf.open(doc.path) as pdf:
        total = len(pdf)
    return load_ocr_pages(doc, total)
