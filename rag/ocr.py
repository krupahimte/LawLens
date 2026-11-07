"""OCR for Hindi PDFs whose text layer is missing or corrupted.

Pipeline per page:  PDF page -> grayscale PNG (PyMuPDF) -> Tesseract (hin+eng, TSV)
                    -> text + per-word confidence -> data/ocr/<doc_id>/page_NNNN.json

Design points:
* Original PDFs are only read, never written.
* One JSON file per page => the job is resumable (finished pages are skipped).
* Confidence is stored with the text so later stages can flag uncertain pages.

Usage (from project root):
    python -m rag.ocr                      # all OCR documents
    python -m rag.ocr --doc bsa_hi         # one document
    python -m rag.ocr --doc bsa_hi --pages 1-5
"""
import argparse
import json
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf

import config
from rag import catalog

_local = threading.local()  # PyMuPDF documents are not thread-safe: one per thread

OCR_ENGINE = "tesseract"


def _get_doc(pdf_path: str) -> pymupdf.Document:
    cache = getattr(_local, "docs", None)
    if cache is None:
        cache = _local.docs = {}
    if pdf_path not in cache:
        cache[pdf_path] = pymupdf.open(pdf_path)
    return cache[pdf_path]


def _run_tesseract(png_bytes: bytes) -> str:
    env = dict(os.environ, TESSDATA_PREFIX=str(config.TESSDATA_DIR), OMP_THREAD_LIMIT="1")
    result = subprocess.run(
        [config.TESSERACT_CMD, "stdin", "stdout", "-l", "hin+eng", "tsv"],
        input=png_bytes, capture_output=True, env=env, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"tesseract failed: {result.stderr.decode('utf-8', 'replace')[:300]}")
    return result.stdout.decode("utf-8", "replace")


def parse_tsv(tsv: str) -> tuple[str, float, int, int]:
    """Turn Tesseract TSV into (text, mean_conf, n_words, n_low_conf_words)."""
    lines: dict[tuple, list[str]] = {}
    confs: list[float] = []
    low = 0
    for row in tsv.splitlines()[1:]:
        cols = row.split("\t")
        if len(cols) < 12:
            continue
        conf, word = float(cols[10]), cols[11].strip()
        if conf < 0 or not word:
            continue
        confs.append(conf)
        if conf < 60:
            low += 1
        key = (cols[2], cols[3], cols[4])  # block, paragraph, line
        lines.setdefault(key, []).append(word)
    text_lines, last_par = [], None
    for key, words in lines.items():
        par = key[:2]
        if last_par is not None and par != last_par:
            text_lines.append("")  # blank line between paragraphs
        text_lines.append(" ".join(words))
        last_par = par
    mean_conf = round(sum(confs) / len(confs), 1) if confs else 0.0
    return "\n".join(text_lines), mean_conf, len(confs), low


def page_file(doc_id: str, page_number: int):
    return config.OCR_DIR / doc_id / f"page_{page_number:04d}.json"


def ocr_page(doc_id: str, page_number: int) -> dict:
    doc = catalog.get(doc_id)
    pdf = _get_doc(str(doc.path))
    pix = pdf[page_number - 1].get_pixmap(dpi=config.OCR_DPI, colorspace=pymupdf.csGRAY)
    tsv = _run_tesseract(pix.tobytes("png"))
    text, mean_conf, n_words, n_low = parse_tsv(tsv)
    record = {
        "doc_id": doc_id, "page": page_number, "text": text,
        "mean_conf": mean_conf, "n_words": n_words, "n_low_conf_words": n_low,
        "engine": OCR_ENGINE, "lang": "hin+eng", "dpi": config.OCR_DPI,
    }
    out = page_file(doc_id, page_number)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    return record


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    start, _, end = spec.partition("-")
    return list(range(int(start), int(end or start) + 1))


def ocr_document(doc_id: str, pages_spec: str | None = None, workers: int | None = None) -> None:
    doc = catalog.get(doc_id)
    with pymupdf.open(doc.path) as pdf:
        total = len(pdf)
    pages = [p for p in parse_pages(pages_spec, total) if not page_file(doc_id, p).exists()]
    print(f"[{doc_id}] {total} pages, {len(pages)} to OCR", flush=True)
    if not pages:
        return
    start, done = time.time(), 0
    with ThreadPoolExecutor(max_workers=workers or config.OCR_WORKERS) as pool:
        futures = {pool.submit(ocr_page, doc_id, p): p for p in pages}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as exc:  # keep going; failed pages are retried on next run
                print(f"[{doc_id}] page {futures[fut]} FAILED: {exc}", flush=True)
            done += 1
            if done % 20 == 0 or done == len(pages):
                rate = done / (time.time() - start)
                print(f"[{doc_id}] {done}/{len(pages)} pages ({rate:.2f} pages/s)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR Hindi PDFs with Tesseract")
    parser.add_argument("--doc", help="doc_id from rag/catalog.py (default: all OCR docs)")
    parser.add_argument("--pages", help="page range like 1-5 (1-based)")
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()
    targets = [args.doc] if args.doc else [d.doc_id for d in catalog.DOCUMENTS if d.text_source == "ocr"]
    for doc_id in targets:
        ocr_document(doc_id, args.pages, args.workers)


if __name__ == "__main__":
    main()
