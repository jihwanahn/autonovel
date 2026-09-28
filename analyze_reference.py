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
