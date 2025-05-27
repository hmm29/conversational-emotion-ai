"""
Tests for the EmotionAnalyzer class.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from emotion_analyzer import EmotionAnalyzer

# Sample API response for testing
SAMPLE_EMOTION_RESPONSE = {
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
def mock_emotion_analyzer():
    """Fixture to create a properly mocked EmotionAnalyzer instance."""
    with patch('emotion_analyzer.httpx.AsyncClient') as mock_client:
        # Configure the mock client
        mock_response = AsyncMock()
        mock_response.json.return_value = SAMPLE_EMOTION_RESPONSE
        mock_response.raise_for_status.return_value = None
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Create the analyzer with a test API key
        analyzer = EmotionAnalyzer(api_key="test_api_key")
        yield analyzer

@pytest.mark.asyncio
async def test_analyze_emotion_success(mock_emotion_analyzer):
    """Test successful emotion analysis."""
    text = "I'm feeling great today!"
    result = await mock_emotion_analyzer.analyze_emotion(text)
    
    assert result == SAMPLE_EMOTION_RESPONSE
    
    # Verify the API was called with the correct parameters
    mock_emotion_analyzer._client.post.assert_called_once()
    args, kwargs = mock_emotion_analyzer._client.post.call_args
    
    assert kwargs['json']['text'] == text
    assert kwargs['json']['models'] == ["emotion"]

@pytest.mark.asyncio
async def test_analyze_emotion_empty_text(mock_emotion_analyzer):
    """Test that empty text raises a ValueError."""
    with pytest.raises(ValueError):
        await mock_emotion_analyzer.analyze_emotion("")

@pytest.mark.asyncio
async def test_analyze_emotion_api_error():
    """Test handling of API errors."""
    with patch('emotion_analyzer.httpx.AsyncClient') as mock_client:
        # Configure the mock to raise an exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = \
            Exception("API Error")
            
        analyzer = EmotionAnalyzer(api_key="test_api_key")
        
        with pytest.raises(Exception, match="API Error"):
            await analyzer.analyze_emotion("test")

def test_extract_primary_emotion():
    """Test extraction of primary emotions from analysis results."""
    analyzer = EmotionAnalyzer(api_key="test_api_key")
    emotions = analyzer.extract_primary_emotion(SAMPLE_EMOTION_RESPONSE)
    
    assert isinstance(emotions, dict)
    assert "joy" in emotions
    assert emotions["joy"] == 0.85
    assert len(emotions) == 6  # All 6 emotions should be present

def test_extract_primary_emotion_invalid_input():
    """Test extraction with invalid input data."""
    analyzer = EmotionAnalyzer(api_key="test_api_key")
    
    # Test with None
    assert analyzer.extract_primary_emotion(None) == {}
    
    # Test with empty dict
    assert analyzer.extract_primary_emotion({}) == {}
    
    # Test with missing keys
    assert analyzer.extract_primary_emotion({"invalid": "data"}) == {}

def test_emotion_analyzer_init_no_api_key():
    """Test that EmotionAnalyzer raises an error if no API key is provided."""
    # Save and clear the environment variable if it exists
    saved_key = os.environ.pop("HUME_API_KEY", None)
    
    try:
        with pytest.raises(ValueError, match="Hume API key not provided"):
            EmotionAnalyzer(api_key=None)
    finally:
        # Restore the environment variable
        if saved_key is not None:
            os.environ["HUME_API_KEY"] = saved_key
