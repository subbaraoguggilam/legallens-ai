from app.services.clauses import build_chunks
from app.services.extraction import ExtractedPage, extract_txt


def test_extract_txt_paginates_and_warns():
    result = extract_txt(b"line one\nline two\n")
    assert result.pages
    assert result.pages[0].number == 1
    assert "approximate" in result.warnings[0]


def test_build_chunks_assigns_clause_and_page():
    pages = [
        ExtractedPage(
            1,
            "EMPLOYMENT AGREEMENT\n"
            "This is made between Acme and Priya.\n"
            "8. NOTICE\n"
            "8.1 Either party may terminate by providing thirty (30) days written notice.\n"
            "9. Termination\n"
            "9.1 For cause.",
        ),
        ExtractedPage(2, "9.2 Immediate termination is permitted for gross misconduct."),
    ]
    chunks = build_chunks(pages)
    by_clause = {c.clause: c for c in chunks}

    assert "8.1" in by_clause
    assert by_clause["8.1"].section == "8. Notice"
    assert by_clause["8.1"].page_number == 1

    assert "9.2" in by_clause
    assert by_clause["9.2"].page_number == 2
    assert by_clause["9.2"].section == "9. Termination"

    # bare numbered headings ("8. NOTICE" alone) should not become their own chunk
    assert not any(c.clause == "8" and c.content.strip() == "8. NOTICE" for c in chunks)


def test_build_chunks_splits_long_clauses():
    long_text = "9.1 " + ("This is a very long clause sentence. " * 60)
    pages = [ExtractedPage(1, long_text)]
    chunks = build_chunks(pages)
    assert len(chunks) >= 2
    assert all(len(c.content) <= 1100 for c in chunks)
