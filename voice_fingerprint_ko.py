#!/usr/bin/env python3
"""
voice_fingerprint_ko.py — Quantitative prose quality & Korean AI slop detection.
"""
import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CHAPTERS_DIR = BASE_DIR / "chapters"

from nlp_stats import analyze_text_style

BANNED_KO_PATTERNS = [
    r"입꼬리를\s*(?:슬쩍|살짝|비틀어|씨익)?\s*올렸다",
    r"씁쓸한\s*(?:미소|웃음)를\s*지었다",
    r"알\s*수\s*없는\s*(?:감정|위화감|불안감|기운)이\s*(?:밀려왔다|스쳤다|들었다|느껴졌다)",
    r"묘한\s*위화감이\s*들었다",
    r"한\s*줄기\s*(?:서늘한|차가운)\s*바람이",
    r"마치\s*.*?(?:인\s*것만\s*같았다|듯\s*보였다)",
    r"머릿속이\s*하얘졌다",
    r"숨을\s*(?:깊게|몰아)\s*(?:들이쉬었다|내쉬었다)",
]


def evaluate_korean_chapter_prose(
    text: str,
    target_sentence_len: float = 20.0,
    vocabulary_wells: list[str] = None,
) -> dict:
    stats = analyze_text_style(text, lang="ko")

    # Slop detection
    slop_matches = []
    for pattern in BANNED_KO_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            slop_matches.extend(matches)

    slop_count = len(slop_matches)
    slop_penalty = min(slop_count * 1.5, 5.0)

    # Sentence rhythm adherence
    len_diff = abs(stats["avg_sentence_len"] - target_sentence_len)
    rhythm_penalty = min(len_diff * 0.1, 2.0)

    # Vocabulary wells coverage
    vocab_hits = 0
    if vocabulary_wells:
        for w in vocabulary_wells:
            if w in text:
                vocab_hits += 1
        vocab_coverage = round(vocab_hits / max(len(vocabulary_wells), 1), 2)
    else:
        vocab_coverage = 1.0

    overall_penalty = round(slop_penalty + rhythm_penalty, 2)
    overall_score = max(round(10.0 - overall_penalty, 1), 0.0)

    return {
        "avg_sentence_len": stats["avg_sentence_len"],
        "std_sentence_len": stats["std_sentence_len"],
        "dialogue_ratio": stats["dialogue_ratio"],
        "slop_hits": slop_count,
        "slop_examples": slop_matches[:5],
        "vocabulary_well_coverage": vocab_coverage,
        "slop_penalty": overall_penalty,
        "prose_score": overall_score,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Korean chapter prose fingerprint")
    parser.add_argument("target", nargs="?", default="1", help="Chapter number or path to markdown file")
    args = parser.parse_args()

    target_path = Path(args.target)
    if not target_path.exists():
        try:
            ch_num = int(args.target)
            target_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
        except ValueError:
            pass

    if not target_path.exists():
        print(f"[-] Chapter file not found: {target_path}")
        sys.exit(1)

    text = target_path.read_text(encoding="utf-8")
    result = evaluate_korean_chapter_prose(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
