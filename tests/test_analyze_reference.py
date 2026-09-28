import json
import pytest
from pathlib import Path
from analyze_reference import run_analysis


def test_run_analysis_mock(tmp_path):
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text(
        """
    제1장 도의 길.
    "너는 오늘부터 미친 사내다." 스승이 말했다.
    주인공은 하늘을 올려다보았다. 눈이 내리고 있었다.
    """,
        encoding="utf-8",
    )

    out_dir = tmp_path / "references" / "test_ref"
    run_analysis(
        name="test_ref",
        input_path=sample_file,
        lang="ko",
        output_base=tmp_path / "references",
        mock_llm=True,
    )

    assert (out_dir / "summary.md").exists()
    assert (out_dir / "voice_dna.json").exists()
    assert (out_dir / "plot_dna.json").exists()
    assert (out_dir / "entertainment_dna.md").exists()

    with open(out_dir / "voice_dna.json", encoding="utf-8") as f:
        v_data = json.load(f)
        assert "avg_sentence_len" in v_data
        assert "dialogue_ratio" in v_data
        assert v_data["name"] == "test_ref"
