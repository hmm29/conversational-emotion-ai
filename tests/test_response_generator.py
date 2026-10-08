from pathlib import Path

from src.emotion_analyzer import keyword_emotions
from src.response_generator import (
    APPROACH_PROMPTS,
    BALANCED,
    DEFAULT_STRATEGIES,
    FALLBACK_REPLIES,
    ConversationContext,
    EmotionAwareResponseGenerator,
    build_messages,
    build_system_prompt,
    choose_approach,
    format_trend,
    load_strategies,
)
from tests.fakes import FakeOpenAI


def context_for(text, history=None, trend=None):
    return ConversationContext(
        user_message=text,
        emotion_result=keyword_emotions(text),
        conversation_history=history or [],
        emotion_trend=trend or {},
    )


def test_repo_config_loads_and_is_valid():
    strategies = load_strategies()
    assert strategies
    for strategy in strategies.values():
        assert strategy["approach"] in APPROACH_PROMPTS
        assert strategy["emotions"]


def test_missing_config_falls_back_to_defaults():
    assert load_strategies(Path("does/not/exist.yaml")) == DEFAULT_STRATEGIES


def test_choose_approach_by_dominant_emotion():
    assert choose_approach(keyword_emotions("I am so happy"), DEFAULT_STRATEGIES) == "amplify_positive"
    assert choose_approach(keyword_emotions("I feel sad and lonely"), DEFAULT_STRATEGIES) == "empathetic_support"
    assert choose_approach(keyword_emotions("wow"), DEFAULT_STRATEGIES) == BALANCED  # surprise is unlisted
    assert choose_approach(keyword_emotions("the report is due Friday"), DEFAULT_STRATEGIES) == BALANCED


def test_system_prompt_carries_approach_and_emotion():
    context = context_for("I am furious", trend={"anger": 0.4, "joy": 0.0})
    prompt = build_system_prompt("empathetic_support", context)
    assert APPROACH_PROMPTS["empathetic_support"] in prompt
    assert "anger" in prompt
    assert "anger 0.40" in prompt


def test_format_trend_with_no_history():
    assert format_trend({}) == "no earlier messages"


def test_messages_include_recent_history_only():
    history = [{"user": f"u{i}", "bot": f"b{i}"} for i in range(10)]
    messages = build_messages(context_for("latest", history=history), "SYSTEM", max_turns=2)
    assert [m["content"] for m in messages] == ["SYSTEM", "u8", "b8", "u9", "b9", "latest"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user", "assistant", "user"]


def test_generate_uses_the_model_reply():
    client = FakeOpenAI(reply="  That is wonderful news!  ")
    generator = EmotionAwareResponseGenerator(client=client, model="test-model", strategies=DEFAULT_STRATEGIES)

    response = generator.generate_response(context_for("I am so happy"))

    assert response.text == "That is wonderful news!"
    assert response.approach == "amplify_positive"
    assert response.used_fallback is False
    request = client.requests[0]
    assert request["model"] == "test-model"
    assert request["temperature"] == 0.8
    assert request["messages"][-1] == {"role": "user", "content": "I am so happy"}


def test_generate_falls_back_when_the_model_call_fails():
    generator = EmotionAwareResponseGenerator(client=FakeOpenAI(error=RuntimeError("rate limited")), strategies=DEFAULT_STRATEGIES)
    response = generator.generate_response(context_for("I feel sad"))
    assert response.used_fallback is True
    assert response.text == FALLBACK_REPLIES["empathetic_support"]


def test_generate_falls_back_on_an_empty_reply():
    generator = EmotionAwareResponseGenerator(client=FakeOpenAI(reply="   "), strategies=DEFAULT_STRATEGIES)
    assert generator.generate_response(context_for("hello")).used_fallback is True


def test_generate_without_a_client_uses_canned_replies():
    generator = EmotionAwareResponseGenerator(strategies=DEFAULT_STRATEGIES)
    assert generator.has_model is False
    response = generator.generate_response(context_for("hello there"))
    assert response.used_fallback is True
    assert response.text == FALLBACK_REPLIES[BALANCED]
