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
    genre: str = "",
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
            genre_tag = genre if genre else "판타지/미스터리"
            results.append(f"""NUMBER: {i}
TITLE: 망각의 유실물 보관소 #{i}
GENRE: {genre_tag}
HOOK: 저승의 문턱에서 기억을 잃은 사서가 영혼들이 두고 간 마지막 미련을 역추적한다.
HOMAGE MAP: Voice from '{voice_ref}' (rhythmic dialogue & dry wit) + Plot from '{plot_ref}' (episodic catharsis & central mystery)
WORLD: 저승과 이승의 경계에 끝없이 늘어선 서고와 수억 개의 유실물 상자들.
CORE MECHANIC & COST: 유품을 만지면 망자의 기억을 체험할 수 있으나, 자신의 생전 기억이 하나씩 영구 소멸된다.
TENSION: Personal(자신의 잊힌 정체를 찾으려는 갈망) vs Cosmic(저승의 기억 질서 붕괴를 막아야 하는 의무)
THEME: 인간을 진정으로 인간답게 만드는 것은 행복한 기억인가, 아픈 상처인가?
SAFE ABSTRACTION CHECK: PASSED (No proper nouns, characters, or specific lore copied from references).
""")
        return results

    if genre:
        genre_instruction = (
            f"TARGET GENRE: {genre}\n"
            f"CRITICAL GENRE RULE: The story MUST belong strictly to the '{genre}' genre. "
            f"If the genre is non-supernatural (e.g. 현대 미스터리, 스릴러, 일반 드라마), do NOT introduce magic or fantasy elements; "
            f"if the genre is 무협(Martial Arts), focus on martial sects, internal energy (내공), Jianghu chivalry, and realistic combat; "
            f"if SF, extrapolate technology and society."
        )
    else:
        genre_instruction = (
            f"TARGET GENRE STRATEGY (AUTONOMOUS BEST-FIT RECOMMENDATION):\n"
            f"Do NOT default to generic high fantasy! Instead, deeply analyze the creative friction, chemistry, and tone between "
            f"the Voice DNA ('{voice_ref}') and Plot DNA ('{plot_ref}').\n"
            f"Autonomously determine the single most compelling, commercially fresh genre that brings out the absolute best in this combination "
            f"(for example: pairing a cynical martial arts monologue with a cozy episodic shop plot produces '강호 일상 무협(Cozy Wuxia)' or '현대 블랙코미디 탐정/오컬트물'; "
            f"pairing contemplative prose with epic adventure produces '사색적 역사 미스터리').\n"
            f"In each concept, declare the optimal RECOMMENDED GENRE and clearly explain WHY this genre is the ultimate playground for this specific Voice + Plot collision."
        )

    system_prompt = (
        "You are an acclaimed master novelist, genre theorist, and conceptual architect across all literary forms "
        "(Martial Arts/무협, Mystery, Thriller, SF, Literary Fiction, Cozy Drama, Urban Fantasy). "
        "You analyze storytelling DNA and synthesize original concepts in the most fitting, unexpected, and commercially brilliant genres. "
        "CRITICAL SAFEGUARD: Never copy proper nouns, character names, or specific plot sequences from references."
    )

    user_prompt = f"""Generate {count} completely original novel seed concepts in {lang.upper()} ('ko' = Korean, 'en' = English).

{genre_instruction}

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
"{idea if idea else '(None provided - brainstorm original premises combining the reference DNAs in the most synergistic recommended genres)'}"

FOR EACH CONCEPT, PROVIDE:
NUMBER: <N>
TITLE: <Evocative, memorable title>
GENRE: <Recommended Genre (e.g. 강호 일상 무협, 현대 어반 미스터리, 사색적 SF 등)>
GENRE RATIONALE: <1-2 sentences explaining why this genre is the absolute best match to unleash the synergy between {voice_ref}'s voice and {plot_ref}'s plot>
HOOK: <One punchy sentence that hooks the reader instantly>
HOMAGE MAP: <Explain precisely how the voice of {voice_ref} and plot of {plot_ref} were creatively cross-pollinated>
WORLD: <Concrete, sensory world details and premise setting appropriate to the recommended genre>
CORE MECHANIC & COST: <The core conflict mechanism, trade-off, martial law, or central investigation rule, and its severe cost or dilemma>
TENSION: <Personal dilemma vs External/Societal conflict>
THEME: <A genuine question with no easy answer>
SAFE ABSTRACTION CHECK: PASSED (Affirm that no names or lore from references were copied).
"""

    resp = call_llm(user_prompt, system_prompt, max_tokens=8000)
    # Split by NUMBER or CONCEPT markers (handles markdown bold/headers)
    parts = re.split(
        r'\n(?=(?:#{1,3}\s*CONCEPT\s*\d+|\*{0,2}NUMBER\*{0,2}:?\s*\d+))',
        resp.strip(),
        flags=re.IGNORECASE,
    )
    clean_parts = [
        p.strip() for p in parts
        if re.search(r'(?:CONCEPT\s*\d+|NUMBER\s*[:\.]?\s*\d+)', p, re.IGNORECASE)
    ]
    return clean_parts if clean_parts else [resp.strip()]



def save_candidates_and_seed(
    seeds: list[str],
    base_dir: Path,
    select: int = 0,
    voice: str = "",
    plot: str = "",
    genre: str = "",
) -> tuple[Path, Path]:
    # 1. Save all generated concepts to candidates.md
    candidates_file = base_dir / "candidates.md"
    md_content = "# Novel Seed Candidates\n\n"
    if voice:
        md_content += f"- **Voice Reference**: `{voice}`\n"
    if plot:
        md_content += f"- **Plot Reference**: `{plot}`\n"
    if genre:
        md_content += f"- **Target Genre**: `{genre}`\n"
    md_content += f"- **Total Concepts**: {len(seeds)}\n\n---\n\n"
    for i, s in enumerate(seeds, 1):
        md_content += f"## Candidate {i}\n\n```text\n{s}\n```\n\n---\n\n"
    candidates_file.write_text(md_content, encoding="utf-8")

    # 2. Handle seed.txt save
    seed_file = base_dir / "seed.txt"
    if select > 0 and 1 <= select <= len(seeds):
        target_seed = seeds[select - 1]
        seed_file.write_text(target_seed, encoding="utf-8")
        print(f"[+] 선택하신 Concept #{select} 가 seed.txt 에 저장되었습니다!")
    elif not seed_file.exists() and seeds:
        # Default: auto-select concept #1 if seed.txt doesn't exist
        seed_file.write_text(seeds[0], encoding="utf-8")
        print(f"[+] (기본값) Concept #1 이 seed.txt 로 자동 저장되었습니다.")
        print("    - 다른 후보로 변경하려면: --select=<번호> 로 다시 실행하거나,")
        print("    - 에디터에서 candidates.md 의 마음에 드는 후보를 복사하여 seed.txt 에 붙여넣으세요.")
    else:
        print("[!] 기존 seed.txt 파일이 이미 존재하여 보존되었습니다.")
        print("    - 이번 후보 중 하나로 교체하려면: --select=<번호> 로 실행하거나 seed.txt 를 직접 편집하세요.")

    return candidates_file, seed_file


def main():
    parser = argparse.ArgumentParser(description="Generate homage novel seeds from reference DNA")
    parser.add_argument("--voice", type=str, required=True, help="Reference name for voice DNA")
    parser.add_argument("--plot", type=str, required=True, help="Reference name for plot DNA")
    parser.add_argument("--mechanics", type=str, default="", help="Comma-separated reference names for mechanics")
    parser.add_argument("--idea", type=str, default="", help="Optional author premise/idea")
    parser.add_argument("--genre", type=str, default="", help="Target novel genre (e.g. 무협, 판타지, 현대미스터리, SF, 스릴러, 일상드라마)")
    parser.add_argument("--lang", type=str, default="ko", choices=["ko", "en"], help="Target novel language")
    parser.add_argument("--count", type=int, default=5, help="Number of seeds to generate")
    parser.add_argument("--select", type=int, default=0, help="Automatically save seed N (1-based) to seed.txt")
    args = parser.parse_args()

    mechanics = [m.strip() for m in args.mechanics.split(",") if m.strip()]
    if not mechanics:
        mechanics = [args.voice, args.plot]

    genre_msg = f" (Genre: {args.genre})" if args.genre else ""
    print(f"[*] Synthesizing {args.count} homage seeds{genre_msg} (Voice: {args.voice}, Plot: {args.plot})...")
    seeds = generate_homage_seeds(
        voice_ref=args.voice,
        plot_ref=args.plot,
        mechanics_refs=mechanics,
        idea=args.idea,
        genre=args.genre,
        lang=args.lang,
        count=args.count,
    )

    for s in seeds:
        print("\n" + "=" * 60)
        print(s)

    save_candidates_and_seed(
        seeds=seeds,
        base_dir=BASE_DIR,
        select=args.select,
        voice=args.voice,
        plot=args.plot,
        genre=args.genre,
    )



if __name__ == "__main__":
    main()
