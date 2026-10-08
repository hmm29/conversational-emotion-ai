"""Emotion analysis.

Two analyzers share one interface, `analyze_emotion(text) -> EmotionResult`:

- `HumeEmotionAnalyzer` sends the text to Hume AI's Expression Measurement
  streaming API (language model) and averages the scores it returns.
- `KeywordEmotionAnalyzer` is a small keyword matcher. It needs no API key and
  is what the Hume analyzer falls back to when a call fails.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

HUME_STREAM_URL = "wss://api.hume.ai/v0/stream/models"
HUME_MAX_CHARS = 10_000  # documented limit per text payload
NEUTRAL = "neutral"

EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "joy": ["happy", "joy", "glad", "great", "awesome", "wonderful", "amazing", "delighted"],
    "excitement": ["excited", "thrilled", "pumped"],
    "sadness": ["sad", "depressed", "down", "unhappy", "miserable", "upset", "lonely"],
    "disappointment": ["disappointed", "letdown"],
    "anger": ["angry", "mad", "furious", "annoyed", "frustrated", "irritated"],
    "fear": ["scared", "afraid", "worried", "anxious", "nervous", "terrified"],
    "surprise": ["surprised", "shocked", "unexpected", "wow"],
    "amusement": ["funny", "hilarious", "laugh", "haha", "lol", "amusing"],
    "tiredness": ["tired", "exhausted", "drained"],
}


@dataclass
class EmotionResult:
    """Emotion scores for one piece of text."""

    emotions: Dict[str, float]
    dominant_emotion: str
    confidence: float
    text: str
    source: str  # "hume" or "keywords"
    timestamp: datetime = field(default_factory=datetime.now)

    def top(self, n: int = 3) -> List[tuple]:
        ranked = sorted(self.emotions.items(), key=lambda item: item[1], reverse=True)
        return [(name, score) for name, score in ranked[:n] if score > 0]


def _result(emotions: Dict[str, float], text: str, source: str) -> EmotionResult:
    if emotions and max(emotions.values()) > 0:
        dominant, confidence = max(emotions.items(), key=lambda item: item[1])
    else:
        dominant, confidence = NEUTRAL, 0.0
    return EmotionResult(
        emotions=emotions,
        dominant_emotion=dominant,
        confidence=float(confidence),
        text=text,
        source=source,
    )


def keyword_emotions(text: str) -> EmotionResult:
    """Score emotions by counting whole-word keyword matches.

    Each match adds 0.3, capped at 1.0. Text with no matches is "neutral".
    """
    words = re.findall(r"[a-z']+", text.lower())
    emotions = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        hits = sum(1 for word in words if word in keywords)
        emotions[emotion] = min(1.0, round(0.3 * hits, 2))
    return _result(emotions, text, "keywords")


class KeywordEmotionAnalyzer:
    """Offline analyzer. Useful for demos without a Hume key, and as a fallback."""

    name = "keywords"

    def analyze_emotion(self, text: str) -> EmotionResult:
        return keyword_emotions(text)


def parse_hume_message(message: dict) -> Dict[str, float]:
    """Average emotion scores across the predictions in one Hume response.

    The language model returns one prediction per word or sentence, each with
    a list of `{"name": ..., "score": ...}` emotions. Names are lower-cased.
    """
    if "error" in message:
        raise RuntimeError(f"Hume error: {message.get('error')}")
    predictions = message.get("language", {}).get("predictions", [])
    totals: Dict[str, float] = {}
    for prediction in predictions:
        for emotion in prediction.get("emotions", []):
            name = str(emotion.get("name", "")).lower()
            if name:
                totals[name] = totals.get(name, 0.0) + float(emotion.get("score", 0.0))
    if not predictions or not totals:
        raise RuntimeError("Hume returned no language predictions")
    return {name: total / len(predictions) for name, total in totals.items()}


def _default_connect(url: str, api_key: str, timeout: float):
    from websockets.sync.client import connect

    return connect(url, additional_headers={"X-Hume-Api-Key": api_key}, open_timeout=timeout)


class HumeEmotionAnalyzer:
    """Analyze text with Hume AI's streaming language model.

    Opens one WebSocket per message, sends the text and reads one response.
    Any failure (network, auth, unexpected payload) is logged and the keyword
    analyzer's result is returned instead, so a conversation never stalls.
    """

    name = "hume"

    def __init__(
        self,
        api_key: str,
        url: str = HUME_STREAM_URL,
        timeout: float = 10.0,
        connect: Optional[Callable] = None,
    ):
        if not api_key:
            raise ValueError("A Hume API key is required")
        self.api_key = api_key
        self.url = url
        self.timeout = timeout
        self._connect = connect or _default_connect

    def analyze_emotion(self, text: str) -> EmotionResult:
        try:
            return _result(self._request(text), text, "hume")
        except Exception as error:  # noqa: BLE001 - fall back on any failure
            logger.warning("Hume analysis failed, using keyword fallback: %s", error)
            return keyword_emotions(text)

    def _request(self, text: str) -> Dict[str, float]:
        payload = {"models": {"language": {}}, "raw_text": True, "data": text[:HUME_MAX_CHARS]}
        with self._connect(self.url, self.api_key, self.timeout) as socket:
            socket.send(json.dumps(payload))
            raw = socket.recv(timeout=self.timeout)
        return parse_hume_message(json.loads(raw))


class EmotionHistory:
    """The most recent emotion results, for trend calculation."""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[EmotionResult] = []

    def add_emotion(self, result: EmotionResult) -> None:
        self.history.append(result)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_emotion_trend(self, window: int = 5) -> Dict[str, float]:
        """Average score per emotion over the last `window` results."""
        recent = self.history[-window:]
        if not recent:
            return {}
        totals: Dict[str, float] = {}
        for result in recent:
            for emotion, score in result.emotions.items():
                totals[emotion] = totals.get(emotion, 0.0) + score
        return {emotion: total / len(recent) for emotion, total in totals.items()}

    def get_dominant_emotion_sequence(self) -> List[str]:
        return [result.dominant_emotion for result in self.history]

    def clear(self) -> None:
        self.history = []
