"""Exercises the real WebSocket client code against a local server that
answers in Hume's documented response shape. No Hume account is involved."""
import json
import threading

import pytest

pytest.importorskip("websockets")

from websockets.sync.server import serve  # noqa: E402

from src.emotion_analyzer import HumeEmotionAnalyzer  # noqa: E402
from tests.fakes import hume_message  # noqa: E402


def test_real_websocket_round_trip():
    seen = {}

    def handler(websocket):
        seen["api_key"] = websocket.request.headers.get("X-Hume-Api-Key")
        seen["payload"] = json.loads(websocket.recv())
        websocket.send(hume_message({"Joy": 0.9, "Calmness": 0.3}))

    with serve(handler, "127.0.0.1", 0) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.socket.getsockname()[1]
        try:
            analyzer = HumeEmotionAnalyzer("secret-key", url=f"ws://127.0.0.1:{port}", timeout=5)
            result = analyzer.analyze_emotion("What a lovely day")
        finally:
            server.shutdown()
            thread.join(timeout=5)

    assert result.source == "hume"
    assert result.dominant_emotion == "joy"
    assert seen["api_key"] == "secret-key"
    assert seen["payload"] == {"models": {"language": {}}, "raw_text": True, "data": "What a lovely day"}
