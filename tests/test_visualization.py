import pytest

pytest.importorskip("plotly")

from src.conversation_manager import ConversationManager  # noqa: E402
from src.emotion_analyzer import KeywordEmotionAnalyzer  # noqa: E402
from src.response_generator import DEFAULT_STRATEGIES, EmotionAwareResponseGenerator  # noqa: E402
from src.visualization import approach_pie, emotion_radar, emotion_timeline, profile_bars  # noqa: E402


@pytest.fixture()
def manager():
    manager = ConversationManager(KeywordEmotionAnalyzer(), EmotionAwareResponseGenerator(strategies=DEFAULT_STRATEGIES))
    for text in ["I am happy", "now I am sad", "haha funny"]:
        manager.process_message(text)
    return manager


def test_radar_closes_the_shape(manager):
    figure = emotion_radar({"joy": 0.6, "fear": 0.2, "anger": 0.0}, top_n=2)
    trace = figure.data[0]
    assert list(trace.theta) == ["Joy", "Fear", "Joy"]
    assert list(trace.r) == [0.6, 0.2, 0.6]


def test_radar_handles_all_zero_scores():
    assert emotion_radar({"joy": 0.0}).data[0].r[0] == 0.0


def test_timeline_has_one_line_per_leading_emotion(manager):
    figure = emotion_timeline(manager.turns)
    names = {trace.name for trace in figure.data}
    assert names == {"Joy", "Sadness", "Amusement"}
    assert all(list(trace.x) == [1, 2, 3] for trace in figure.data)


def test_pie_and_profile(manager):
    pie = approach_pie(manager.approach_counts())
    assert sum(pie.data[0].values) == 3
    bars = profile_bars(manager.profile.traits)
    assert len(bars.data[0].x) == 4
