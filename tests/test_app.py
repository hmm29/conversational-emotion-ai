"""Runs the Streamlit app headlessly, offline, and sends it a message."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

from src.response_generator import FALLBACK_REPLIES  # noqa: E402

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture()
def app(monkeypatch):
    # Empty keys put the app in offline mode: keyword matcher and canned replies.
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("HUME_API_KEY", "")
    return AppTest.from_file(APP_PATH, default_timeout=30)


def test_app_starts_without_keys(app):
    app.run()
    assert not app.exception
    assert app.title[0].value == "Conversational Emotion AI"
    assert len(app.chat_message) == 0


def test_app_handles_a_message(app):
    app.run()
    app.chat_input[0].set_value("I am so happy today").run()
    assert not app.exception
    assert len(app.chat_message) == 2
    manager = app.session_state["manager"]
    assert manager.turns[0].emotion_result.dominant_emotion == "joy"
    assert manager.turns[0].bot_response == FALLBACK_REPLIES["amplify_positive"]


def test_start_over_clears_the_conversation(app):
    app.run()
    app.chat_input[0].set_value("I feel sad").run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.chat_message) == 0
