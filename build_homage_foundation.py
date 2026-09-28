#!/usr/bin/env python3
"""
build_homage_foundation.py — Generates foundation planning documents
(voice.md, world.md, characters.md, outline.md, canon.md) from seed.txt and reference DNA.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")


def call_llm(prompt: str, system: str, max_tokens: int = 16000) -> str:
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def build_foundation_docs(
    seed_path: Path,
    output_dir: Path,
    voice_ref: str = "",
    plot_ref: str = "",
    genre: str = "",
    lang: str = "ko",
    mock: bool = False,
):
    seed_text = seed_path.read_text(encoding="utf-8")
    ref_dir = BASE_DIR / "references"

    v_dna = {}
    if voice_ref and (ref_dir / voice_ref / "voice_dna.json").exists():
        with open(ref_dir / voice_ref / "voice_dna.json", encoding="utf-8") as f:
            v_dna = json.load(f)

    p_dna = {}
    if plot_ref and (ref_dir / plot_ref / "plot_dna.json").exists():
        with open(ref_dir / plot_ref / "plot_dna.json", encoding="utf-8") as f:
            p_dna = json.load(f)

    # 1. Voice.md
    voice_base = (BASE_DIR / "voice.md").read_text(encoding="utf-8") if (BASE_DIR / "voice.md").exists() else ""
    part1_guardrails = voice_base.split("## Part 2:")[0] if "## Part 2:" in voice_base else "# Voice Profile\n"

    if mock or not API_KEY:
        part2_voice = f"""## Part 2: Voice Identity (Generated for this Novel)

### Tone
건조하지만 위트 있고, 깊은 통찰과 감정이 잔잔히 배어 나오는 독백조.

### Sentence Rhythm
평균 15-25자의 단문 위주로 빠른 호흡 유지. 행동과 감정의 변화 지점에서는 감각적인 짧은 문장 연타.

### Vocabulary Register
{', '.join(v_dna.get('vocabulary_wells', ['기억', '사서', '유실물', '저승', '바람', '손바닥']))}

### POV and Tense
{v_dna.get('pov', '1인칭 주인공 시점, 과거형.')}

### Dialogue Conventions
과장된 감정 표현을 배제하고 인물별 명확한 어조(하오체/해라체/존댓말) 차별화.

### Exemplar Passages
기억이란 기이한 것이다. 버릴 때는 아무런 무게도 없던 것들이, 이곳 유실물 보관소 선반에 얹히는 순간 한 사람의 생애보다 무거워진다.
"""
        world_text = f"""# WORLD BIBLE

## Core Setting
저승과 이승의 경계선에 존재하는 끝없는 서고와 유실물 보관소.

## Speculative Laws
1. 유품에 깃든 잔류 사념: 물건을 접촉하면 망자의 가장 강렬했던 감정의 파편을 감응할 수 있다.
2. 대가(Cost): 타인의 기억을 읽을 때마다 자신의 개인적 기억 일부가 마모된다.

## Locations
- 중앙 수장고: 수억 개의 기억함이 분류를 기다리는 거대한 홀.
- 안개의 문: 이승과 연결되는 유일한 통로.
"""
        characters_text = f"""# CHARACTERS

## 주인공 (POV: 1인칭)
- 역할: 저승 유실물 보관소의 3급 관리관
- 성격: 냉소적인 척하지만 집요한 의리를 지님.
- 말투: 담담하고 짧게 끊어 치는 어조.
- 결핍/욕망: 자신의 과거 기억이 완전히 지워져 있으나 그 빈자리를 두려워함.

## 보조 인물
- 역할: 오랜 시간 서고를 지켜온 수석 감식관
- 성격: 능글맞고 비밀이 많은 성격.
"""
        outline_text = f"""# OUTLINE

### Ch 1: 도착하지 않은 기억
- 비트 1: 안개 속에서 새로운 유실물 상자가 접수된다.
- 비트 2: 주인공이 상자를 개봉하며 금지된 표식을 발견한다.
- 클리프행어: 유품에 손을 대는 순간 익숙한 목소리가 들려온다.

### Ch 2: 망자의 미련
- 비트 1: 사라진 영혼의 행적을 추적하기 시작한다.
- 클리프행어: 서고 깊은 곳에서 규칙을 어긴 흔적이 포착된다.
"""
        canon_text = f"""# CANON DATABASE

## Core Rules
- 유실물 보관소 내에서는 폭력이 금지된다. (world.md)
- 유품의 사념은 3일이 지나면 자연 소멸한다. (world.md)

## Character Facts
- 주인공은 자신의 이름을 기억하지 못한다. (characters.md)
"""
    else:
        # Generate with LLM
        print("[*] Generating voice.md (Part 2)...")
        part2_prompt = f"""Generate Part 2: Voice Identity for this novel in {lang.upper()}.
SEED CONCEPT:
{seed_text}
REFERENCE VOICE DNA:
{json.dumps(v_dna, ensure_ascii=False, indent=2)}

Include sections:
### Tone
### Sentence Rhythm
### Vocabulary Register
### POV and Tense
### Dialogue Conventions
### Exemplar Passages (3-4 paragraphs)
"""
        part2_voice = "## Part 2: Voice Identity\n\n" + call_llm(part2_prompt, "You are a master literary voice stylist.", 4000)

        print("[*] Generating world.md...")
        genre_header = f"TARGET GENRE: {genre}\n" if genre else ""
        world_prompt = f"""Build complete world bible (WORLD.MD) for this premise in {lang.upper()}:
{genre_header}
SEED:
{seed_text}
Ensure the setting and rules fit the genre. Concrete, sensory geography and societal structures.
"""
        world_builder_role = f"You are a master {genre} worldbuilder." if genre else "You are a master fiction worldbuilder."
        world_text = call_llm(world_prompt, world_builder_role, 8000)

        print("[*] Generating characters.md...")
        char_prompt = f"""Build characters registry (CHARACTERS.MD) for this novel in {lang.upper()}:
{genre_header}
SEED:
{seed_text}
WORLD:
{world_text[:4000]}
Include Protagonist, Antagonist, and Key Supporting Cast with distinct speech styles and internal/external stakes.
"""
        characters_text = call_llm(char_prompt, f"You are an expert character designer specializing in {genre if genre else 'fiction'}.", 8000)

        print("[*] Generating outline.md...")
        outline_prompt = f"""Generate a 15-20 chapter OUTLINE.MD in {lang.upper()} using Save the Cat / 3-Act beats.
SEED:
{seed_text}
WORLD:
{world_text[:2000]}
CHARACTERS:
{characters_text[:2000]}
FORMAT EACH CHAPTER AS:
### Ch <N>: <Chapter Title>
- Beats: ...
- Pacing / Tension: ...
- Cliffhanger / Ending hook: ...
"""
        outline_text = call_llm(outline_prompt, "You are a novel outline architect.", 12000)

        print("[*] Generating canon.md...")
        canon_prompt = f"""Extract hard factual database (CANON.MD) from WORLD and CHARACTERS:
=== WORLD ===
{world_text[:4000]}
=== CHARACTERS ===
{characters_text[:4000]}
Format as categorized bullet points. Checkable facts only.
"""
        canon_text = call_llm(canon_prompt, "You are a continuity editor.", 6000)

    # Write files
    (output_dir / "voice.md").write_text(part1_guardrails.strip() + "\n\n" + part2_voice.strip() + "\n", encoding="utf-8")
    (output_dir / "world.md").write_text(world_text.strip() + "\n", encoding="utf-8")
    (output_dir / "characters.md").write_text(characters_text.strip() + "\n", encoding="utf-8")
    (output_dir / "outline.md").write_text(outline_text.strip() + "\n", encoding="utf-8")
    (output_dir / "canon.md").write_text(canon_text.strip() + "\n", encoding="utf-8")

    print(f"[+] All foundation planning documents successfully generated in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Build novel foundation planning documents from seed.txt")
    parser.add_argument("--seed", type=str, default="seed.txt", help="Path to seed.txt")
    parser.add_argument("--voice-ref", type=str, default="", help="Optional reference name for voice DNA")
    parser.add_argument("--plot-ref", type=str, default="", help="Optional reference name for plot DNA")
    parser.add_argument("--genre", type=str, default="", help="Target novel genre (e.g. 무협, 판타지, 현대미스터리, SF, 스릴러)")
    parser.add_argument("--lang", type=str, default="ko", choices=["ko", "en"], help="Target language")
    parser.add_argument("--inspect", action="store_true", help="Inspect generated planning docs (Review Gate 3)")
    args = parser.parse_args()

    seed_path = BASE_DIR / args.seed
    if not seed_path.exists():
        print(f"[-] Seed file not found: {seed_path}. Run seed_homage.py first.")
        sys.exit(1)

    build_foundation_docs(
        seed_path=seed_path,
        output_dir=BASE_DIR,
        voice_ref=args.voice_ref,
        plot_ref=args.plot_ref,
        genre=args.genre,
        lang=args.lang,
    )

    if args.inspect:
        print("\n" + "=" * 60)
        print("REVIEW GATE 3: FOUNDATION PLANNING DOCUMENTS")
        print("=" * 60)
        print(f"- voice.md: {len((BASE_DIR / 'voice.md').read_text(encoding='utf-8').splitlines())} lines")
        print(f"- world.md: {len((BASE_DIR / 'world.md').read_text(encoding='utf-8').splitlines())} lines")
        print(f"- characters.md: {len((BASE_DIR / 'characters.md').read_text(encoding='utf-8').splitlines())} lines")
        print(f"- outline.md: {len((BASE_DIR / 'outline.md').read_text(encoding='utf-8').splitlines())} lines")
        print(f"- canon.md: {len((BASE_DIR / 'canon.md').read_text(encoding='utf-8').splitlines())} lines")
        print("\nPlease review and refine these markdown files as desired before proceeding to chapter drafting!")


if __name__ == "__main__":
    main()
