"""
Conversation Manager Module

This module handles generating contextually appropriate and emotionally aware responses
using OpenAI's API with psychology-informed prompting.
"""
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from pathlib import Path

from .emotion_analyzer import EmotionResult, EmotionHistory
from .response_generator import ConversationContext, EmotionAwareResponseGenerator

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Single turn in conversation with metadata"""
    user_message: str
    bot_response: str
    emotion_result: EmotionResult
    timestamp: datetime
    response_strategy: str
    context_used: Dict[str, Any]

class PersonalityProfile:
    """Track user personality traits over conversation"""
    
    def __init__(self):
        self.traits = {
            'openness': 0.5,           # Openness to experience
            'emotional_expressivity': 0.5,  # How emotionally expressive
            'humor_appreciation': 0.5,      # Response to humor
            'support_seeking': 0.5,         # Tendency to seek support
            'conversation_depth': 0.5       # Preference for deep vs shallow topics
        }
        self.confidence = {trait: 0.1 for trait in self.traits}
        self.update_count = 0
    
    def update_from_emotion(self, emotion_result: EmotionResult, response_engagement: float):
        """Update personality profile based on emotional expression and engagement"""
        self.update_count += 1
        learning_rate = min(0.1, 1.0 / self.update_count)  # Decreasing learning rate
        
        # Update emotional expressivity based on emotion confidence
        if emotion_result.confidence > 0.6:
            self.traits['emotional_expressivity'] += learning_rate * 0.2
        
        # Update humor appreciation based on amusement
        if emotion_result.emotions.get('amusement', 0) > 0.3:
            self.traits['humor_appreciation'] += learning_rate * 0.3
        
        # Update support seeking based on negative emotions
        negative_emotions = ['sadness', 'fear', 'anger', 'disappointment', 'shame']
        negative_score = sum(emotion_result.emotions.get(e, 0) for e in negative_emotions)
        if negative_score > 0.4:
            self.traits['support_seeking'] += learning_rate * 0.2
        
        # Update conversation depth based on engagement with complex topics
        if response_engagement > 0.7:
            self.traits['conversation_depth'] += learning_rate * 0.1
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
