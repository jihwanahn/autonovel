#!/usr/bin/env python3
"""
Draft a single chapter using the writer model.
Usage: python draft_chapter.py 1
"""
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")
CHAPTERS_DIR = BASE_DIR / "chapters"


def call_writer(prompt, max_tokens=16000):
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "context-1m-2025-08-07",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.8,
        "system": (
            "You are a master fiction writer drafting a novel chapter. "
            "You strictly follow the voice and POV defined in the voice guide. "
            "You hit every beat in the outline. You never use words from the banned list. "
            "You show, never tell emotions. Your prose is specific, sensory, and grounded. "
            "Metaphors come from the characters' lived experiences. You vary sentence length. "
            "You write the FULL chapter without truncating, summarizing, or skipping ahead."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def extract_chapter_outline(outline_text, chapter_num):
    """Extract a specific chapter's outline entry."""
    pattern = rf'### Ch(?:apter)?\s*{chapter_num}:.*?(?=### Ch(?:apter)?\s*{chapter_num + 1}:|## Foreshadowing|$)'
    match = re.search(pattern, outline_text, re.DOTALL | re.IGNORECASE)
    return match.group(0).strip() if match else "(not found)"


def extract_next_chapter_outline(outline_text, chapter_num):
    """Extract the next chapter's outline (just first few lines for continuity)."""
    next_entry = extract_chapter_outline(outline_text, chapter_num + 1)
    if next_entry == "(not found)":
        return "(final chapter)"
    lines = next_entry.split('\n')[:10]
    return '\n'.join(lines)


def get_novel_title(base_dir: Path) -> str:
    seed_path = base_dir / "seed.txt"
    if seed_path.exists():
        for line in seed_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TITLE:"):
                return line.split("TITLE:", 1)[1].strip()
            if line.startswith("# "):
                return line.split("# ", 1)[1].strip()
    return "The Novel"


def build_chapter_prompt(
    chapter_num: int,
    title: str,
    voice_text: str,
    chapter_outline: str,
    next_outline: str,
    prev_tail: str,
    canon_text: str,
    world_text: str,
    characters_text: str,
) -> str:
    # Extract POV if present in voice_text
    pov_hint = "Follow the POV and Tense defined in the voice guide."
    if "### POV and Tense" in voice_text:
        pov_section = voice_text.split("### POV and Tense", 1)[1].split("###", 1)[0].strip()
        if pov_section:
            pov_hint = f"POV & Tense: {pov_section}"

    return f"""Write Chapter {chapter_num} of "{title}."

VOICE DEFINITION (follow this exactly):
{voice_text}

THIS CHAPTER'S OUTLINE (hit every beat):
{chapter_outline}

NEXT CHAPTER'S OUTLINE (for continuity -- end this chapter so it flows into the next):
{next_outline}

PREVIOUS CHAPTER'S ENDING (continue from here):
{prev_tail}

WORLD BIBLE (reference for worldbuilding details):
{world_text}

CHARACTER REGISTRY (reference for speech patterns and behavior):
{characters_text}

CANON RULES (never contradict these facts):
{canon_text}

WRITING INSTRUCTIONS:
1. Write the COMPLETE chapter. Target ~3,000-4,000 words. Do not truncate or summarize.
2. {pov_hint}
3. Hit ALL numbered beats from the outline in order.
4. Plant all foreshadowing elements designated for this chapter.
5. Ground every scene in sensory detail: tactile textures, lighting, sounds, scents.
6. Dialogue must strictly follow the distinct speech patterns defined in characters.md.
7. Strictly avoid banned words and AI clichés from voice.md.
8. Vary sentence and paragraph lengths deliberately for dynamic pacing.
9. Metaphors must emerge naturally from the protagonist's background and world.
10. Trust the reader. Show actions and physical reactions; do not over-explain emotional meanings.
11. Start the chapter in-scene, not with static exposition. End on an active moment or cliffhanger.
12. At least 70% of the chapter should be in-scene (dialogue and immediate action) rather than summary.

Write the chapter now. Full text, beginning to end.
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python draft_chapter.py <chapter_num>")
        sys.exit(1)

    chapter_num = int(sys.argv[1])
    title = get_novel_title(BASE_DIR)

    # Load all context
    voice = load_file(BASE_DIR / "voice.md")
    world = load_file(BASE_DIR / "world.md")
    characters = load_file(BASE_DIR / "characters.md")
    outline = load_file(BASE_DIR / "outline.md")
    canon = load_file(BASE_DIR / "canon.md")

    # Chapter-specific context
    chapter_outline = extract_chapter_outline(outline, chapter_num)
    next_chapter = extract_next_chapter_outline(outline, chapter_num)

    # Previous chapter (if exists)
    prev_path = CHAPTERS_DIR / f"ch_{chapter_num - 1:02d}.md"
    if prev_path.exists():
        prev_text = prev_path.read_text(encoding="utf-8")
        prev_tail = prev_text[-2000:] if len(prev_text) > 2000 else prev_text
    else:
        prev_tail = "(first chapter -- no previous)"

    prompt = build_chapter_prompt(
        chapter_num=chapter_num,
        title=title,
        voice_text=voice,
        chapter_outline=chapter_outline,
        next_outline=next_chapter,
        prev_tail=prev_tail,
        canon_text=canon,
        world_text=world,
        characters_text=characters,
    )

    print(f"Drafting Chapter {chapter_num} of '{title}'...", file=sys.stderr)
    result = call_writer(prompt)

    # Save
    CHAPTERS_DIR.mkdir(exist_ok=True)
    out_path = CHAPTERS_DIR / f"ch_{chapter_num:02d}.md"
    out_path.write_text(result, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)
    print(result)


if __name__ == "__main__":
    main()
