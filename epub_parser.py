"""
epub_parser.py — Lightweight, pure-standard-library EPUB and TXT text extractor.
"""
import html
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def clean_html_text(raw_html: str) -> str:
    """Strips HTML tags, decodes entities, and normalizes whitespace."""
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    # Collapse multiple blank lines into at most two
    cleaned = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()
    return cleaned


def extract_epub_chapters(epub_path: str | Path) -> list[dict]:
    """
    Extracts ordered chapter contents from an EPUB or TXT file.
    Returns list of dict: [{"index": int, "title": str, "text": str}]
    """
    path = Path(epub_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Fallback if raw txt
    if path.suffix.lower() == ".txt":
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        return [{"index": 1, "title": path.stem, "text": raw_text.strip()}]

    chapters = []
    with zipfile.ZipFile(path, "r") as z:
        # Find OPF path via container.xml
        try:
            container_xml = z.read("META-INF/container.xml")
            root = ET.fromstring(container_xml)
            ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//c:rootfile", ns)
            opf_path = rootfile.attrib["full-path"] if rootfile is not None else "content.opf"
        except Exception:
            opf_path = None
            for name in z.namelist():
                if name.endswith(".opf"):
                    opf_path = name
                    break

        if opf_path and opf_path in z.namelist():
            opf_dir = Path(opf_path).parent
            opf_xml = z.read(opf_path)
            opf_root = ET.fromstring(opf_xml)

            # Map id to href in manifest
            manifest = {}
            for item in opf_root.findall(".//{*}item"):
                item_id = item.attrib.get("id")
                href = item.attrib.get("href")
                media_type = item.attrib.get("media-type", "")
                if item_id and href and ("html" in media_type or href.endswith((".html", ".xhtml", ".xml"))):
                    target_path = (opf_dir / href).as_posix() if str(opf_dir) != "." else href
                    manifest[item_id] = target_path

            # Read spine order
            spine_ids = [item.attrib.get("idref") for item in opf_root.findall(".//{*}itemref")]
            chapter_files = [manifest[sid] for sid in spine_ids if sid in manifest]
        else:
            # Fallback: scan all html/xhtml files sorted
            chapter_files = sorted(
                [n for n in z.namelist() if n.endswith((".xhtml", ".html", ".htm")) and not n.startswith("toc")]
            )

        idx = 1
        for fpath in chapter_files:
            try:
                content = z.read(fpath).decode("utf-8", errors="ignore")
                cleaned = clean_html_text(content)
                if len(cleaned) > 10:  # Skip trivial/empty navigation stubs
                    chapters.append({"index": idx, "title": Path(fpath).stem, "text": cleaned})
                    idx += 1
            except Exception:
                continue

    return chapters
