import pytest

from app.services.upload_validation import UploadRejected, sanitize_filename, validate_upload


def test_sanitize_filename_strips_path_and_control_chars():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("my report.pdf") == "my report.pdf"
    assert sanitize_filename(None) == "document"


def test_rejects_unsupported_extension():
    with pytest.raises(UploadRejected):
        validate_upload("virus.exe", "application/octet-stream", b"MZ\x90\x00")


def test_rejects_pdf_without_signature():
    with pytest.raises(UploadRejected):
        validate_upload("fake.pdf", "application/pdf", b"not a real pdf")


def test_rejects_docx_without_zip_signature():
    with pytest.raises(UploadRejected):
        validate_upload("fake.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"not a zip")


def test_rejects_empty_file():
    with pytest.raises(UploadRejected):
        validate_upload("empty.txt", "text/plain", b"")


def test_rejects_oversized_file(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    get_settings.cache_clear()
    with pytest.raises(UploadRejected):
        validate_upload("big.txt", "text/plain", b"hello world")
    get_settings.cache_clear()


def test_accepts_valid_pdf_signature():
    data = b"%PDF-1.4\n%mock pdf content"
    result = validate_upload("contract.pdf", "application/pdf", data)
    assert result.ext == "pdf"
    assert result.filename == "contract.pdf"


def test_mismatched_content_type_rejected():
    with pytest.raises(UploadRejected):
        validate_upload("contract.pdf", "image/png", b"%PDF-1.4\ncontent")
