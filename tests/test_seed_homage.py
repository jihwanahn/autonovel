import json
import pytest
from pathlib import Path
from seed_homage import generate_homage_seeds, save_candidates_and_seed


def test_generate_homage_seeds_mock(tmp_path):
    # Setup dummy reference profiles
    ref_dir = tmp_path / "references"
    v_dir = ref_dir / "ref_a"
    v_dir.mkdir(parents=True)
    with open(v_dir / "voice_dna.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "name": "ref_a",
                "pov": "1인칭",
                "voice_summary": "시니컬하고 빠른 리듬",
                "vocabulary_wells": ["주먹", "바람"],
            },
            f,
        )

    p_dir = ref_dir / "ref_b"
    p_dir.mkdir(parents=True)
    with open(p_dir / "plot_dna.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "name": "ref_b",
                "turning_point_pattern": "옴니버스식 감동과 치밀한 복선",
                "protagonist_dynamic": "상처 입은 치유자",
                "safe_abstraction_formula": "잃어버린 기억을 찾아주는 안내자 모델",
            },
            f,
        )

    seeds = generate_homage_seeds(
        voice_ref="ref_a",
        plot_ref="ref_b",
        mechanics_refs=["ref_a", "ref_b"],
        idea="기억을 잃은 사신의 유실물 센터",
        lang="ko",
        count=3,
        ref_base=ref_dir,
        mock=True,
    )
    assert len(seeds) == 3
    assert "TITLE:" in seeds[0]
    assert "HOOK:" in seeds[0]
    assert "HOMAGE MAP:" in seeds[0]
    assert "SAFE ABSTRACTION CHECK: PASSED" in seeds[0]


def test_save_candidates_and_seed_defaults(tmp_path):
    seeds = ["CONCEPT_1_CONTENT", "CONCEPT_2_CONTENT", "CONCEPT_3_CONTENT"]
    
    # 1. Default: seed.txt does not exist -> auto save concept 1, create candidates.md
    cand_file, seed_file = save_candidates_and_seed(seeds, base_dir=tmp_path, select=0)
    assert cand_file.exists()
    assert seed_file.exists()
    assert "CONCEPT_1_CONTENT" in cand_file.read_text(encoding="utf-8")
    assert "CONCEPT_3_CONTENT" in cand_file.read_text(encoding="utf-8")
    assert seed_file.read_text(encoding="utf-8") == "CONCEPT_1_CONTENT"

    # 2. Select specific concept #2
    cand_file, seed_file = save_candidates_and_seed(seeds, base_dir=tmp_path, select=2)
    assert seed_file.read_text(encoding="utf-8") == "CONCEPT_2_CONTENT"

    # 3. If seed.txt exists and select=0, preserve existing
    seed_file.write_text("CUSTOM_USER_SEED", encoding="utf-8")
    cand_file, seed_file = save_candidates_and_seed(seeds, base_dir=tmp_path, select=0)
    assert seed_file.read_text(encoding="utf-8") == "CUSTOM_USER_SEED"

