"""
Conversation Manager Module

This module handles conversation state, history, and context management.
"""
from typing import Dict, List, Optional, TypedDict, Any
from datetime import datetime
import json
import os
from pathlib import Path


class Message(TypedDict):
    """Represents a single message in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    emotions: Optional[Dict[str, float]]


class ConversationManager:
    """Manages conversation state and history."""
    
    def __init__(self, conversation_id: Optional[str] = None, history_dir: str = 'data/conversation_history'):
        """Initialize the conversation manager.
        
        Args:
            conversation_id: Optional ID for the conversation. If not provided, a timestamp-based ID will be generated.
            history_dir: Directory to store conversation history files.
        """
        self.messages: List[Message] = []
        self.conversation_id = conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.emotion_history: List[Dict[str, float]] = []
    
    def add_message(self, role: str, content: str, emotions: Optional[Dict[str, float]] = None) -> None:
        """Add a message to the conversation.
        
        Args:
            role: The role of the message sender ('user' or 'assistant').
            content: The text content of the message.
            emotions: Optional dictionary of emotion scores for the message.
        """
        if role not in ['user', 'assistant']:
            raise ValueError("Role must be either 'user' or 'assistant'")
            
        message: Message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'emotions': emotions
        }
        
        self.messages.append(message)
        
        if role == 'user' and emotions:
            self.emotion_history.append(emotions)
    
    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Message]:
        """Get the conversation history.
        
        Args:
            max_messages: Maximum number of messages to return. If None, returns all messages.
            
        Returns:
            List of message dictionaries.
        """
        if max_messages is None:
            return self.messages
        return self.messages[-max_messages:]
    
    def get_emotion_history(self) -> List[Dict[str, float]]:
        """Get the emotion history for the conversation.
        
        Returns:
            List of emotion dictionaries for user messages.
        """
        return self.emotion_history
    
    def save_conversation(self) -> str:
        """Save the conversation to a JSON file.
        
        Returns:
            Path to the saved conversation file.
        """
        if not self.messages:
            raise ValueError("No messages to save")
            
        filename = self.history_dir / f"{self.conversation_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'conversation_id': self.conversation_id,
                'created_at': self.messages[0]['timestamp'],
                'messages': self.messages
            }, f, indent=2)
            
        return str(filename)
    
    @classmethod
    def load_conversation(cls, filepath: str) -> 'ConversationManager':
        """Load a conversation from a JSON file.
        
        Args:
            filepath: Path to the conversation JSON file.
            
        Returns:
            A new ConversationManager instance with the loaded conversation.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        manager = cls(conversation_id=data['conversation_id'])
        manager.messages = data['messages']
        
        # Rebuild emotion history
        manager.emotion_history = [
            msg['emotions'] for msg in manager.messages 
            if msg['role'] == 'user' and msg['emotions']
        ]
        
        return manager
    
    def clear(self) -> None:
        """Clear the current conversation."""
        self.messages = []
        self.emotion_history = []
        self.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
