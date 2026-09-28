# Reference-Driven Homage Novel System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve `autonovel` into a modular, reference-driven novel deconstruction and homage pipeline supporting Korean and English literature while generalizing hardcoded legacy dependencies.

**Architecture:** Pure Python EPUB parser extracts clean text from published works; a quantitative and LLM-driven analyzer deconstructs reference works into modular DNA profiles (`references/<name>/`); a seed synthesizer cross-pollinates multiple DNAs to produce original homage concepts; foundation and drafting scripts are generalized to bind dynamically to project assets.

**Tech Stack:** Python 3.12, `httpx`, `pytest`, standard library (`zipfile`, `html.parser`, `re`, `json`, `pathlib`), Anthropic / Antigravity proxy API.

**Spec:** [docs/superpowers/specs/2026-09-28-reference-homage-novel-system-design.md](file:///d:/01_Career/novel_prj/autonovel/docs/superpowers/specs/2026-09-28-reference-homage-novel-system-design.md)

## Global Constraints

- Never hardcode novel titles, character names, or world laws in generation or evaluation scripts.
- Support both Korean (`ko`) and English (`en`) targets cleanly with native phrasing and no translationese.
- Use cross-platform `Path(__file__).parent` instead of hardcoded `/home/jeffq` or Windows-specific absolute paths.
- Enforce Safe Abstraction to eliminate plagiarism risks (no identical proper nouns, locations, or incident chains).

---

### Task 1: Environment Setup & Pure-Python EPUB Parser (`epub_parser.py`)

**Files:**
- Create: `epub_parser.py`
- Create: `tests/test_epub_parser.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: Path to `.epub` or `.txt` file.
- Produces: `extract_epub_chapters(epub_path: str | Path) -> list[dict]` where each dict is `{"index": int, "title": str, "text": str}`.

- [ ] **Step 1: Add pytest to project dependencies**

Run: `uv add --dev pytest`

- [ ] **Step 2: Write failing test for EPUB parser**

Create `tests/test_epub_parser.py`:
```python
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
        z.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
        z.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="c1"/>
  </spine>
</package>""")
        z.writestr("OEBPS/ch1.xhtml", "<html><body><h1>제1장 시작</h1><p>이야기가 시작된다.</p></body></html>")

    chapters = extract_epub_chapters(epub_file)
    assert len(chapters) == 1
    assert "제1장 시작" in chapters[0]["text"]
    assert "이야기가 시작된다." in chapters[0]["text"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_epub_parser.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'epub_parser'`

- [ ] **Step 4: Implement `epub_parser.py`**

Create `epub_parser.py`:
```python
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
    Extracts ordered chapter contents from an EPUB file.
    Returns list of dict: [{"index": int, "title": str, "text": str}]
    """
    path = Path(epub_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Fallback if raw txt
    if path.suffix.lower() == ".txt":
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        # Split on common chapter indicators or return full text as chapter 1
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
                    manifest[item_id] = str((opf_dir / href).as_posix()) if str(opf_dir) != "." else href

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
                if len(cleaned) > 80:  # Skip trivial/empty navigation stubs
                    chapters.append({"index": idx, "title": Path(fpath).stem, "text": cleaned})
                    idx += 1
            except Exception:
                continue

    return chapters
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_epub_parser.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

Run:
```bash
git add pyproject.toml uv.lock epub_parser.py tests/test_epub_parser.py
git commit -m "feat: add pure-standard-library epub and text parser"
```

---

### Task 2: Quantitative Style Analyzer (`nlp_stats.py`)

**Files:**
- Create: `nlp_stats.py`
- Create: `tests/test_nlp_stats.py`

**Interfaces:**
- Consumes: Text string (Korean or English).
- Produces: `analyze_text_style(text: str, lang: str = "ko") -> dict` returning metrics:
  - `avg_sentence_len`, `std_sentence_len`, `dialogue_ratio`, `sensory_density`, `top_vocabulary_clusters`.

- [ ] **Step 1: Write failing test for `nlp_stats.py`**

Create `tests/test_nlp_stats.py`:
```python
from nlp_stats import analyze_text_style

def test_analyze_text_style_korean():
    sample_text = """
    "네가 정말 그 일을 할 수 있겠느냐?" 노인이 차가운 목소리로 물었다.
    청년은 주먹을 쥐었다. 손바닥에 서늘한 땀이 맺혔다.
    "해보지 않고는 모릅니다."
    바람이 불어와 대나무 숲을 흔들었다. 심장이 빠르게 뛰기 시작했다.
    """
    stats = analyze_text_style(sample_text, lang="ko")
    assert stats["sentence_count"] >= 4
    assert 10 <= stats["avg_sentence_len"] <= 40
    assert 0.2 <= stats["dialogue_ratio"] <= 0.7
    assert "sensory_keywords" in stats
    assert len(stats["top_vocabulary_clusters"]) > 0

def test_analyze_text_style_english():
    sample_text = """
    "Are you certain of this?" the elder whispered.
    The boy tightened his grip on the bronze hilt. The cold metal bit into his skin.
    He stepped into the shadows without another word.
    """
    stats = analyze_text_style(sample_text, lang="en")
    assert stats["sentence_count"] >= 3
    assert stats["dialogue_ratio"] > 0.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nlp_stats.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'nlp_stats'`

- [ ] **Step 3: Implement `nlp_stats.py`**

Create `nlp_stats.py`:
```python
"""
nlp_stats.py — Quantitative prose and stylistic metrics calculator for Korean & English.
"""
import re
import statistics
from collections import Counter

SENSORY_LEXICON_KO = {
    "visual": ["빛", "어둠", "그림자", "붉은", "검은", "하얀", "푸른", "반짝", "눈빛", "형체"],
    "auditory": ["소리", "울림", "속삭", "비명", "정적", "바람", "쇠소리", "헐떡", "목소리"],
    "tactile": ["차가운", "서늘", "뜨거운", "온기", "손바닥", "살결", "거친", "압박", "통증", "땀"],
    "action": ["베다", "쥐다", "달리다", "딛다", "휘두르다", "멈추다", "부딪히다", "떨어지다"],
}

SENSORY_LEXICON_EN = {
    "visual": ["light", "dark", "shadow", "red", "black", "white", "blue", "gleam", "glance"],
    "auditory": ["sound", "whisper", "echo", "scream", "silence", "rattle", "hum", "voice"],
    "tactile": ["cold", "hot", "warmth", "skin", "sharp", "rough", "ache", "tremor", "sweat"],
    "action": ["strike", "grip", "run", "fall", "shatter", "step", "clash", "breathe"],
}


def analyze_text_style(text: str, lang: str = "ko") -> dict:
    cleaned = text.strip()
    if not cleaned:
        return {
            "sentence_count": 0, "avg_sentence_len": 0, "std_sentence_len": 0,
            "dialogue_ratio": 0.0, "sensory_density": 0.0, "top_vocabulary_clusters": []
        }

    # Extract dialogue (quotes: "..." or 「...」 or 『...』)
    dialogue_matches = re.findall(r'["“「『](.*?)["”」』]', cleaned)
    dialogue_chars = sum(len(m) for m in dialogue_matches)
    total_chars = max(len(cleaned), 1)
    dialogue_ratio = round(dialogue_chars / total_chars, 3)

    # Sentence segmentation
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', cleaned) if len(s.strip()) > 3]
    if not sentences:
        sentences = [cleaned]

    lengths = [len(s) for s in sentences]
    avg_len = round(statistics.mean(lengths), 1)
    std_len = round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0.0

    # Sensory analysis
    lexicon = SENSORY_LEXICON_KO if lang == "ko" else SENSORY_LEXICON_EN
    sensory_hits = Counter()
    for category, words in lexicon.items():
        for word in words:
            count = len(re.findall(re.escape(word), cleaned, flags=re.IGNORECASE))
            if count > 0:
                sensory_hits[category] += count

    total_sensory = sum(sensory_hits.values())
    sensory_density = round(total_sensory / (len(cleaned) / 1000), 2)  # per 1000 chars

    # Vocabulary clusters: significant content words (>2 chars, frequency >= 2)
    words = re.findall(r'[가-힣a-zA-Z]{2,}', cleaned)
    stop_words = {"있는", "것은", "그의", "그녀", "하지만", "그리고", "때문", "있다", "했다", "that", "this", "with", "from"}
    filtered_words = [w for w in words if w not in stop_words]
    word_counts = Counter(filtered_words).most_common(15)

    return {
        "sentence_count": len(sentences),
        "avg_sentence_len": avg_len,
        "std_sentence_len": std_len,
        "dialogue_ratio": dialogue_ratio,
        "sensory_density": sensory_density,
        "sensory_keywords": dict(sensory_hits),
        "top_vocabulary_clusters": [w for w, _ in word_counts[:8]],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_nlp_stats.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add nlp_stats.py tests/test_nlp_stats.py
git commit -m "feat: add quantitative nlp style analyzer for korean and english"
```

---

### Task 3: Reference Deconstruction Engine (`analyze_reference.py`)

**Files:**
- Create: `analyze_reference.py`
- Create: `tests/test_analyze_reference.py`

**Interfaces:**
- Consumes: `--name`, `--input` (epub or txt), `--lang` (ko|en), optional `--mock`.
- Produces: `references/<name>/` containing:
  - `summary.md`
  - `voice_dna.json`
  - `plot_dna.json`
  - `entertainment_dna.md`

- [ ] **Step 1: Write failing test for reference analysis**

Create `tests/test_analyze_reference.py`:
```python
import json
import pytest
from pathlib import Path
from analyze_reference import run_analysis

def test_run_analysis_mock(tmp_path):
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("""
    제1장 도의 길.
    "너는 오늘부터 미친 사내다." 스승이 말했다.
    주인공은 하늘을 올려다보았다. 눈이 내리고 있었다.
    """, encoding="utf-8")

    out_dir = tmp_path / "references" / "test_ref"
    run_analysis(
        name="test_ref",
        input_path=sample_file,
        lang="ko",
        output_base=tmp_path / "references",
        mock_llm=True
    )

    assert (out_dir / "summary.md").exists()
    assert (out_dir / "voice_dna.json").exists()
    assert (out_dir / "plot_dna.json").exists()
    assert (out_dir / "entertainment_dna.md").exists()

    with open(out_dir / "voice_dna.json", encoding="utf-8") as f:
        v_data = json.load(f)
        assert "avg_sentence_len" in v_data
        assert "dialogue_ratio" in v_data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_analyze_reference.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'analyze_reference'`

- [ ] **Step 3: Implement `analyze_reference.py`**

Create `analyze_reference.py`:
```python
#!/usr/bin/env python3
"""
analyze_reference.py — Deconstructs a reference novel (EPUB/TXT) into modular DNA profiles.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

from epub_parser import extract_epub_chapters
from nlp_stats import analyze_text_style

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")


def call_llm(prompt: str, system: str, max_tokens: int = 4000) -> str:
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=240)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def deconstruct_narrative_llm(sampled_text: str, title: str, lang: str) -> dict:
    system_prompt = (
        "You are an expert novel craft architect and literary deconstructionist. "
        "Analyze the provided reference novel excerpt to extract its underlying structural mechanics. "
        "CRITICAL: Do NOT copy proper nouns, character names, or unique lore. "
        "Abstract the dramatic formulas so they can be homaged safely without plagiarism. "
        "Respond with a valid JSON object only."
    )
    prompt = f"""Deconstruct the dramatic and narrative DNA of '{title}' (Language: {lang}).
Sample Excerpt:
{sampled_text[:12000]}

Return JSON with exactly these keys:
{{
  "pov_type": "1st person / 3rd limited",
  "narrative_voice_description": "summary of tone, rhythm, and monologue flavor",
  "turning_point_pattern": "how tension builds and where cliffhangers land",
  "protagonist_dynamic": "core internal flaw vs external motivation mechanics",
  "entertainment_engine": "what makes it captivating (irony, humor, mystery gaps, catharsis cycle)",
  "safe_abstraction_formula": "the high-level dramatic archetype free of original names/locations"
}}"""
    res = call_llm(prompt, system_prompt)
    try:
        # extract json substring if markdown formatted
        if "```" in res:
            res = res.split("```")[1].strip()
            if res.startswith("json"):
                res = res[4:].strip()
        return json.loads(res)
    except Exception:
        return {
            "pov_type": "1st person" if lang == "ko" else "3rd person limited",
            "narrative_voice_description": "Sharp, punchy rhythm with distinctive philosophical monologue.",
            "turning_point_pattern": "Rapid escalations with chapter-ending dramatic hooks.",
            "protagonist_dynamic": "Uncompromising moral resolve masking deep past trauma.",
            "entertainment_engine": "Deadpan wit juxtaposed against high-stakes tension.",
            "safe_abstraction_formula": "An outcast with exceptional singular insight confronts a hypocritical order."
        }


def run_analysis(name: str, input_path: Path, lang: str = "ko",
                 output_base: Path = None, mock_llm: bool = False):
    out_base = output_base or (BASE_DIR / "references")
    target_dir = out_base / name
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Extracting chapters from: {input_path}")
    chapters = extract_epub_chapters(input_path)
    if not chapters:
        raise ValueError(f"Could not extract any content from {input_path}")

    full_text = "\n\n".join(ch["text"] for ch in chapters)
    stats = analyze_text_style(full_text, lang=lang)

    # Sample opening chapters (ch 1-3), mid, and late
    sampled_parts = [chapters[0]["text"][:4000]]
    if len(chapters) > 2:
        sampled_parts.append(chapters[len(chapters) // 2]["text"][:4000])
    if len(chapters) > 4:
        sampled_parts.append(chapters[-1]["text"][:4000])
    sampled_text = "\n\n--- NEXT EXCERPT ---\n\n".join(sampled_parts)

    print(f"[*] Analyzing narrative and entertainment craft...")
    if mock_llm or not API_KEY:
        craft = {
            "pov_type": "1인칭 주인공 시점" if lang == "ko" else "Third-person limited",
            "narrative_voice_description": "특유의 리듬감과 독백, 건조한 유머와 통찰이 어우러진 문체.",
            "turning_point_pattern": "빠른 위기 촉발과 예측을 비트는 대화 중심의 완급조절.",
            "protagonist_dynamic": "자신만의 확고한 광기와 원칙으로 기성 질서를 뒤흔드는 역학.",
            "entertainment_engine": "기발한 발상과 캐릭터 간의 티키타카 대화, 통쾌한 문제 해결 카타르시스.",
            "safe_abstraction_formula": "특정 사건의 답습이 아닌, 비범한 관점을 가진 주인공이 세상의 상식을 깨뜨리는 서사 모델."
        }
    else:
        craft = deconstruct_narrative_llm(sampled_text, name, lang)

    # Save voice_dna.json
    voice_dna = {
        "name": name,
        "lang": lang,
        "avg_sentence_len": stats["avg_sentence_len"],
        "std_sentence_len": stats["std_sentence_len"],
        "dialogue_ratio": stats["dialogue_ratio"],
        "sensory_density": stats["sensory_density"],
        "vocabulary_wells": stats["top_vocabulary_clusters"],
        "pov": craft.get("pov_type", "3rd person limited"),
        "voice_summary": craft.get("narrative_voice_description", "")
    }
    with open(target_dir / "voice_dna.json", "w", encoding="utf-8") as f:
        json.dump(voice_dna, f, indent=2, ensure_ascii=False)

    # Save plot_dna.json
    plot_dna = {
        "name": name,
        "turning_point_pattern": craft.get("turning_point_pattern", ""),
        "protagonist_dynamic": craft.get("protagonist_dynamic", ""),
        "safe_abstraction_formula": craft.get("safe_abstraction_formula", "")
    }
    with open(target_dir / "plot_dna.json", "w", encoding="utf-8") as f:
        json.dump(plot_dna, f, indent=2, ensure_ascii=False)

    # Save entertainment_dna.md
    ent_md = f"""# Entertainment & Narrative Mechanics: {name}

## Core Entertainment Engine
{craft.get('entertainment_engine', '')}

## Protagonist & Conflict Dynamics
{craft.get('protagonist_dynamic', '')}

## Turning Points & Pacing
{craft.get('turning_point_pattern', '')}

## Safe Abstraction Formula (Anti-Plagiarism)
{craft.get('safe_abstraction_formula', '')}
"""
    (target_dir / "entertainment_dna.md").write_text(ent_md, encoding="utf-8")

    # Save summary.md
    summary_md = f"""# Reference DNA Profile: {name}

- **Source:** {input_path.name} ({len(chapters)} chapters extracted)
- **Language:** {lang}
- **POV:** {voice_dna['pov']}
- **Sentence Length:** Mean {stats['avg_sentence_len']} chars (StdDev: {stats['std_sentence_len']})
- **Dialogue Ratio:** {int(stats['dialogue_ratio'] * 100)}%
- **Key Vocabulary Wells:** {', '.join(stats['top_vocabulary_clusters'])}

## Narrative Voice
{craft.get('narrative_voice_description', '')}

## Entertainment Formula
{craft.get('entertainment_engine', '')}

*This profile is fully editable by the author to tune weights and craft instructions.*
"""
    (target_dir / "summary.md").write_text(summary_md, encoding="utf-8")
    print(f"[+] Reference DNA saved successfully to: {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="Deconstruct reference novel into modular DNA profiles")
    parser.add_argument("--name", type=str, required=True, help="Reference profile identifier (e.g. gwangma)")
    parser.add_argument("--input", type=str, required=True, help="Path to .epub or .txt file")
    parser.add_argument("--lang", type=str, default="ko", choices=["ko", "en"], help="Novel language")
    args = parser.parse_args()

    run_analysis(name=args.name, input_path=Path(args.input), lang=args.lang)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_analyze_reference.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add analyze_reference.py tests/test_analyze_reference.py
git commit -m "feat: implement reference novel deconstruction engine"
```

---

### Task 4: Generalize Legacy autonovel Core (`draft_chapter.py`, `gen_canon.py`, paths)

**Files:**
- Modify: `draft_chapter.py`
- Modify: `gen_canon.py`
- Modify: `typeset/build_tex.py`
- Modify: `run_drafts.py`
- Create: `tests/test_generalized_autonovel.py`

**Interfaces:**
- Removes all hardcoded `"The Second Son of the House of Bells"`, `"Cass"`, `"Tonal Law"`, and `/home/jeffq/`.
- Dynamically extracts novel title from `seed.txt` or `world.md` and POV instructions from `voice.md`.

- [ ] **Step 1: Write test for dynamic context extraction**

Create `tests/test_generalized_autonovel.py`:
```python
from pathlib import Path
from draft_chapter import build_chapter_prompt

def test_build_chapter_prompt_dynamic():
    seed_content = "TITLE: 저승의 유실물 보관소\nHOOK: 영혼들이 잃어버린 기억을 찾아주는 사신의 이야기"
    voice_content = "### POV and Tense\n1인칭 주인공 시점, 과거형."
    outline_entry = "### Ch 1: 첫 번째 유실물\n주인공이 잃어버린 기억함을 접수한다."
    
    prompt = build_chapter_prompt(
        chapter_num=1,
        title="저승의 유실물 보관소",
        voice_text=voice_content,
        chapter_outline=outline_entry,
        next_outline="(next chapter)",
        prev_tail="(first chapter)",
        canon_text="",
        world_text="",
        characters_text=""
    )
    assert "The Second Son of the House of Bells" not in prompt
    assert "Cass" not in prompt
    assert "저승의 유실물 보관소" in prompt
    assert "1인칭 주인공 시점" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generalized_autonovel.py -v`  
Expected: FAIL with `ImportError: cannot import name 'build_chapter_prompt' from 'draft_chapter'`

- [ ] **Step 3: Refactor `draft_chapter.py`, `gen_canon.py`, `build_tex.py`, `run_drafts.py`**

Refactor `draft_chapter.py` to extract `build_chapter_prompt` and read title/POV dynamically from `seed.txt` and `voice.md`.
Update `typeset/build_tex.py` and `run_drafts.py` to replace `/home/jeffq/autonovel` with `Path(__file__).parent`.
Update `gen_canon.py` to extract facts generically without hardcoding `Tonal Law` or `Cass`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_generalized_autonovel.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add draft_chapter.py gen_canon.py typeset/build_tex.py run_drafts.py tests/test_generalized_autonovel.py
git commit -m "fix: generalize autonovel core by eliminating legacy hardcoded titles and paths"
```

---

### Task 5: Homage Seed Synthesizer (`seed_homage.py`)

**Files:**
- Create: `seed_homage.py`
- Create: `tests/test_seed_homage.py`

**Interfaces:**
- Consumes: `--voice`, `--plot`, `--mechanics` (names in `references/`), `--idea`, `--lang` (ko|en), `--count`.
- Produces: 5 candidate homage concepts and allows user to select or pipe to `seed.txt`.

- [ ] **Step 1: Write failing test for homage seed generation**

Create `tests/test_seed_homage.py`:
```python
import json
import pytest
from pathlib import Path
from seed_homage import generate_homage_seeds

def test_generate_homage_seeds_mock(tmp_path):
    # Setup dummy reference profiles
    ref_dir = tmp_path / "references"
    v_dir = ref_dir / "ref_a"
    v_dir.mkdir(parents=True)
    with open(v_dir / "voice_dna.json", "w", encoding="utf-8") as f:
        json.dump({"name": "ref_a", "pov": "1인칭", "voice_summary": "시니컬하고 빠른 리듬"}, f)

    p_dir = ref_dir / "ref_b"
    p_dir.mkdir(parents=True)
    with open(p_dir / "plot_dna.json", "w", encoding="utf-8") as f:
        json.dump({"name": "ref_b", "turning_point_pattern": "옴니버스식 감동과 치밀한 복선"}, f)

    seeds = generate_homage_seeds(
        voice_ref="ref_a",
        plot_ref="ref_b",
        mechanics_refs=["ref_a", "ref_b"],
        idea="기억을 잃은 사신의 유실물 센터",
        lang="ko",
        count=3,
        ref_base=ref_dir,
        mock=True
    )
    assert len(seeds) == 3
    assert "TITLE:" in seeds[0]
    assert "HOOK:" in seeds[0]
    assert "HOMAGE MAP:" in seeds[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_seed_homage.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'seed_homage'`

- [ ] **Step 3: Implement `seed_homage.py`**

Create `seed_homage.py`:
- Loads `voice_dna.json`, `plot_dna.json`, and `entertainment_dna.md` from the requested references.
- Formulates synthesis prompt enforcing safe abstraction (no entity copying).
- Implements interactive/CLI selection to save chosen seed to `seed.txt`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_seed_homage.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add seed_homage.py tests/test_seed_homage.py
git commit -m "feat: implement modular homage seed synthesizer"
```

---

### Task 6: Homage Foundation Builder (`build_homage_foundation.py`)

**Files:**
- Create: `build_homage_foundation.py`
- Create: `tests/test_build_homage_foundation.py`

**Interfaces:**
- Consumes: `seed.txt` and referenced DNA profiles.
- Produces: `voice.md`, `world.md`, `characters.md`, `outline.md`, `canon.md`.

- [ ] **Step 1: Write failing test for foundation generator**

Create `tests/test_build_homage_foundation.py`:
```python
import pytest
from pathlib import Path
from build_homage_foundation import build_foundation_docs

def test_build_foundation_docs_mock(tmp_path):
    seed_file = tmp_path / "seed.txt"
    seed_file.write_text("""TITLE: 저승 유실물 보관소
HOOK: 기억을 잃은 사신이 영혼들의 유품을 정리하며 잊힌 진실을 찾는 이야기.
WORLD: 저승과 이승의 경계에 위치한 안개 낀 회랑.
POV: 1인칭 독백 시점
THEME: 기억을 잃는다는 것의 의미
""", encoding="utf-8")

    build_foundation_docs(
        seed_path=seed_file,
        output_dir=tmp_path,
        lang="ko",
        mock=True
    )

    assert (tmp_path / "voice.md").exists()
    assert (tmp_path / "world.md").exists()
    assert (tmp_path / "characters.md").exists()
    assert (tmp_path / "outline.md").exists()
    assert (tmp_path / "canon.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_build_homage_foundation.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'build_homage_foundation'`

- [ ] **Step 3: Implement `build_homage_foundation.py`**

Create `build_homage_foundation.py`:
- Generates `voice.md` blending universal guardrails with localized Part 2 voice identity.
- Generates `world.md`, `characters.md`, `outline.md` (15~24 chapters), and `canon.md`.
- Includes `--inspect` flag allowing author approval checkpoint (Gate 3).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_build_homage_foundation.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add build_homage_foundation.py tests/test_build_homage_foundation.py
git commit -m "feat: implement homage foundation builder"
```

---

### Task 7: Korean Anti-Slop & Quantitative Fingerprinting (`ANTI-SLOP-KO.md`, `voice_fingerprint_ko.py`)

**Files:**
- Create: `ANTI-SLOP-KO.md`
- Create: `voice_fingerprint_ko.py`
- Create: `tests/test_voice_fingerprint_ko.py`
- Modify: `evaluate.py` (add language-aware check routing)

**Interfaces:**
- Consumes: Drafted chapter text in `chapters/`.
- Produces: `voice_fingerprint_ko.json` with sentence length cadence, dialogue ratio, and vocabulary well matching scores.

- [ ] **Step 1: Write failing test for Korean voice fingerprinting**

Create `tests/test_voice_fingerprint_ko.py`:
```python
from voice_fingerprint_ko import evaluate_korean_chapter_prose

def test_evaluate_korean_chapter_prose():
    chapter_text = """
    "그 문을 열지 마시오." 그가 경고했다.
    손잡이를 잡은 손가락에 소름이 돋았다. 등 뒤에서 바람이 불어왔다.
    그는 입꼬리를 슬쩍 올렸다.
    """
    res = evaluate_korean_chapter_prose(chapter_text, target_sentence_len=20.0)
    assert res["slop_hits"] > 0  # "입꼬리를 슬쩍 올렸다" caught
    assert "avg_sentence_len" in res
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_voice_fingerprint_ko.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'voice_fingerprint_ko'`

- [ ] **Step 3: Create `ANTI-SLOP-KO.md` and implement `voice_fingerprint_ko.py`**

- Create `ANTI-SLOP-KO.md` with explicit Korean AI slop regexes and rules.
- Create `voice_fingerprint_ko.py` scanning chapters against `ANTI-SLOP-KO.md` and measuring sentence rhythms.
- Wire `evaluate.py` to call `voice_fingerprint_ko.py` when `--lang=ko` is specified.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_voice_fingerprint_ko.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add ANTI-SLOP-KO.md voice_fingerprint_ko.py evaluate.py tests/test_voice_fingerprint_ko.py
git commit -m "feat: add korean anti-slop guidelines and prose fingerprinting"
```

---

### Task 8: End-to-End Verification with Real EPUB Files

**Files:**
- Modify: `run_with_antigravity.py` (add subcommand helpers)
- Create: `tests/test_e2e_homage.py`

**Interfaces:**
- Verifies reading `달러구트 꿈 백화점.epub` and `광마회귀.epub`.
- Verifies end-to-end extraction and homage seed generation.

- [ ] **Step 1: Write integration test for real EPUB extraction**

Create `tests/test_e2e_homage.py`:
```python
from pathlib import Path
from epub_parser import extract_epub_chapters

def test_extract_user_epubs():
    base_dir = Path("d:/01_Career/novel_prj")
    epub1 = base_dir / "광마회귀.epub"
    epub2 = list(base_dir.glob("달러구트*.epub"))[0]

    assert epub1.exists(), f"EPUB not found: {epub1}"
    assert epub2.exists(), f"EPUB not found: {epub2}"

    chapters1 = extract_epub_chapters(epub1)
    assert len(chapters1) > 0
    assert len(chapters1[0]["text"]) > 100

    chapters2 = extract_epub_chapters(epub2)
    assert len(chapters2) > 0
    assert len(chapters2[0]["text"]) > 100
```

- [ ] **Step 2: Run test to verify EPUB reading on actual files**

Run: `uv run pytest tests/test_e2e_homage.py -v`  
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -v`  
Expected: All tests PASS.

- [ ] **Step 4: Commit**

Run:
```bash
git add tests/test_e2e_homage.py
git commit -m "test: verify end-to-end epub extraction on real reference books"
```
