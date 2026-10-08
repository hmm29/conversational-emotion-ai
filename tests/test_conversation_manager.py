import json

from src.conversation_manager import ConversationManager, PersonalityProfile
from src.emotion_analyzer import KeywordEmotionAnalyzer, keyword_emotions
from src.response_generator import DEFAULT_STRATEGIES, EmotionAwareResponseGenerator
from tests.fakes import FakeOpenAI, raises


def make_manager(client=None):
    generator = EmotionAwareResponseGenerator(client=client, strategies=DEFAULT_STRATEGIES)
    return ConversationManager(KeywordEmotionAnalyzer(), generator)


def test_process_message_records_a_turn():
    manager = make_manager(FakeOpenAI(reply="Glad to hear it."))
    turn = manager.process_message("  I am happy today  ")
    assert turn.user_message == "I am happy today"
    assert turn.bot_response == "Glad to hear it."
    assert turn.emotion_result.dominant_emotion == "joy"
    assert turn.approach == "amplify_positive"
    assert manager.turns == [turn]


def test_blank_message_is_rejected():
    manager = make_manager()
    assert raises(ValueError, manager.process_message, "   ")
    assert manager.turns == []


def test_earlier_turns_and_trend_reach_the_model():
    client = FakeOpenAI(reply="ok")
    manager = make_manager(client)
    manager.process_message("I am sad")
    manager.process_message("still sad")

    second_request = client.requests[1]["messages"]
    assert [m["content"] for m in second_request[1:]] == ["I am sad", "ok", "still sad"]
    assert "sadness 0.30" in second_request[0]["content"]  # trend from the first message


def test_summary_and_approach_counts():
    manager = make_manager()
    assert manager.summary() == {"turns": 0}
    for text in ["I am happy", "I am sad", "so sad and lonely"]:
        manager.process_message(text)
    summary = manager.summary()
    assert summary["turns"] == 3
    assert summary["most_common_emotion"] == "sadness"
    assert summary["approach_counts"] == {"amplify_positive": 1, "empathetic_support": 2}


def test_export_is_valid_json_with_every_turn():
    manager = make_manager()
    manager.process_message("haha that was funny")
    exported = json.loads(manager.export_json())
    assert exported["summary"]["turns"] == 1
    turn = exported["turns"][0]
    assert turn["user"] == "haha that was funny"
    assert turn["dominant_emotion"] == "amusement"
    assert turn["emotion_source"] == "keywords"
    assert turn["used_fallback"] is True
    assert set(exported["profile"]) == set(PersonalityProfile().traits)


def test_clear_resets_everything():
    manager = make_manager()
    manager.process_message("I am angry")
    manager.clear()
    assert manager.turns == []
    assert manager.emotion_history.history == []
    assert manager.profile.update_count == 0


def test_profile_moves_with_the_conversation_and_stays_in_range():
    profile = PersonalityProfile()
    for _ in range(50):
        profile.update(keyword_emotions("haha so funny, but I am sad sad sad"))
    assert profile.traits["humor_appreciation"] > 0.5
    assert profile.traits["support_seeking"] > 0.5
    assert profile.traits["conversation_depth"] < 0.5  # short messages
    assert all(0.0 <= value <= 1.0 for value in profile.traits.values())
