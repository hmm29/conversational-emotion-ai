import json

from src.emotion_analyzer import (
    HUME_MAX_CHARS,
    EmotionHistory,
    HumeEmotionAnalyzer,
    KeywordEmotionAnalyzer,
    keyword_emotions,
    parse_hume_message,
)
from tests.fakes import FakeConnect, FakeSocket, hume_message, raises


def test_keywords_find_the_dominant_emotion():
    result = keyword_emotions("I am so happy, this is wonderful!")
    assert result.dominant_emotion == "joy"
    assert result.confidence == 0.6
    assert result.source == "keywords"


def test_keywords_match_whole_words_only():
    # "made" contains "mad" and "download" contains "down"; neither should count.
    result = keyword_emotions("I made a download script")
    assert result.dominant_emotion == "neutral"
    assert result.confidence == 0.0


def test_keywords_score_is_capped():
    result = keyword_emotions("sad sad sad sad sad sad")
    assert result.emotions["sadness"] == 1.0


def test_keyword_analyzer_interface():
    assert KeywordEmotionAnalyzer().analyze_emotion("haha that is funny").dominant_emotion == "amusement"


def test_top_skips_zero_scores():
    result = keyword_emotions("I am worried and a bit sad")
    assert {name for name, _ in result.top(5)} == {"sadness", "fear"}


def test_parse_hume_message_averages_across_predictions():
    message = json.loads(hume_message({"Joy": 0.8, "Sadness": 0.0}, {"Joy": 0.4, "Sadness": 0.2}))
    emotions = parse_hume_message(message)
    assert abs(emotions["joy"] - 0.6) < 1e-9
    assert abs(emotions["sadness"] - 0.1) < 1e-9


def test_parse_hume_message_rejects_errors_and_empty_payloads():
    assert raises(RuntimeError, parse_hume_message, {"error": "bad key", "code": "E0100"})
    assert raises(RuntimeError, parse_hume_message, {"language": {"predictions": []}})
    assert raises(RuntimeError, parse_hume_message, {})


def test_hume_analyzer_sends_text_and_returns_scores():
    socket = FakeSocket(reply=hume_message({"Anger": 0.7, "Joy": 0.1}))
    connect = FakeConnect(socket)
    analyzer = HumeEmotionAnalyzer("key-123", connect=connect)

    result = analyzer.analyze_emotion("This is infuriating")

    assert result.source == "hume"
    assert result.dominant_emotion == "anger"
    assert abs(result.confidence - 0.7) < 1e-9
    assert connect.calls[0][1] == "key-123"
    assert socket.sent == [{"models": {"language": {}}, "raw_text": True, "data": "This is infuriating"}]


def test_hume_analyzer_truncates_long_text():
    socket = FakeSocket(reply=hume_message({"Joy": 0.5}))
    HumeEmotionAnalyzer("key", connect=FakeConnect(socket)).analyze_emotion("a" * (HUME_MAX_CHARS + 50))
    assert len(socket.sent[0]["data"]) == HUME_MAX_CHARS


def test_hume_analyzer_falls_back_when_connection_fails():
    analyzer = HumeEmotionAnalyzer("key", connect=FakeConnect(error=OSError("no network")))
    result = analyzer.analyze_emotion("I am scared")
    assert result.source == "keywords"
    assert result.dominant_emotion == "fear"


def test_hume_analyzer_falls_back_on_error_payload():
    socket = FakeSocket(reply=json.dumps({"error": "invalid api key"}))
    result = HumeEmotionAnalyzer("key", connect=FakeConnect(socket)).analyze_emotion("so happy")
    assert result.source == "keywords"
    assert result.dominant_emotion == "joy"


def test_hume_analyzer_falls_back_on_timeout():
    socket = FakeSocket(error=TimeoutError())
    result = HumeEmotionAnalyzer("key", connect=FakeConnect(socket)).analyze_emotion("hello")
    assert result.source == "keywords"


def test_hume_analyzer_requires_a_key():
    assert raises(ValueError, HumeEmotionAnalyzer, "")


def test_history_keeps_the_most_recent_results():
    history = EmotionHistory(max_history=2)
    for text in ["happy", "sad", "angry"]:
        history.add_emotion(keyword_emotions(text))
    assert history.get_dominant_emotion_sequence() == ["sadness", "anger"]


def test_history_trend_is_an_average():
    history = EmotionHistory()
    assert history.get_emotion_trend() == {}
    history.add_emotion(keyword_emotions("happy"))
    history.add_emotion(keyword_emotions("the weather"))
    assert abs(history.get_emotion_trend()["joy"] - 0.15) < 1e-9
