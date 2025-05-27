"""
Tests for the main Streamlit application.
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Import the app module
import app

# Mock the Streamlit functions
class MockSessionState:
    def __init__(self):
        self.conversation = MagicMock()
        self.conversation.messages = []
        self.conversation.emotion_history = []
        self.conversation.conversation_id = "test_conv_123"
        self.emotion_analyzer = MagicMock()
        self.response_generator = MagicMock()

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch('streamlit.set_page_config'), \
         patch('streamlit.markdown'), \
         patch('streamlit.sidebar'), \
         patch('streamlit.container'), \
         patch('streamlit.form'), \
         patch('streamlit.text_area'), \
         patch('streamlit.form_submit_button'), \
         patch('streamlit.spinner'), \
         patch('streamlit.error'), \
         patch('streamlit.success'), \
         patch('streamlit.plotly_chart'):
        yield

@pytest.fixture
def mock_app_components():
    """Mock the app components."""
    with patch('app.ConversationManager') as mock_conv, \
         patch('app.EmotionAnalyzer') as mock_analyzer, \
         patch('app.ResponseGenerator') as mock_generator:
        
        # Configure mocks
        mock_conv.return_value = MagicMock()
        mock_analyzer.return_value = MagicMock()
        mock_generator.return_value = MagicMock()
        
        yield mock_conv, mock_analyzer, mock_generator

def test_app_initialization(mock_streamlit, mock_app_components):
    """Test that the app initializes correctly."""
    # Import here to apply the mocks
    import app
    
    # Check that the page config was set
    app.st.set_page_config.assert_called_once()
    
    # Check that the ConversationManager was initialized
    app.ConversationManager.assert_called_once()
    
    # Check that EmotionAnalyzer was initialized
    app.EmotionAnalyzer.assert_called_once()
    
    # Check that ResponseGenerator was initialized
    app.ResponseGenerator.assert_called_once()

@patch('app.st.session_state', new_callable=MockSessionState)
def test_chat_submission(mock_session_state, mock_streamlit):
    """Test submitting a chat message."""
    # Import here to apply the mocks
    import app
    
    # Mock the form submission
    app.st.form_submit_button.return_value = True
    app.st.text_area.return_value = "Hello, how are you?"
    
    # Mock the emotion analysis response
    mock_emotions = {"joy": 0.8, "sadness": 0.1}
    app.st.session_state.emotion_analyzer.analyze_emotion.return_value = {"emotion": {"predictions": [{"emotions": mock_emotions}]}}
    app.st.session_state.emotion_analyzer.extract_primary_emotion.return_value = mock_emotions
    
    # Mock the response generation
    app.st.session_state.response_generator.generate_response.return_value = "I'm doing well, thank you!"
    
    # Run the app
    app.main()
    
    # Check that the message was added to the conversation
    app.st.session_state.conversation.add_message.assert_called()
    
    # Check that the emotion was analyzed
    app.st.session_state.emotion_analyzer.analyze_emotion.assert_called_once_with("Hello, how are you?")
    
    # Check that a response was generated
    app.st.session_state.response_generator.generate_response.assert_called_once()

@patch('app.st.session_state', new_callable=MockSessionState)
def test_new_conversation(mock_session_state, mock_streamlit):
    """Test starting a new conversation."""
    # Import here to apply the mocks
    import app
    
    # Mock the new conversation button click
    app.st.sidebar.button.return_value = True
    
    # Run the app
    app.main()
    
    # Check that a new conversation was started
    app.ConversationManager.assert_called_once()
    
    # Check that the session state was updated
    assert app.st.session_state.conversation is not None

@patch('app.st.session_state', new_callable=MockSessionState)
def test_error_handling(mock_session_state, mock_streamlit):
    """Test error handling in the app."""
    # Import here to apply the mocks
    import app
    
    # Mock the form submission
    app.st.form_submit_button.return_value = True
    app.st.text_area.return_value = "Test error"
    
    # Make the emotion analyzer raise an exception
    app.st.session_state.emotion_analyzer.analyze_emotion.side_effect = Exception("Test error")
    
    # Run the app
    app.main()
    
    # Check that the error was displayed
    app.st.error.assert_called()
    
    # Check that the error message contains the exception text
    error_message = app.st.error.call_args[0][0]
    assert "Test error" in error_message
