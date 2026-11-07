"""Catalog of the source PDFs and their metadata.

One entry per PDF. English and Hindi files are kept as separate documents:
they may be different editions, so they are never merged.
"""
from dataclasses import dataclass
from pathlib import Path

import config
from config import RAW_DIR


@dataclass(frozen=True)
class Document:
    doc_id: str          # unique id, used in chunk ids and OCR folders
    filename: str        # file inside data/raw
    act_name: str        # official name in the document's own language
    act_name_en: str     # English name (for display in either language)
    language: str        # "en" or "hi"
    unit: str            # "section" or "article"
    text_source: str     # "text_layer" (selectable text) or "ocr"
    edition_note: str    # what we know/don't know about this edition

    @property
    def path(self) -> Path:
        return RAW_DIR / self.filename


def _doc(doc_id, filename, act_hi_or_en, act_en, language, unit, text_source, note):
    return Document(doc_id, filename, act_hi_or_en, act_en, language, unit, text_source, note)


DOCUMENTS: list[Document] = [
    # ---------------- English: all have a clean selectable text layer ----------------
    _doc("bns_en", "bns_english.pdf", "Bharatiya Nyaya Sanhita, 2023", "Bharatiya Nyaya Sanhita, 2023",
         "en", "section", "text_layer", "Word-generated PDF, created 2025-11-07."),
    _doc("bnss_en", "bnss_english.pdf", "Bharatiya Nagarik Suraksha Sanhita, 2023", "Bharatiya Nagarik Suraksha Sanhita, 2023",
         "en", "section", "text_layer", "NCRB copy, created 2024-02-12."),
    _doc("bsa_en", "bsa_english.pdf", "Bharatiya Sakshya Adhiniyam, 2023", "Bharatiya Sakshya Adhiniyam, 2023",
         "en", "section", "text_layer", "Gazette copy, created 2023-08-11."),
    _doc("constitution_en", "constitution_ofindia_english.pdf", "The Constitution of India", "The Constitution of India",
         "en", "article", "text_layer", "PDF titled '20 MAY 2026 (final)'. Verify amendment status."),
    _doc("cp_en", "cp_english.pdf", "The Consumer Protection Act, 2019", "The Consumer Protection Act, 2019",
         "en", "section", "text_layer", "Gazette Extraordinary copy, created 2019-08-09."),
    _doc("it_en", "it_act_english.pdf", "The Information Technology Act, 2000", "The Information Technology Act, 2000",
         "en", "section", "text_layer", "Includes 2008 amendments; PDF created 2018-11-05."),
    # ---------------- Hindi: text layers are broken or absent -> OCR ----------------
    # NOT the Hindi text of the Act: a Delhi Police Academy quick-reference booklet (introduction, IPC-to-BNS
    # comparison and classification tables, partial section text with unreliable OCR numbering).
    # Indexed per booklet page ("page" unit) and cited as such, never as an official section text.
    _doc("bns_hi", "bns_hindi.pdf", "भारतीय न्याय संहिता, 2023 (दिल्ली पुलिस अकादमी पुस्तिका)", "Bharatiya Nyaya Sanhita, 2023",
         "hi", "page", "ocr",
         "Delhi Police Academy booklet (2024-06), not the Act text. Text layer has doubled matras so it is OCRed. "
         "Mostly IPC-to-BNS comparison and classification tables; indexed and cited by booklet page."),
    # Low-resolution scan (593x841 px per page): OCR ~73% and headings unreliable -> indexed per page.
    _doc("bnss_hi", "bnss_hindi.pdf", "भारतीय नागरिक सुरक्षा संहिता, 2023", "Bharatiya Nagarik Suraksha Sanhita, 2023",
         "hi", "page", "ocr",
         "Low-resolution scanned image PDF (2023-07/08); OCR confidence ~73%, so chunks are flagged low quality "
         "and never quoted. Indexed per page because section headings cannot be read reliably."),
    _doc("bsa_hi", "bsa_hindi.pdf", "भारतीय साक्ष्य अधिनियम, 2023", "Bharatiya Sakshya Adhiniyam, 2023",
         "hi", "section", "ocr",
         "Scanned image PDF (593x841 px); no text layer. The OCR'd front page reads 'भारतीय साक्ष्य विधेयक, 2023', "
         "so this is the Bill as introduced, not the enacted Act: numbering may differ from the English Act."),
    # Article headings are not reliably readable from the OCR (the detector locked onto Schedule text), so
    # this document is indexed per page. Exact "Article N" lookups use the English Constitution.
    _doc("constitution_hi", "constitution_ofindia_hindi.pdf", "भारत का संविधान", "The Constitution of India",
         "hi", "page", "ocr",
         "Legacy font encoding makes the text layer unreadable, so it is OCRed. Indexed and cited by PDF page."),
    _doc("cp_hi", "cp_hindi.pdf", "उपभोक्ता संरक्षण अधिनियम, 2019", "The Consumer Protection Act, 2019",
         "hi", "section", "ocr",
         "Scanned image PDF (2019-07); no text layer. OCR'd front page reads 'उपभोक्ता संरक्षण विधेयक, 2019' (Bill "
         "text, not the gazetted Act); clause count matches the Act (107) but wording may differ."),
    _doc("it_hi", "it_act_hindi.pdf", "सूचना प्रौद्योगिकी अधिनियम, 2000", "The Information Technology Act, 2000",
         "hi", "section", "ocr",
         "PDF created 2016-05; text layer uses legacy glyph order (i-matra before consonant) so it is OCRed. "
         "Likely an older edition than the English copy (2018)."),
]

BY_ID: dict[str, Document] = {d.doc_id: d for d in DOCUMENTS}


def active_documents() -> list[Document]:
    """Documents that take part in ingestion and retrieval: English only unless ENABLE_HINDI is on."""
    return [d for d in DOCUMENTS if config.ENABLE_HINDI or d.language == "en"]


def get(doc_id: str) -> Document:
    return BY_ID[doc_id]
