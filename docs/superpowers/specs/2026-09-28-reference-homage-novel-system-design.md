# Reference-Driven Homage Novel Generation System Design

**Date:** 2026-09-28  
**Status:** Approved  
**Author:** Pair Programming (Antigravity IDE & User)  
**Target Repository:** `d:/01_Career/novel_prj/autonovel`

---

## 1. Executive Summary & Objective

The goal of this system is to evolve `autonovel` beyond static, single-genre seed generation (previously hardcoded in `seed.py` for Western fantasy) into a **Reference-Driven Novel Deconstruction & Homage Pipeline**.

Rather than copying or plagiarizing text, the system reverse-engineers the structural and stylistic DNA of exemplary published novels (e.g., EPUB / text files such as 『달러구트 꿈 백화점』, 『광마회귀』), extracts modular craft profiles (Prose Style & Rhythm, Plot Beats & Tension, Core Entertainment / Trope Mechanics), and synthesizes completely original novel concepts through cross-pollination (e.g., combining the distinctive monologue rhythm of 『광마회귀』 with the cozy, imaginative episodic wonder of 『달러구트 꿈 백화점』).

Crucially, the workflow incorporates **Human-in-the-Loop Review Gates**, empowering the author to inspect, tweak, inject ideas, and approve blueprints at every milestone.

---

## 2. Key Requirements & Design Principles

1. **Direct EPUB Ingestion**: Directly accept `.epub` and `.txt` files without requiring manual file conversions.
2. **Modular DNA Extraction**: Decouple novel elements into independent, reusable assets stored under `references/<name>/`:
   - **Voice & Prose DNA**: Sentence length distributions, dialogue/exposition ratios, sensory keyword density, vocabulary wells.
   - **Plot & Structural DNA**: 3-act beats (Save the Cat), scene pacing curves, chapter cliffhangers.
   - **Entertainment & Tension DNA**: Core dilemma engines, dramatic irony, curiosity gaps, catharsis formulas.
3. **Cross-Reference Synthesis (Mix & Match)**: Enable arbitrary pairing of DNA profiles (e.g., `--voice "광마회귀" --plot "달러구트"`).
4. **Anti-Plagiarism Guardrails (Safe Abstraction)**:
   - Extract generalized dramatic principles rather than specific lore.
   - Maintain a banned-names/proper-nouns registry per reference to ensure no direct names, locations, or identical incident sequences are copied.
5. **Multi-Language Support (Korean & English)**:
   - Provide Korean prompt templates with natural syntax (no translationese/번역투).
   - Korean speech style enforcement (해라체, 하오체, 해요체 등).
   - Korean-specific anti-slop guidelines (`ANTI-SLOP-KO.md`) and Korean sentence metrics (`voice_fingerprint_ko.py`).
6. **Human-in-the-Loop Gates**: Allow author intervention before moving between pipeline phases.

---

## 3. Architecture & Subsystems

```
[Reference EPUB / TXT Files]
  │
  ▼
┌────────────────────────────────────────────────────────┐
│ Subsystem 1: EPUB Parsing & Reference Deconstruction    │
│  - epub_parser.py                                      │
│  - analyze_reference.py                                │
└────────────────────────────────────────────────────────┘
  │
  ├──► Output: references/<name>/ (voice_dna.json, plot_dna.json, etc.)
  │
  ▼ [Gate 1: Author Inspects / Curates DNA Library]
┌────────────────────────────────────────────────────────┐
│ Subsystem 2: Homage Seed Synthesizer                   │
│  - seed_homage.py                                      │
└────────────────────────────────────────────────────────┘
  │
  ├──► Output: seed.txt (Chosen from 5 candidates or author-refined)
  │
  ▼ [Gate 2: Author Finalizes Seed Concept]
┌────────────────────────────────────────────────────────┐
│ Subsystem 3: Homage Foundation Builder                 │
│  - build_homage_foundation.py                          │
└────────────────────────────────────────────────────────┘
  │
  ├──► Output: world.md, characters.md, outline.md, voice.md, canon.md
  │
  ▼ [Gate 3: Author Approves Planning Documents]
┌────────────────────────────────────────────────────────┐
│ Subsystem 4: Drafting, Anti-Slop & Quality Evaluation   │
│  - draft_chapter.py (with Korean/English templates)    │
│  - voice_fingerprint_ko.py                             │
│  - evaluate.py & review.py                             │
└────────────────────────────────────────────────────────┘
  │
  ▼ [Gate 4: Chapter Revision Briefs & Direct Edits]
[Final Manuscript & Export]
```

---

## 4. Component Details

### 4.1 Subsystem 1: EPUB Parsing & Reference Analysis (`analyze_reference.py`, `epub_parser.py`)

- **`epub_parser.py`**:
  - Unzips and parses EPUB HTML/XHTML components without external heavy binary dependencies (`zipfile` + standard HTML parser / BeautifulSoup).
  - Strips HTML markup, cleans whitespace, identifies chapter breaks, and produces an ordered list of clean chapter texts.
- **`analyze_reference.py`**:
  - **Stage A (Quantitative NLP Analysis)**:
    - Calculates average sentence length (characters and syllables), variance, dialogue percentage (via Korean quotes `"..."`), and sensory word frequencies.
    - Generates 3~5 dominant vocabulary wells (e.g. 무공/신체/자연 or 상점/감정/환상).
  - **Stage B (Narrative Craft Deconstruction via LLM)**:
    - Samples key milestones (Chapters 1~5 for voice & promise, Midpoint, Climax).
    - Extracts 3-Act beats, hook mechanisms, protagonist dilemma formulas, and tension pacing.
    - Applies safe abstraction: removes all proper nouns, locations, and concrete lore.
  - **Storage**: Saved into `references/<name>/`:
    - `summary.md`: Human-readable summary for the author.
    - `voice_dna.json`: Sentence length target, dialogue ratio, vocabulary wells.
    - `plot_dna.json`: Beat sheet targets, cliffhanger frequency.
    - `entertainment_dna.md`: Dramatic engine, humor/tension techniques.

### 4.2 Subsystem 2: Homage Seed Synthesizer (`seed_homage.py`)

- Replaces / augments `seed.py`.
- **Inputs**:
  - `--voice <ref_name>`: Source for voice & style DNA.
  - `--plot <ref_name>`: Source for narrative structure DNA.
  - `--mechanics <ref_name1,ref_name2>`: Source for world/conflict mechanisms.
  - `--idea "<text>"`: Optional author logline/premise.
  - `--lang ko|en`: Target novel language (default `ko`).
  - `--count <int>`: Number of candidates to generate (default 5).
- **Output format**: 5 distinct concepts formatted with:
  1. Title & Logline
  2. Homage Inspiration Map (how the DNAs were blended)
  3. Core Speculative Element & Cost
  4. Protagonist Internal Flaw vs External Stakes
  5. 3-Act Turning Points
  6. Anti-Plagiarism Validation Checklist
- The author picks a candidate and writes it to `seed.txt`.

### 4.3 Subsystem 3: Homage Foundation Builder (`build_homage_foundation.py`)

- Reads `seed.txt` and the referenced DNAs.
- Injects the tailored Korean/English craft principles to generate:
  - `voice.md`: Localized style guide (vocabulary wells, sentence rhythm, banned phrases).
  - `world.md`: Rules, setting, sensory anchors.
  - `characters.md`: Cast, internal/external stakes, distinct speech styles.
  - `outline.md`: Chapter-by-chapter outline (15~20 chapters default) with explicit scene goals, conflicts, and cliffhangers.
  - `canon.md`: Factual database to prevent continuity errors.
- Includes `--inspect` flag so the user can review before advancing.

### 4.4 Subsystem 4: Korean-Aware Drafting & Evaluation

- **`ANTI-SLOP-KO.md`**:
  - Bans Korean AI clichés (*"입꼬리를 슬쩍 올렸다"*, *"씁쓸한 미소를 지었다"*, *"마치 ~인 것만 같았다"*, *"알 수 없는 감정이 밀려왔다"* 등).
  - Enforces "Show, Don't Tell" and forbids emotion-labeling verbs.
- **`voice_fingerprint_ko.py`**:
  - Analyzes drafted chapters for sentence rhythm, dialogue ratios, and vocabulary well adherence against `voice.md`.
- **Language Switcher**:
  - Configuration in `project.json` or CLI flag (`--lang ko` vs `--lang en`) routes drafting prompts to either Korean-native prompts or original English prompts.

---

## 5. Directory & File Structure

```
autonovel/
├── references/                 # Reusable Reference DNA Library
│   ├── 광마회귀/
│   │   ├── summary.md
│   │   ├── voice_dna.json
│   │   ├── plot_dna.json
│   │   └── entertainment_dna.md
│   └── 달러구트_꿈_백화점/
│       ├── summary.md
│       ├── voice_dna.json
│       ├── plot_dna.json
│       └── entertainment_dna.md
├── epub_parser.py             # Pure-Python EPUB extractor
├── analyze_reference.py       # Reference deconstruction tool
├── seed_homage.py             # Homage concept synthesizer
├── build_homage_foundation.py # Foundation generator (world, chars, outline, voice)
├── voice_fingerprint_ko.py    # Korean prose quantitative fingerprinting
├── ANTI-SLOP-KO.md            # Korean AI slop detection & craft rubric
├── docs/superpowers/specs/    # System specifications
└── ... (existing autonovel files)
```

---

## 6. Error Handling & Edge Cases

1. **Large EPUB Token Limits**: Full novels can contain 200k~500k words. The system uses full text for statistical calculations, but performs craft analysis using smart chapter sampling (Opening 1~5 chapters, Midpoint, Climax, Resolution) to fit comfortably within LLM context windows while maintaining analytical precision.
2. **Malformed EPUB Archives**: The EPUB parser handles both standard `container.xml` -> `content.opf` structures and fallbacks to direct directory scanning for XHTML files.
3. **Plagiarism Prevention**: Automated regex and semantic checks against reference character names, unique place names, and signature phrases ensure no direct copying.
4. **Antigravity Proxy Compatibility**: All LLM calls route through `antigravity_proxy.py` / `run_with_antigravity.py` or standard API keys seamlessly.

---

## 7. Verification & Testing Plan

1. **Test 1: EPUB Parsing**
   - Run `epub_parser.py` on `d:\01_Career\novel_prj\달러구트 꿈 백화점 (이미예) (z-library.sk, 1lib.sk, z-lib.sk).epub` and `d:\01_Career\novel_prj\광마회귀.epub`.
   - Verify chapter extraction and clean Korean text without residual HTML tags.
2. **Test 2: Reference Deconstruction**
   - Run `analyze_reference.py` on both references.
   - Verify `references/` output directories containing valid `voice_dna.json`, `plot_dna.json`, and `summary.md`.
3. **Test 3: Homage Seed Generation**
   - Run `seed_homage.py --voice "광마회귀" --plot "달러구트_꿈_백화점" --lang ko`.
   - Inspect generated concepts to verify clear homage integration and originality.
4. **Test 4: Foundation Document Generation**
   - Run `build_homage_foundation.py` to produce `world.md`, `characters.md`, `outline.md`, and `voice.md`.
   - Run `voice_fingerprint_ko.py` to ensure metric validation works as expected.
