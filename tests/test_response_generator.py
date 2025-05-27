"""
Tests for the ResponseGenerator class.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import openai
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from response_generator import ResponseGenerator

# Sample API responses for testing
SAMPLE_OPENAI_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "I'm doing well, thank you for asking! How can I assist you today?"
            }
        }
    ]
}

@pytest.fixture
def mock_openai_response():
    """Mock the OpenAI API response."""
    with patch('openai.ChatCompletion.acreate') as mock_acreate:
        mock_acreate.return_value = SAMPLE_OPENAI_RESPONSE
        yield mock_acreate

@pytest.fixture
def response_generator():
    """Create a ResponseGenerator instance for testing."""
    return ResponseGenerator(api_key="test_api_key")

def test_build_system_prompt_no_emotion(response_generator):
    """Test building a system prompt with no emotion context."""
    prompt = response_generator._build_system_prompt()
    assert "emotionally intelligent" in prompt.lower()
    assert "emotion" in prompt.lower()

def test_build_system_prompt_with_emotion(response_generator):
    """Test building a system prompt with emotion context."""
    emotion_context = {"joy": 0.8, "sadness": 0.1, "anger": 0.05}
    prompt = response_generator._build_system_prompt(emotion_context)
    
    # Should include emotion information
    assert "joy (0.80)" in prompt
    assert "sadness (0.10)" in prompt
    assert "anger (0.05)" in prompt
    
    # Should include guidance for handling emotions
    assert "consider these emotions" in prompt.lower()

@pytest.mark.asyncio
async def test_generate_response_success(response_generator, mock_openai_response):
    """Test successful response generation."""
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    response = await response_generator.generate_response(
        messages=messages,
        emotion_context={"joy": 0.7},
        temperature=0.7,
        max_tokens=100
    )
    
    assert response == SAMPLE_OPENAI_RESPONSE["choices"][0]["message"]["content"]
    
    # Verify the API was called with the correct parameters
    mock_openai_response.assert_called_once()
    args, kwargs = mock_openai_response.call_args
    
    assert kwargs["model"] == response_generator.model
    assert kwargs["temperature"] == 0.7
    assert kwargs["max_tokens"] == 100
    
    # Check that the system prompt was included
    messages_passed = kwargs["messages"]
    assert messages_passed[0]["role"] == "system"
    assert "emotionally intelligent" in messages_passed[0]["content"]
    assert messages_passed[1] == messages[0]

@pytest.mark.asyncio
async def test_generate_response_api_error(response_generator):
    """Test handling of API errors during response generation."""
    with patch('openai.ChatCompletion.acreate') as mock_acreate:
        # Configure the mock to raise an exception
        mock_acreate.side_effect = Exception("API Error")
        
        # This should not raise an exception but return a fallback response
        response = await response_generator.generate_response(
            messages=[{"role": "user", "content": "Hello"}],
            emotion_context={"joy": 0.5}
        )
        
        assert isinstance(response, str)
        assert "trouble generating" in response.lower()

def test_format_messages_for_api(response_generator):
    """Test formatting conversation history for the OpenAI API."""
    conversation_history = [
        {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:00:01"},
        {"role": "system", "content": "You are helpful", "timestamp": "2023-01-01T00:00:00"},
        {"role": "user", "content": "How are you?", "timestamp": "2023-01-01T00:00:02"}
    ]
    
    formatted = response_generator.format_messages_for_api(conversation_history)
    
    # Should exclude system messages and only include role and content
    assert len(formatted) == 3  # 2 user + 1 assistant messages
    assert all(set(msg.keys()) == {'role', 'content'} for msg in formatted)
    assert formatted[0]["content"] == "Hello"
    assert formatted[1]["content"] == "Hi there!"
    assert formatted[2]["content"] == "How are you?"

def test_format_messages_limit_history(response_generator):
    """Test that message history can be limited."""
    # Create a long conversation history
    conversation_history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(20)  # 20 messages total
    ]
    
    # Limit to 5 messages
    formatted = response_generator.format_messages_for_api(
        conversation_history,
        max_history=5
    )
    
    # Should only include the most recent 5 messages
    assert len(formatted) == 5
    assert formatted[0]["content"] == "Message 15"
    assert formatted[-1]["content"] == "Message 19"

def test_response_generator_init_no_api_key():
    """Test that ResponseGenerator raises an error if no API key is provided."""
    # Save and clear the environment variable if it exists
    saved_key = os.environ.pop("OPENAI_API_KEY", None)
    
    try:
        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            ResponseGenerator(api_key=None)
    finally:
        # Restore the environment variable
        if saved_key is not None:
            os.environ["OPENAI_API_KEY"] = saved_key
