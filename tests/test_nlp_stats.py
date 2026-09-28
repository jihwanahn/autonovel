from nlp_stats import analyze_text_style


def test_analyze_text_style_korean():
    sample_text = """
    "네가 정말 그 일을 할 수 있겠느냐?" 노인이 차가운 목소리로 물었다.
    청년은 주먹을 쥐었다. 손바닥에 서늘한 땀이 맺혔다.
    "해보지 않고는 모릅니다."
    바람이 불어와 대나무 숲을 흔들었다. 심장이 빠르게 뛰기 시작했다.
    """
    stats = analyze_text_style(sample_text, lang="ko")
    assert stats["sentence_count"] >= 4
    assert 10 <= stats["avg_sentence_len"] <= 40
    assert 0.2 <= stats["dialogue_ratio"] <= 0.7
    assert "sensory_keywords" in stats
    assert len(stats["top_vocabulary_clusters"]) > 0


def test_analyze_text_style_english():
    sample_text = """
    "Are you certain of this?" the elder whispered.
    The boy tightened his grip on the bronze hilt. The cold metal bit into his skin.
    He stepped into the shadows without another word.
    """
    stats = analyze_text_style(sample_text, lang="en")
    assert stats["sentence_count"] >= 3
    assert stats["dialogue_ratio"] > 0.1
