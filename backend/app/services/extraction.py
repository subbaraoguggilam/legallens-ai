"""Text extraction with page mapping: PDF (PyMuPDF + optional OCR), DOCX, TXT."""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import pymupdf

from app.core.config import get_settings
from app.services.upload_validation import UploadRejected, enforce_page_limit

TXT_PAGE_CHARS = 3200  # logical "page" size for plain text files


@dataclass
class ExtractedPage:
    number: int
    text: str
    used_ocr: bool = False


@dataclass
class ExtractionResult:
    pages: list[ExtractedPage]
    warnings: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)


def _ocr_page(page: pymupdf.Page) -> str | None:
    """OCR one page if pytesseract + the tesseract binary are available."""
    try:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception:
        return None


def extract_pdf(data: bytes) -> ExtractionResult:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise UploadRejected("The PDF could not be opened (it may be corrupt).", 422) from exc
    if doc.needs_pass:
        raise UploadRejected("Password-protected PDFs are not supported.", 422)
    enforce_page_limit(doc.page_count)

    pages: list[ExtractedPage] = []
    warnings: list[str] = []
    ocr_missing = False
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        used_ocr = False
        if len(text) < 20 and get_settings().ocr_enabled:
            ocr_text = _ocr_page(page)
            if ocr_text is None:
                ocr_missing = True
            elif ocr_text.strip():
                text, used_ocr = ocr_text.strip(), True
        pages.append(ExtractedPage(i, text, used_ocr))
    doc.close()

    if ocr_missing and any(len(p.text) < 20 for p in pages):
        warnings.append(
            "Some pages contain no selectable text and OCR is not available on this server; "
            "those pages could not be analysed."
        )
    if any(p.used_ocr for p in pages):
        warnings.append("Some pages were read with OCR; check the original for accuracy.")
    return ExtractionResult(pages, warnings)


def extract_docx(data: bytes) -> ExtractionResult:
    from docx import Document as DocxDocument
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        doc = DocxDocument(io.BytesIO(data))
    except Exception as exc:
        raise UploadRejected("The DOCX could not be opened (it may be corrupt).", 422) from exc

    pages: list[list[str]] = [[]]
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            para = Paragraph(child, doc)
            xml = child.xml
            if "w:lastRenderedPageBreak" in xml or 'w:type="page"' in xml:
                if pages[-1]:
                    pages.append([])
            if para.text.strip():
                pages[-1].append(para.text)
        elif tag == "tbl":
            table = Table(child, doc)
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    pages[-1].append(" | ".join(cells))
    result = [ExtractedPage(i, "\n".join(lines)) for i, lines in enumerate(pages, 1) if lines]
    enforce_page_limit(len(result))
    warnings = []
    if len(result) <= 1:
        warnings.append("DOCX page numbers are approximate; the file has no page-break markers.")
    return ExtractionResult(result or [ExtractedPage(1, "")], warnings)


def extract_txt(data: bytes) -> ExtractionResult:
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    pages: list[str] = []
    buf: list[str] = []
    size = 0
    for line in lines:
        buf.append(line)
        size += len(line) + 1
        if size >= TXT_PAGE_CHARS:
            pages.append("\n".join(buf))
            buf, size = [], 0
    if buf:
        pages.append("\n".join(buf))
    enforce_page_limit(len(pages))
    return ExtractionResult(
        [ExtractedPage(i, p.strip()) for i, p in enumerate(pages, 1)] or [ExtractedPage(1, "")],
        ["Plain-text files have approximate page numbers (about 3,200 characters per page)."],
    )


def extract(data: bytes, ext: str) -> ExtractionResult:
    if ext == "pdf":
        return extract_pdf(data)
    if ext == "docx":
        return extract_docx(data)
    return extract_txt(data)
