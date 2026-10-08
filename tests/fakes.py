"""In-memory stand-ins for Hume AI and OpenAI, so tests need no network or keys."""
import json
from types import SimpleNamespace


def raises(exception_type, function, *args, **kwargs) -> bool:
    try:
        function(*args, **kwargs)
    except exception_type:
        return True
    return False


def hume_message(*word_scores) -> str:
    """Build a Hume-shaped response: one prediction per dict of emotion scores."""
    predictions = [
        {
            "text": f"word{index}",
            "position": {"begin": index, "end": index + 1},
            "emotions": [{"name": name, "score": score} for name, score in scores.items()],
        }
        for index, scores in enumerate(word_scores)
    ]
    return json.dumps({"language": {"predictions": predictions}})


class FakeSocket:
    def __init__(self, reply=None, error=None):
        self.reply = reply
        self.error = error
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def send(self, data):
        self.sent.append(json.loads(data))

    def recv(self, timeout=None):
        if self.error:
            raise self.error
        return self.reply


class FakeConnect:
    """Callable with the same signature as the analyzer's connect function."""

    def __init__(self, socket=None, error=None):
        self.socket = socket
        self.error = error
        self.calls = []

    def __call__(self, url, api_key, timeout):
        self.calls.append((url, api_key, timeout))
        if self.error:
            raise self.error
        return self.socket


class FakeOpenAI:
    """Mimics `client.chat.completions.create` from the OpenAI SDK."""

    def __init__(self, reply="A thoughtful reply.", error=None):
        self.reply = reply
        self.error = error
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])
