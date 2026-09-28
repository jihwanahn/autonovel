#!/usr/bin/env python3
"""
analyze_reference.py — Deconstructs reference novels (single EPUB/TXT or multi-volume series)
into modular DNA profiles.
"""
import argparse
import glob
import json
import os
import re
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


def resolve_input_files(input_arg: str | Path) -> list[Path]:
    """Resolves single file, comma-separated files, directories, or glob patterns into sorted Paths."""
    raw_str = str(input_arg).strip()
    parts = [p.strip() for p in raw_str.split(",") if p.strip()]
    resolved = []
    for part in parts:
        p = Path(part)
        if p.is_file():
            resolved.append(p)
        elif p.is_dir():
            resolved.extend(p.glob("*.epub"))
            resolved.extend(p.glob("*.txt"))
        else:
            matches = glob.glob(part)
            if matches:
                resolved.extend(Path(m) for m in matches)
            else:
                matches_norm = glob.glob(part.replace("\\", "/"))
                resolved.extend(Path(m) for m in matches_norm)

    if not resolved:
        raise FileNotFoundError(f"No files matched input: {input_arg}")

    def natural_sort_key(p: Path):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', p.name)]

    return sorted(list(set(resolved)), key=natural_sort_key)


def run_analysis(name: str, input_path: str | Path, lang: str = "ko",
                 output_base: Path = None, mock_llm: bool = False):
    out_base = output_base or (BASE_DIR / "references")
    target_dir = out_base / name
    target_dir.mkdir(parents=True, exist_ok=True)

    input_files = resolve_input_files(input_path)
    print(f"[*] Resolved {len(input_files)} volume file(s) for '{name}':")
    for f in input_files:
        print(f"    - {f.name}")

    all_chapters = []
    global_idx = 1
    for fpath in input_files:
        chs = extract_epub_chapters(fpath)
        for c in chs:
            c_copy = dict(c)
            c_copy["index"] = global_idx
            c_copy["source_volume"] = fpath.name
            all_chapters.append(c_copy)
            global_idx += 1

    if not all_chapters:
        raise ValueError(f"Could not extract any content from {input_path}")

    full_text = "\n\n".join(ch["text"] for ch in all_chapters)
    stats = analyze_text_style(full_text, lang=lang)

    # Sample opening chapters (Vol 1 intro), mid (middle volume), and climax (last volume)
    sampled_parts = [all_chapters[0]["text"][:4000]]
    if len(all_chapters) > 2:
        mid_idx = len(all_chapters) // 2
        sampled_parts.append(all_chapters[mid_idx]["text"][:4000])
    if len(all_chapters) > 4:
        sampled_parts.append(all_chapters[-1]["text"][:4000])
    sampled_text = "\n\n--- NEXT EXCERPT ---\n\n".join(sampled_parts)

    print(f"[*] Analyzing narrative and entertainment craft across {len(all_chapters)} chapters...")
    if mock_llm or not API_KEY:
        craft = {
            "pov_type": "3인칭 전지적/제한적 시점" if lang == "ko" else "Third-person limited",
            "narrative_voice_description": "장대한 서사와 인물 군상극, 무협의 의기와 낭만이 깃든 정통 문체.",
            "turning_point_pattern": "영웅의 성장과 기연, 문파 간의 은원 관계가 얽히며 거대한 결전으로 향하는 구조.",
            "protagonist_dynamic": "우직하고 순박한 성품의 주인공이 시련을 겪으며 천하제일의 무공과 덕을 완성해가는 성장 서사.",
            "entertainment_engine": "다채로운 무공 대결, 기발한 기연, 인물 간의 애증과 협(俠)의 카타르시스.",
            "safe_abstraction_formula": "비범한 무림 세계 속에서 순수한 주인공이 거대한 역사의 소용돌이를 헤쳐나가는 대서사 성장 모델."
        }
    else:
        craft = deconstruct_narrative_llm(sampled_text, name, lang)

    # Save voice_dna.json
    voice_dna = {
        "name": name,
        "lang": lang,
        "volume_count": len(input_files),
        "total_chapters": len(all_chapters),
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
        "volume_count": len(input_files),
        "total_chapters": len(all_chapters),
        "turning_point_pattern": craft.get("turning_point_pattern", ""),
        "protagonist_dynamic": craft.get("protagonist_dynamic", ""),
        "safe_abstraction_formula": craft.get("safe_abstraction_formula", "")
    }
    with open(target_dir / "plot_dna.json", "w", encoding="utf-8") as f:
        json.dump(plot_dna, f, indent=2, ensure_ascii=False)

    # Save entertainment_dna.md
    ent_md = f"""# Entertainment & Narrative Mechanics: {name}

## Volumes & Scope
- **Total Volumes:** {len(input_files)}
- **Total Chapters:** {len(all_chapters)}

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
    if len(input_files) == 1:
        sources_str = f"{input_files[0].name} ({len(all_chapters)} chapters extracted)"
    else:
        sources_str = f"{len(input_files)} volumes ({len(all_chapters)} total chapters extracted):\n" + "\n".join(f"  - {f.name}" for f in input_files)

    summary_md = f"""# Reference DNA Profile: {name}

- **Source:** {sources_str}
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
    print(f"[+] Multi-volume Reference DNA saved successfully to: {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="Deconstruct reference novel into modular DNA profiles")
    parser.add_argument("--name", type=str, required=True, help="Reference profile identifier (e.g. sajoyeongung)")
    parser.add_argument("--input", type=str, required=True, help="Path, glob pattern, or comma-separated list of .epub/.txt files")
    parser.add_argument("--lang", type=str, default="ko", choices=["ko", "en"], help="Novel language")
    args = parser.parse_args()

    run_analysis(name=args.name, input_path=args.input, lang=args.lang)


if __name__ == "__main__":
    main()
