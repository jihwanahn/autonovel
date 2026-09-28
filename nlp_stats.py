"""
nlp_stats.py — Quantitative prose and stylistic metrics calculator for Korean & English.
"""
import re
import statistics
from collections import Counter

SENSORY_LEXICON_KO = {
    "visual": ["빛", "어둠", "그림자", "붉은", "검은", "하얀", "푸른", "반짝", "눈빛", "형체"],
    "auditory": ["소리", "울림", "속삭", "비명", "정적", "바람", "쇠소리", "헐떡", "목소리"],
    "tactile": ["차가운", "서늘", "뜨거운", "온기", "손바닥", "살결", "거친", "압박", "통증", "땀"],
    "action": ["베다", "쥐다", "달리다", "딛다", "휘두르다", "멈추다", "부딪히다", "떨어지다"],
}

SENSORY_LEXICON_EN = {
    "visual": ["light", "dark", "shadow", "red", "black", "white", "blue", "gleam", "glance"],
    "auditory": ["sound", "whisper", "echo", "scream", "silence", "rattle", "hum", "voice"],
    "tactile": ["cold", "hot", "warmth", "skin", "sharp", "rough", "ache", "tremor", "sweat"],
    "action": ["strike", "grip", "run", "fall", "shatter", "step", "clash", "breathe"],
}


def analyze_text_style(text: str, lang: str = "ko") -> dict:
    cleaned = text.strip()
    if not cleaned:
        return {
            "sentence_count": 0,
            "avg_sentence_len": 0,
            "std_sentence_len": 0,
            "dialogue_ratio": 0.0,
            "sensory_density": 0.0,
            "sensory_keywords": {},
            "top_vocabulary_clusters": [],
        }

    # Extract dialogue (quotes: "..." or 「...」 or 『...』)
    dialogue_matches = re.findall(r'["“「『](.*?)["”」』]', cleaned)
    dialogue_chars = sum(len(m) for m in dialogue_matches)
    total_chars = max(len(cleaned), 1)
    dialogue_ratio = round(dialogue_chars / total_chars, 3)

    # Sentence segmentation
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', cleaned) if len(s.strip()) > 3]
    if not sentences:
        sentences = [cleaned]

    lengths = [len(s) for s in sentences]
    avg_len = round(statistics.mean(lengths), 1)
    std_len = round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0.0

    # Sensory analysis
    lexicon = SENSORY_LEXICON_KO if lang == "ko" else SENSORY_LEXICON_EN
    sensory_hits = Counter()
    for category, words in lexicon.items():
        for word in words:
            count = len(re.findall(re.escape(word), cleaned, flags=re.IGNORECASE))
            if count > 0:
                sensory_hits[category] += count

    total_sensory = sum(sensory_hits.values())
    sensory_density = round(total_sensory / (len(cleaned) / 1000), 2)  # per 1000 chars

    # Vocabulary clusters: significant content words (>2 chars)
    words = re.findall(r'[가-힣a-zA-Z]{2,}', cleaned)
    stop_words = {
        "있는", "것은", "그의", "그녀", "하지만", "그리고", "때문", "있다", "했다", "that", "this",
        "with", "from", "were", "been", "have", "they", "there"
    }
    filtered_words = [w for w in words if w not in stop_words]
    word_counts = Counter(filtered_words).most_common(15)

    return {
        "sentence_count": len(sentences),
        "avg_sentence_len": avg_len,
        "std_sentence_len": std_len,
        "dialogue_ratio": dialogue_ratio,
        "sensory_density": sensory_density,
        "sensory_keywords": dict(sensory_hits),
        "top_vocabulary_clusters": [w for w, _ in word_counts[:8]],
    }
