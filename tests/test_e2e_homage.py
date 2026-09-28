from pathlib import Path
from epub_parser import extract_epub_chapters
from nlp_stats import analyze_text_style


def test_extract_user_epubs():
    base_dir = Path("d:/01_Career/novel_prj")
    epub1 = list(base_dir.glob("*광마회귀*.epub"))[0]
    epub2 = list(base_dir.glob("*달러구트*.epub"))[0]

    assert epub1.exists(), f"EPUB not found: {epub1}"
    assert epub2.exists(), f"EPUB not found: {epub2}"

    # Test extracting from Gwangma
    chapters1 = extract_epub_chapters(epub1)
    assert len(chapters1) > 0, "No chapters extracted from 광마회귀"
    long_chapters1 = [c for c in chapters1 if len(c["text"]) > 200]
    assert len(long_chapters1) > 0
    assert len(long_chapters1[0]["text"]) > 200

    stats1 = analyze_text_style(long_chapters1[0]["text"], lang="ko")
    assert stats1["sentence_count"] > 5
    assert stats1["avg_sentence_len"] > 0

    # Test extracting from Dallergut
    chapters2 = extract_epub_chapters(epub2)
    assert len(chapters2) > 0, "No chapters extracted from 달러구트"
    long_chapters2 = [c for c in chapters2 if len(c["text"]) > 200]
    assert len(long_chapters2) > 0
    assert len(long_chapters2[0]["text"]) > 200

    stats2 = analyze_text_style(long_chapters2[0]["text"], lang="ko")
    assert stats2["sentence_count"] > 5
    assert stats2["avg_sentence_len"] > 0
