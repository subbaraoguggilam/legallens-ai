"""Validate uploads: extension, MIME type, file signature, size and page count."""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass

from app.core.config import get_settings

ALLOWED = {
    "pdf": {"application/pdf"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",  # some browsers send this for .docx
    },
    "txt": {"text/plain"},
}


class UploadRejected(ValueError):
    """Raised with a user-safe message when an upload fails validation."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ValidatedUpload:
    filename: str
    ext: str
    data: bytes


_FILENAME_BAD = re.compile(r"[\x00-\x1f\x7f<>:\"|?*\\/]+")


def sanitize_filename(name: str | None) -> str:
    """Return a safe display name (no path components, control chars, or markup)."""
    base = (name or "document").replace("\\", "/").split("/")[-1]
    base = _FILENAME_BAD.sub("_", base).strip(" .")
    base = re.sub(r"\.{2,}", ".", base)
    return (base or "document")[:120]


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _looks_like_text(data: bytes) -> bool:
    if b"\x00" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def validate_upload(filename: str | None, content_type: str | None, data: bytes) -> ValidatedUpload:
    s = get_settings()
    safe_name = sanitize_filename(filename)
    ext = _extension(safe_name)

    if ext not in ALLOWED:
        raise UploadRejected("Unsupported file type. Upload a PDF, DOCX or TXT file.", 415)
    if not data:
        raise UploadRejected("The uploaded file is empty.")
    if len(data) > s.max_upload_bytes:
        raise UploadRejected(f"File is larger than the {s.max_upload_mb} MB limit.", 413)

    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype and ctype not in ALLOWED[ext]:
        raise UploadRejected("The file's declared type does not match its extension.", 415)

    # Signature checks: never trust the extension or client MIME type alone.
    if ext == "pdf":
        if b"%PDF-" not in data[:1024]:
            raise UploadRejected("File content is not a valid PDF.", 415)
    elif ext == "docx":
        if not data.startswith(b"PK\x03\x04"):
            raise UploadRejected("File content is not a valid DOCX.", 415)
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if "word/document.xml" not in z.namelist():
                    raise UploadRejected("File content is not a valid DOCX.", 415)
                # Zip-bomb guard: cap total uncompressed size.
                if sum(i.file_size for i in z.infolist()) > 200 * 1024 * 1024:
                    raise UploadRejected("DOCX expands to an unsafe size.", 413)
        except zipfile.BadZipFile as exc:
            raise UploadRejected("File content is not a valid DOCX.", 415) from exc
    else:
        if not _looks_like_text(data):
            raise UploadRejected("File content is not valid UTF-8 text.", 415)

    return ValidatedUpload(filename=safe_name, ext=ext, data=data)


def enforce_page_limit(page_count: int) -> None:
    limit = get_settings().max_pages
    if page_count > limit:
        raise UploadRejected(f"Document has {page_count} pages; the limit is {limit}.", 413)
