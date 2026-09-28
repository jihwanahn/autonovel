import zipfile
import pytest
from pathlib import Path
from epub_parser import extract_epub_chapters, clean_html_text


def test_clean_html_text():
    raw_html = "<p>첫 번째 문장입니다.&nbsp;이것은 테스트입니다.</p><p>두 번째 문장.</p>"
    cleaned = clean_html_text(raw_html)
    assert "첫 번째 문장입니다." in cleaned
    assert "두 번째 문장." in cleaned
    assert "<p>" not in cleaned
    assert "&nbsp;" not in cleaned


def test_extract_epub_dummy(tmp_path):
    epub_file = tmp_path / "test.epub"
    with zipfile.ZipFile(epub_file, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        z.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="c1"/>
  </spine>
</package>""",
        )
        z.writestr(
            "OEBPS/ch1.xhtml",
            "<html><body><h1>제1장 시작</h1><p>이야기가 시작된다.</p></body></html>",
        )

    chapters = extract_epub_chapters(epub_file)
    assert len(chapters) == 1
    assert "제1장 시작" in chapters[0]["text"]
    assert "이야기가 시작된다." in chapters[0]["text"]
