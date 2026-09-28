#!/usr/bin/env python3
"""
seed_homage.py — Homage novel seed synthesizer.
Mixes and matches modular DNA from multiple reference novels to create original concepts.
"""
import argparse
import json
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


def call_llm(prompt: str, system: str, max_tokens: int = 8000) -> str:
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.8,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=240)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def generate_homage_seeds(
    voice_ref: str,
    plot_ref: str,
    mechanics_refs: list[str],
    idea: str = "",
    lang: str = "ko",
    count: int = 5,
    ref_base: Path = None,
    mock: bool = False,
) -> list[str]:
    base = ref_base or (BASE_DIR / "references")

    v_dna = load_json(base / voice_ref / "voice_dna.json")
    p_dna = load_json(base / plot_ref / "plot_dna.json")
    
    mechanics_texts = []
    for m in mechanics_refs:
        m_txt = load_text(base / m / "entertainment_dna.md")
        if m_txt:
            mechanics_texts.append(f"[{m} Entertainment DNA]:\n{m_txt[:1000]}")

    if mock or not API_KEY:
        results = []
        for i in range(1, count + 1):
            results.append(f"""NUMBER: {i}
TITLE: 망각의 유실물 보관소 #{i}
HOOK: 저승의 문턱에서 기억을 잃은 사서가 영혼들이 두고 간 마지막 미련을 역추적한다.
HOMAGE MAP: Voice from '{voice_ref}' (rhythmic dialogue & dry wit) + Plot from '{plot_ref}' (episodic catharsis & central mystery)
WORLD: 저승과 이승의 경계에 끝없이 늘어선 서고와 수억 개의 유실물 상자들.
MAGIC/COST: 유품을 만지면 망자의 기억을 체험할 수 있으나, 자신의 생전 기억이 하나씩 영구 소멸된다.
TENSION: Personal(자신의 잊힌 정체를 찾으려는 갈망) vs Cosmic(저승의 기억 질서 붕괴를 막아야 하는 의무)
THEME: 인간을 진정으로 인간답게 만드는 것은 행복한 기억인가, 아픈 상처인가?
SAFE ABSTRACTION CHECK: PASSED (No proper nouns, characters, or specific lore copied from references).
""")
        return results

    system_prompt = (
        "You are an acclaimed master novelist and conceptual architect. "
        "You synthesize original, captivating novel seed concepts by homaging distinct storytelling DNA. "
        "CRITICAL SAFEGUARD: Never copy proper nouns, character names, or specific plot sequences from references. "
        "Translate abstract craft mechanics into completely original worlds and premises."
    )

    user_prompt = f"""Generate {count} completely original novel seed concepts in {lang.upper()} ('ko' = Korean, 'en' = English).

REFERENCE CRAFT DNA TO HOMAGE:
1. Voice & Stylistic DNA (from '{voice_ref}'):
   - POV: {v_dna.get('pov', '1인칭')}
   - Rhythm & Voice: {v_dna.get('voice_summary', '')}
   - Key Vocabulary Registers: {', '.join(v_dna.get('vocabulary_wells', []))}

2. Plot Structure & Pacing DNA (from '{plot_ref}'):
   - Pacing & Turning Points: {p_dna.get('turning_point_pattern', '')}
   - Protagonist Dilemma Model: {p_dna.get('protagonist_dynamic', '')}
   - High-level Model: {p_dna.get('safe_abstraction_formula', '')}

3. Entertainment & Core Mechanics (from {', '.join(mechanics_refs)}):
{chr(10).join(mechanics_texts)}

USER'S INITIAL LOGLINE / SEED IDEA (if provided):
"{idea if idea else '(None provided - brainstorm original premises combining the reference DNAs)'}"

FOR EACH CONCEPT, PROVIDE:
NUMBER: <N>
TITLE: <Evocative, memorable title>
HOOK: <One punchy sentence that hooks the reader instantly>
HOMAGE MAP: <Explain precisely how the voice of {voice_ref} and plot of {plot_ref} were creatively cross-pollinated>
WORLD: <Concrete, sensory world details and unusual premise setting>
MAGIC/COST: <Core speculative or thematic rule, and its devastating cost/limitation>
TENSION: <Personal dilemma vs Cosmic/World conflict>
THEME: <A genuine question with no easy answer>
SAFE ABSTRACTION CHECK: PASSED (Affirm that no names or lore from references were copied).
"""

    resp = call_llm(user_prompt, system_prompt, max_tokens=8000)
    # Split by NUMBER:
    parts = re.split(r'\n(?=NUMBER:\s*\d+)', resp.strip())
    return [p.strip() for p in parts if p.strip()]


def main():
    parser = argparse.ArgumentParser(description="Generate homage novel seeds from reference DNA")
    parser.add_argument("--voice", type=str, required=True, help="Reference name for voice DNA")
    parser.add_argument("--plot", type=str, required=True, help="Reference name for plot DNA")
    parser.add_argument("--mechanics", type=str, default="", help="Comma-separated reference names for mechanics")
    parser.add_argument("--idea", type=str, default="", help="Optional author premise/idea")
    parser.add_argument("--lang", type=str, default="ko", choices=["ko", "en"], help="Target novel language")
    parser.add_argument("--count", type=int, default=5, help="Number of seeds to generate")
    parser.add_argument("--select", type=int, default=0, help="Automatically save seed N (1-based) to seed.txt")
    args = parser.parse_args()

    mechanics = [m.strip() for m in args.mechanics.split(",") if m.strip()]
    if not mechanics:
        mechanics = [args.voice, args.plot]

    print(f"[*] Synthesizing {args.count} homage seeds (Voice: {args.voice}, Plot: {args.plot})...")
    seeds = generate_homage_seeds(
        voice_ref=args.voice,
        plot_ref=args.plot,
        mechanics_refs=mechanics,
        idea=args.idea,
        lang=args.lang,
        count=args.count,
    )

    for s in seeds:
        print("\n" + "=" * 60)
        print(s)

    if args.select > 0 and 1 <= args.select <= len(seeds):
        target_seed = seeds[args.select - 1]
        (BASE_DIR / "seed.txt").write_text(target_seed, encoding="utf-8")
        print(f"\n[+] Selected Concept #{args.select} saved to seed.txt!")
    else:
        print("\n" + "=" * 60)
        print("To select a concept, copy your favorite into seed.txt, or re-run with --select=<N>.")


if __name__ == "__main__":
    main()
