"""
Tests for the ConversationManager class.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import tempfile
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from conversation_manager import ConversationManager, Message

@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
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
        }
    ]

@pytest.fixture
def temp_conversation_dir():
    """Create a temporary directory for conversation files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

def test_conversation_manager_init():
    """Test initialization of ConversationManager."""
    conv = ConversationManager()
    assert conv.messages == []
    assert conv.emotion_history == []
    assert conv.conversation_id.startswith("conv_")
    assert len(conv.conversation_id) > len("conv_")

def test_conversation_manager_custom_id():
    """Test initialization with a custom conversation ID."""
    custom_id = "test_conversation_123"
    conv = ConversationManager(conversation_id=custom_id)
    assert conv.conversation_id == custom_id

def test_add_message(sample_messages):
    """Test adding messages to the conversation."""
    conv = ConversationManager()
    
    # Add a user message
    user_msg = sample_messages[0]
    conv.add_message(
        role=user_msg['role'],
        content=user_msg['content'],
        emotions=user_msg['emotions']
    )
    
    assert len(conv.messages) == 1
    assert conv.messages[0]['role'] == 'user'
    assert conv.messages[0]['content'] == user_msg['content']
    assert conv.emotion_history == [user_msg['emotions']]
    
    # Add an assistant message
    assistant_msg = sample_messages[1]
    conv.add_message(
        role=assistant_msg['role'],
        content=assistant_msg['content'],
        emotions=assistant_msg['emotions']
    )
    
    assert len(conv.messages) == 2
    assert conv.messages[1]['role'] == 'assistant'
    assert conv.emotion_history == [user_msg['emotions']]  # Shouldn't change

def test_add_message_invalid_role():
    """Test adding a message with an invalid role."""
    conv = ConversationManager()
    with pytest.raises(ValueError, match="Role must be either 'user' or 'assistant'"):
        conv.add_message(role='invalid', content='test')

def test_get_conversation_history(sample_messages):
    """Test retrieving conversation history."""
    conv = ConversationManager()
    
    # Add sample messages
    for msg in sample_messages:
        conv.add_message(
            role=msg['role'],
            content=msg['content'],
            emotions=msg['emotions']
        )
    
    # Test getting full history
    history = conv.get_conversation_history()
    assert len(history) == 2
    assert history[0]['content'] == sample_messages[0]['content']
    assert history[1]['content'] == sample_messages[1]['content']
    
    # Test limiting history length
    limited = conv.get_conversation_history(max_messages=1)
    assert len(limited) == 1
    assert limited[0]['content'] == sample_messages[1]['content']  # Should return most recent

def test_save_and_load_conversation(temp_conversation_dir, sample_messages):
    """Test saving and loading a conversation to/from a file."""
    # Create and populate a conversation
    conv = ConversationManager(history_dir=temp_conversation_dir)
    for msg in sample_messages:
        conv.add_message(
            role=msg['role'],
            content=msg['content'],
            emotions=msg['emotions']
        )
    
    # Save the conversation
    saved_path = conv.save_conversation()
    assert os.path.exists(saved_path)
    
    # Load the conversation
    loaded_conv = ConversationManager.load_conversation(saved_path)
    
    # Verify the loaded conversation matches the original
    assert loaded_conv.conversation_id == conv.conversation_id
    assert len(loaded_conv.messages) == len(conv.messages)
    assert loaded_conv.messages[0]['content'] == sample_messages[0]['content']
    assert loaded_conv.messages[1]['content'] == sample_messages[1]['content']
    assert loaded_conv.emotion_history == [sample_messages[0]['emotions']]

def test_clear_conversation(sample_messages):
    """Test clearing the conversation."""
    conv = ConversationManager()
    
    # Add some messages
    for msg in sample_messages:
        conv.add_message(
            role=msg['role'],
            content=msg['content'],
            emotions=msg['emotions']
        )
    
    # Clear the conversation
    old_id = conv.conversation_id
    conv.clear()
    
    # Verify everything is reset
    assert conv.messages == []
    assert conv.emotion_history == []
    assert conv.conversation_id != old_id
    assert conv.conversation_id.startswith("conv_")

def test_save_conversation_no_messages(temp_conversation_dir):
    """Test saving an empty conversation raises an error."""
    conv = ConversationManager(history_dir=temp_conversation_dir)
    with pytest.raises(ValueError, match="No messages to save"):
        conv.save_conversation()

def test_load_nonexistent_file():
    """Test loading a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        ConversationManager.load_conversation("nonexistent_file.json")
