"""Text cleaning.

``clean_text`` is the original whitespace cleaner (unchanged). The rest adds
Unicode normalisation and removal of page furniture (running headers, footers,
page numbers, footnote blocks) that would otherwise pollute chunks and
embeddings.
"""
import re
import unicodedata

from rag.extraction import BOLD_MARK


def clean_text(text):

    text = re.sub(r'[ \t]+', ' ', text)

    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_unicode(text: str) -> str:
    """NFC-normalise, map Devanagari digits to ASCII, drop invisible junk."""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_DEVANAGARI_DIGITS)
    text = re.sub(r"[-]", "", text)  # Symbol-font glyphs (e.g. footnote asterisks)
    for junk in ("­", "﻿", "​", "\r", "\x0c"):
        text = text.replace(junk, "")
    return text.replace(" ", " ")


# Whole lines that are running headers/footers, matched after stripping the bold mark.
_FURNITURE_LINES = [
    re.compile(r"^P\s*a\s*g\s*e\s*\|\s*\d+\s*$"),            # "P a g e | 101"
    re.compile(r"^\s*IndiaCode\s*$"),                          # footer on India Code PDFs
    re.compile(r"^SEC\.\s*\d+\]\s*$"),                         # "SEC. 1]"
    re.compile(r"^THE GAZETTE OF INDIA EXTRAORDINARY\s*$"),
    re.compile(r"^\[?\s*PART\s+II\s*[-—–]\s*SEC.*$"),
    re.compile(r"^\s*\d{1,3}\s*$"),                            # bare page number
    re.compile(r"^\s*\([ivxl]{2,6}\)\s*$"),                    # roman page number "(viii)"
    re.compile(r"^भारत का राजपत्र.*$"),
    re.compile(r"^.{0,4}\s*पुस्तिका.{0,12}अकादमी\s*$"),         # running header of the Delhi Police booklet
]

# Footnotes are removed earlier, by font size, in rag/extraction.py.


def strip_page_furniture(text: str) -> str:
    kept = []
    for line in text.split("\n"):
        bare = line.lstrip(BOLD_MARK).strip()
        if any(p.match(bare) for p in _FURNITURE_LINES):
            continue
        kept.append(line)
    return "\n".join(kept)


# Tesseract's Hindi model reads the digit 1 as the letter 'i' (and sometimes '+', 'l', '|') in section
# numbers: "21." -> "2i.", "101." -> "i0i.", "134." -> "i34.". Only the number token at the START of a
# line is repaired, never digits inside sentences, and the stored raw OCR files are left untouched.
_OCR_NUMBER_AT_LINE_START = re.compile(r"(?m)^([ \t]*)([0-9iIl|+]{1,4})(?=[A-Z]{0,2}\.[ \t]+\S)")


def repair_ocr_digits(text: str) -> str:
    def fix(m: re.Match) -> str:
        token = m.group(2)
        if not re.search(r"[iIl|+]", token):
            return m.group(0)
        if re.fullmatch(r"[iIl|+]+", token) and token != "i":   # 'I.' 'l.' alone are bullets, not numbers
            return m.group(0)
        return m.group(1) + re.sub(r"[iIl|+]", "1", token)
    return _OCR_NUMBER_AT_LINE_START.sub(fix, text)


def preprocess_page(text: str, source: str = "text_layer") -> str:
    """Full per-page cleaning. Bold markers are kept for the chunker."""
    text = normalize_unicode(text)
    if source == "ocr":
        text = repair_ocr_digits(text)
    return clean_text(strip_page_furniture(text))
