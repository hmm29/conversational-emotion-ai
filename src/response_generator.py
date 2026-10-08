"""Response generation.

Picks a response approach from the detected emotion, builds a system prompt
for it, and asks an OpenAI chat model for the reply. If no client is
configured, or the call fails, a short canned reply is returned instead.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .emotion_analyzer import EmotionResult

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "emotions_config.yaml"
BALANCED = "balanced_engagement"

# Below this score the detected emotion is too weak to act on.
# The value is a starting point and has not been calibrated against data.
MIN_CONFIDENCE = 0.1

DEFAULT_STRATEGIES: Dict[str, Dict[str, Any]] = {
    "high_positive": {
        "approach": "amplify_positive",
        "emotions": ["joy", "excitement", "amusement", "enthusiasm", "ecstasy", "pride", "triumph", "gratitude", "love", "admiration"],
    },
    "moderate_positive": {
        "approach": "gentle_encouragement",
        "emotions": ["contentment", "interest", "satisfaction", "calmness", "relief", "determination"],
    },
    "negative": {
        "approach": "empathetic_support",
        "emotions": ["sadness", "anger", "fear", "disappointment", "shame", "anxiety", "distress", "annoyance", "guilt", "embarrassment", "tiredness", "pain"],
    },
}

BASE_PROMPT = (
    "You are a conversational assistant that pays attention to how the user feels. "
    "Reply in two to four sentences, naturally, without naming the emotion scores."
)

APPROACH_PROMPTS = {
    "amplify_positive": (
        "The user seems to be feeling good. Match their energy without overdoing it, "
        "acknowledge what they are happy about, and ask one follow-up question."
    ),
    "gentle_encouragement": (
        "The user seems calm or mildly positive. Be warm and interested, and help them "
        "build on what they said."
    ),
    "empathetic_support": (
        "The user seems to be having a hard time. Acknowledge the feeling first. Do not "
        "rush to fix it or cheer them up. Use calm language and offer to hear more."
    ),
    BALANCED: (
        "The user's emotional state is neutral or unclear. Be friendly and curious, and "
        "ask a question that helps you understand them better."
    ),
}

TEMPERATURES = {
    "amplify_positive": 0.8,
    "gentle_encouragement": 0.6,
    "empathetic_support": 0.4,
    BALANCED: 0.7,
}

FALLBACK_REPLIES = {
    "amplify_positive": "That sounds great. What's been the best part of it?",
    "gentle_encouragement": "That sounds good. Tell me more about it?",
    "empathetic_support": "That sounds hard. I'm here to listen if you want to say more.",
    BALANCED: "Thanks for sharing that. What's on your mind?",
}


@dataclass
class ConversationContext:
    """Everything the generator needs for one reply."""

    user_message: str
    emotion_result: EmotionResult
    conversation_history: List[Dict[str, str]]  # [{"user": ..., "bot": ...}]
    emotion_trend: Dict[str, float]


@dataclass
class GeneratedResponse:
    text: str
    approach: str
    used_fallback: bool


def load_strategies(config_path: Path = DEFAULT_CONFIG) -> Dict[str, Dict[str, Any]]:
    """Read emotion-to-approach strategies from YAML, or use the defaults."""
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            strategies = (yaml.safe_load(file) or {}).get("response_strategies", {})
        valid = {
            name: strategy
            for name, strategy in strategies.items()
            if isinstance(strategy, dict) and strategy.get("approach") in APPROACH_PROMPTS
        }
        return valid or DEFAULT_STRATEGIES
    except (OSError, yaml.YAMLError, AttributeError) as error:
        logger.warning("Could not load %s, using default strategies: %s", config_path, error)
        return DEFAULT_STRATEGIES


def choose_approach(result: EmotionResult, strategies: Dict[str, Dict[str, Any]]) -> str:
    """Map the dominant emotion to a response approach."""
    if result.confidence < MIN_CONFIDENCE:
        return BALANCED
    for strategy in strategies.values():
        if result.dominant_emotion in strategy.get("emotions", []):
            return strategy["approach"]
    return BALANCED


def format_trend(trend: Dict[str, float], top_n: int = 3) -> str:
    ranked = sorted(trend.items(), key=lambda item: item[1], reverse=True)[:top_n]
    ranked = [(name, score) for name, score in ranked if score > 0]
    if not ranked:
        return "no earlier messages"
    return ", ".join(f"{name} {score:.2f}" for name, score in ranked)


def build_system_prompt(approach: str, context: ConversationContext) -> str:
    result = context.emotion_result
    emotion_note = (
        f"Detected emotion: {result.dominant_emotion} (score {result.confidence:.2f}). "
        f"Recent trend: {format_trend(context.emotion_trend)}."
    )
    return f"{BASE_PROMPT}\n\n{APPROACH_PROMPTS[approach]}\n\n{emotion_note}"


def build_messages(context: ConversationContext, system_prompt: str, max_turns: int = 6) -> List[Dict[str, str]]:
    messages = [{"role": "system", "content": system_prompt}]
    for turn in context.conversation_history[-max_turns:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["bot"]})
    messages.append({"role": "user", "content": context.user_message})
    return messages


class EmotionAwareResponseGenerator:
    """Generate a reply whose tone follows the detected emotion.

    `client` is anything with the OpenAI SDK's `chat.completions.create`
    method. Pass `api_key` to build a real client, or neither to run with
    canned replies only.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        client: Any = None,
        strategies: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        if client is None and api_key:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self.client = client
        self.model = model
        self.strategies = strategies or load_strategies()

    @property
    def has_model(self) -> bool:
        return self.client is not None

    def generate_response(self, context: ConversationContext) -> GeneratedResponse:
        approach = choose_approach(context.emotion_result, self.strategies)
        if self.client is None:
            return GeneratedResponse(FALLBACK_REPLIES[approach], approach, used_fallback=True)
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=build_messages(context, build_system_prompt(approach, context)),
                temperature=TEMPERATURES[approach],
                max_tokens=200,
            )
            text = (completion.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("empty completion")
            return GeneratedResponse(text, approach, used_fallback=False)
        except Exception as error:  # noqa: BLE001 - keep the conversation going
            logger.warning("OpenAI call failed, using canned reply: %s", error)
            return GeneratedResponse(FALLBACK_REPLIES[approach], approach, used_fallback=True)
