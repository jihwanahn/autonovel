import pytest
from pathlib import Path
from build_homage_foundation import build_foundation_docs


def test_build_foundation_docs_mock(tmp_path):
    seed_file = tmp_path / "seed.txt"
    seed_file.write_text(
        """TITLE: 저승 유실물 보관소
HOOK: 기억을 잃은 사신이 영혼들의 유품을 정리하며 잊힌 진실을 찾는 이야기.
WORLD: 저승과 이승의 경계에 위치한 안개 낀 회랑.
POV: 1인칭 독백 시점
THEME: 기억을 잃는다는 것의 의미
""",
        encoding="utf-8",
    )

    build_foundation_docs(seed_path=seed_file, output_dir=tmp_path, lang="ko", mock=True)

    assert (tmp_path / "voice.md").exists()
    assert (tmp_path / "world.md").exists()
    assert (tmp_path / "characters.md").exists()
    assert (tmp_path / "outline.md").exists()
    assert (tmp_path / "canon.md").exists()

    voice_content = (tmp_path / "voice.md").read_text(encoding="utf-8")
    assert "Part 1: Guardrails" in voice_content
    assert "Part 2: Voice Identity" in voice_content

    outline_content = (tmp_path / "outline.md").read_text(encoding="utf-8")
    assert "### Ch 1:" in outline_content
