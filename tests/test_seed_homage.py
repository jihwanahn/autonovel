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
