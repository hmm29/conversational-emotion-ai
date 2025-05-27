"""
Shared test fixtures for the Conversational Emotion AI tests.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture to provide a test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_dir():
    """Create a temporary directory that's automatically cleaned up."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_emotion_analysis():
    """Sample emotion analysis result from Hume AI."""
    return {
        "emotion": {
            "predictions": [
                {
                    "emotions": {
                        "joy": 0.85,
                        "sadness": 0.1,
                        "anger": 0.02,
                        "fear": 0.01,
                        "surprise": 0.02,
                        "disgust": 0.0
                    },
                    "text": "I'm so happy today!"
                }
            ]
        }
    }

@pytest.fixture
def sample_conversation():
    """Sample conversation with messages."""
    return [
        {
            'role': 'user',
            'content': 'Hello, how are you?',
            'timestamp': '2023-10-27T10:00:00',
            'emotions': {'joy': 0.7, 'sadness': 0.1}
        },
        {
            'role': 'assistant',
            'content': 'I\'m doing well, thank you for asking!',
            'timestamp': '2023-10-27T10:00:01',
            'emotions': None
        },
        {
            'role': 'user',
            'content': 'I\'m feeling a bit anxious today.',
            'timestamp': '2023-10-27T10:01:00',
            'emotions': {'fear': 0.6, 'sadness': 0.4}
        }
    ]

@pytest.fixture
def mock_openai_response():
    """Mock response from OpenAI API."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I'm here to help! How can I assist you today?"
                }
            }
        ]
    }

@pytest.fixture
def mock_httpx_client():
    """Mock HTTPX client for API calls."""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json = json_data or {}
            
        def raise_for_status(self):
            if 400 <= self.status_code < 600:
                raise Exception(f"HTTP Error {self.status_code}")
                
        async def json(self):
            return self._json
    
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            self.response = MockResponse()
            
        async def post(self, *args, **kwargs):
            return self.response
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    return MockAsyncClient()
