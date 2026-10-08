"""Conversation state: turns, emotion history and a running user profile."""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .emotion_analyzer import EmotionHistory, EmotionResult
from .response_generator import ConversationContext, EmotionAwareResponseGenerator

NEGATIVE_EMOTIONS = ("sadness", "fear", "anger", "disappointment", "shame", "anxiety", "distress")
LONG_MESSAGE_WORDS = 25


@dataclass
class ConversationTurn:
    """One user message, the analysis of it, and the reply."""

    user_message: str
    bot_response: str
    emotion_result: EmotionResult
    approach: str
    used_fallback: bool
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "user": self.user_message,
            "bot": self.bot_response,
            "dominant_emotion": self.emotion_result.dominant_emotion,
            "confidence": round(self.emotion_result.confidence, 3),
            "emotion_source": self.emotion_result.source,
            "top_emotions": {name: round(score, 3) for name, score in self.emotion_result.top(5)},
            "approach": self.approach,
            "used_fallback": self.used_fallback,
        }


class PersonalityProfile:
    """A rough running profile of how the user has been talking.

    Four traits start at 0.5 and are nudged by simple rules after each
    message. This is a heuristic summary of the conversation so far, not a
    psychological assessment.
    """

    def __init__(self):
        self.traits = {
            "emotional_expressivity": 0.5,
            "humor_appreciation": 0.5,
            "support_seeking": 0.5,
            "conversation_depth": 0.5,
        }
        self.update_count = 0

    def update(self, result: EmotionResult) -> None:
        self.update_count += 1
        rate = min(0.1, 1.0 / self.update_count)

        self._nudge("emotional_expressivity", rate if result.confidence > 0.3 else -rate / 2)
        if result.emotions.get("amusement", 0.0) > 0.2:
            self._nudge("humor_appreciation", rate)
        if sum(result.emotions.get(name, 0.0) for name in NEGATIVE_EMOTIONS) > 0.3:
            self._nudge("support_seeking", rate)
        long_message = len(result.text.split()) >= LONG_MESSAGE_WORDS
        self._nudge("conversation_depth", rate if long_message else -rate / 2)

    def _nudge(self, trait: str, amount: float) -> None:
        self.traits[trait] = min(1.0, max(0.0, self.traits[trait] + amount))


class ConversationManager:
    """Run a conversation: analyze each message, generate a reply, keep history."""

    def __init__(self, analyzer, generator: EmotionAwareResponseGenerator, history_size: int = 10):
        self.analyzer = analyzer
        self.generator = generator
        self.emotion_history = EmotionHistory(max_history=history_size)
        self.profile = PersonalityProfile()
        self.turns: List[ConversationTurn] = []

    def process_message(self, text: str) -> ConversationTurn:
        text = text.strip()
        if not text:
            raise ValueError("message must not be blank")

        result = self.analyzer.analyze_emotion(text)
        context = ConversationContext(
            user_message=text,
            emotion_result=result,
            conversation_history=[{"user": t.user_message, "bot": t.bot_response} for t in self.turns],
            emotion_trend=self.emotion_history.get_emotion_trend(),
        )
        response = self.generator.generate_response(context)

        self.emotion_history.add_emotion(result)
        self.profile.update(result)
        turn = ConversationTurn(
            user_message=text,
            bot_response=response.text,
            emotion_result=result,
            approach=response.approach,
            used_fallback=response.used_fallback,
            timestamp=datetime.now(),
        )
        self.turns.append(turn)
        return turn

    def approach_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for turn in self.turns:
            counts[turn.approach] = counts.get(turn.approach, 0) + 1
        return counts

    def summary(self) -> Dict[str, Any]:
        if not self.turns:
            return {"turns": 0}
        confidences = [turn.emotion_result.confidence for turn in self.turns]
        sequence = [turn.emotion_result.dominant_emotion for turn in self.turns]
        return {
            "turns": len(self.turns),
            "average_confidence": round(sum(confidences) / len(confidences), 3),
            "most_common_emotion": max(sorted(set(sequence)), key=sequence.count),
            "approach_counts": self.approach_counts(),
        }

    def export_json(self) -> str:
        """The whole conversation as a JSON string, for download."""
        return json.dumps(
            {
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "summary": self.summary(),
                "profile": {name: round(value, 3) for name, value in self.profile.traits.items()},
                "turns": [turn.to_dict() for turn in self.turns],
            },
            indent=2,
        )

    def clear(self) -> None:
        self.turns = []
        self.emotion_history.clear()
        self.profile = PersonalityProfile()
