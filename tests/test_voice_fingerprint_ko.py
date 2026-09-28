from voice_fingerprint_ko import evaluate_korean_chapter_prose


def test_evaluate_korean_chapter_prose():
    chapter_text = """
    "그 문을 열지 마시오." 그가 경고했다.
    손잡이를 잡은 손가락에 소름이 돋았다. 등 뒤에서 바람이 불어왔다.
    그는 입꼬리를 슬쩍 올렸다.
    알 수 없는 위화감이 들었다.
    """
    res = evaluate_korean_chapter_prose(chapter_text, target_sentence_len=20.0)
    assert res["slop_hits"] >= 2  # "입꼬리를 슬쩍 올렸다", "알 수 없는 위화감" caught
    assert "avg_sentence_len" in res
    assert res["slop_penalty"] > 0.0
