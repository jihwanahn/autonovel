from pathlib import Path
from draft_chapter import build_chapter_prompt


def test_build_chapter_prompt_dynamic():
    seed_content = "TITLE: 저승의 유실물 보관소\nHOOK: 영혼들이 잃어버린 기억을 찾아주는 사신의 이야기"
    voice_content = "### POV and Tense\n1인칭 주인공 시점, 과거형."
    outline_entry = "### Ch 1: 첫 번째 유실물\n주인공이 잃어버린 기억함을 접수한다."

    prompt = build_chapter_prompt(
        chapter_num=1,
        title="저승의 유실물 보관소",
        voice_text=voice_content,
        chapter_outline=outline_entry,
        next_outline="(next chapter)",
        prev_tail="(first chapter)",
        canon_text="",
        world_text="",
        characters_text="",
    )
    assert "The Second Son of the House of Bells" not in prompt
    assert "Cass" not in prompt
    assert "저승의 유실물 보관소" in prompt
    assert "1인칭 주인공 시점" in prompt
