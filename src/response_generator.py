"""
Response Generator Module

This module handles generating contextually appropriate and emotionally aware responses
using OpenAI's API with psychology-informed prompting.
"""
import openai
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
import yaml

from .emotion_analyzer import EmotionResult, EmotionHistory

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Context for maintaining conversation state"""
    user_message: str
    emotion_result: EmotionResult
    conversation_history: List[Dict[str, Any]]
    emotion_trend: Dict[str, float]
    user_personality_profile: Dict[str, Any]
    
class EmotionAwareResponseGenerator:
    """
    Advanced response generator that creates emotionally-intelligent responses
    using OpenAI's GPT models with psychology-informed prompting
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        
        # Load response strategies from config
        self.load_response_strategies()
        
        # Initialize personality tracking
        self.user_profiles = {}
        
    def load_response_strategies(self):
        """Load emotion-based response strategies from config"""
        try:
            with open('config/emotions_config.yaml', 'r') as file:
                config = yaml.safe_load(file)
                self.response_strategies = config.get('response_strategies', {})
                self.conversation_config = config.get('conversation', {})
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.response_strategies = self._default_strategies()
            self.conversation_config = {}
    
    def _default_strategies(self):
        """Default response strategies if config fails to load"""
        return {
            'high_positive': {
                'threshold': 0.7,
                'emotions': ['joy', 'excitement', 'amusement', 'enthusiasm'],
                'approach': 'amplify_positive'
            },
            'moderate_positive': {
                'threshold': 0.4,
                'emotions': ['contentment', 'interest', 'satisfaction'],
                'approach': 'gentle_encouragement'
            },
            'negative': {
                'threshold': 0.3,
                'emotions': ['sadness', 'anger', 'fear', 'disappointment', 'shame'],
                'approach': 'empathetic_support'
            },
            'neutral': {
                'threshold': 0.2,
                'emotions': ['doubt', 'tiredness'],
                'approach': 'balanced_engagement'
            }
        }
    
    async def generate_response(self, context: ConversationContext) -> str:
        """
        Generate emotionally-aware response based on conversation context
        
        Args:
            context: Complete conversation context including emotions
            
        Returns:
            Generated response string
        """
        try:
            # Determine response strategy
            strategy = self._determine_response_strategy(context.emotion_result)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(strategy, context)
            
            # Build conversation history for context
            messages = self._build_message_history(context, system_prompt)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self._get_temperature_for_strategy(strategy),
                max_tokens=200,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(context.emotion_result)
    
    def _determine_response_strategy(self, emotion_result: EmotionResult) -> str:
        """Determine appropriate response strategy based on emotions"""
        dominant_emotion = emotion_result.dominant_emotion
        confidence = emotion_result.confidence
        
        # Check each strategy category
        for strategy_name, strategy_config in self.response_strategies.items():
            if (dominant_emotion in strategy_config.get('emotions', []) and 
                confidence >= strategy_config.get('threshold', 0.3)):
                return strategy_name
        
        return 'balanced_engagement'  # Default strategy
    
    def _build_system_prompt(self, strategy: str, context: ConversationContext) -> str:
        """Build psychology-informed system prompt based on strategy"""
        base_prompt = """You are an emotionally intelligent AI assistant designed to have natural, 
        empathetic conversations. You have been trained to understand and respond appropriately to 
        human emotions based on psychological research in human-computer interaction."""
        
        strategy_prompts = {
            'amplify_positive': """
            The user is experiencing positive emotions (joy, excitement, amusement). Your approach should:
            - Mirror their positive energy appropriately
            - Encourage and validate their feelings
            - Ask follow-up questions to maintain engagement
            - Use enthusiastic but not overwhelming language
            - Share in their positivity without being fake
            """,
            
            'gentle_encouragement': """
            The user is in a mildly positive or content state. Your approach should:
            - Provide gentle encouragement and support
            - Maintain a warm, friendly tone
            - Show genuine interest in their thoughts
            - Help build on their positive momentum
            - Be supportive without being overly enthusiastic
            """,
            
            'empathetic_support': """
            The user is experiencing negative emotions (sadness, anger, fear). Your approach should:
            - Show genuine empathy and understanding
            - Validate their feelings without trying to "fix" everything immediately
            - Use supportive, calming language
            - Offer to listen and understand more
            - Avoid being dismissive or overly cheerful
            - Focus on being present and supportive
            """,
            
            'balanced_engagement': """
            The user's emotional state is neutral or unclear. Your approach should:
            - Maintain a balanced, friendly tone
            - Show interest in understanding them better
            - Ask thoughtful questions to engage them
            - Be responsive to emotional cues in their responses
            - Stay flexible and adaptive to their needs
            """
        }
        
        emotion_context = f"""
        Current emotion analysis:
        - Dominant emotion: {context.emotion_result.dominant_emotion}
        - Confidence: {context.emotion_result.confidence:.2f}
        - Recent emotional trend: {self._format_emotion_trend(context.emotion_trend)}
        """
        
        return f"{base_prompt}\n\n{strategy_prompts.get(strategy, strategy_prompts['balanced_engagement'])}\n\n{emotion_context}"
    
    def _build_message_history(self, context: ConversationContext, system_prompt: str) -> List[Dict[str, str]]:
        """Build message history for OpenAI API"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 6 exchanges to maintain context)
        recent_history = context.conversation_history[-6:] if context.conversation_history else []
        
        for exchange in recent_history:
            messages.append({"role": "user", "content": exchange.get('user', '')})
            messages.append({"role": "assistant", "content": exchange.get('bot', '')})
        
        # Add current user message
        messages.append({"role": "user", "content": context.user_message})
        
        return messages
    
    def _get_temperature_for_strategy(self, strategy: str) -> float:
        """Get appropriate temperature setting for response strategy"""
        temperature_map = {
            'amplify_positive': 0.8,      # More creative and enthusiastic
            'gentle_encouragement': 0.6,  # Moderately warm and supportive
            'empathetic_support': 0.4,    # More measured and careful
            'balanced_engagement': 0.7    # Balanced creativity
        }
        return temperature_map.get(strategy, 0.7)
    
    def _format_emotion_trend(self, emotion_trend: Dict[str, float]) -> str:
        """Format emotion trend for prompt context"""
        if not emotion_trend:
            return "No previous emotional context"
        
        top_emotions = sorted(emotion_trend.items(), key=lambda x: x[1], reverse=True)[:3]
        return ", ".join([f"{emotion}: {score:.2f}" for emotion, score in top_emotions])
    
    def _fallback_response(self, emotion_result: EmotionResult) -> str:
        """Fallback response when OpenAI API fails"""
        emotion = emotion_result.dominant_emotion
        
        fallback_responses = {
            'joy': "I can sense your positive energy! That's wonderful to hear.",
            'sadness': "I understand you might be feeling down. I'm here to listen.",
            'anger': "I can tell you might be frustrated. Let's talk through this.",
            'fear': "It sounds like you might be worried. That's completely understandable.",
            'surprise': "That sounds unexpected! I'd love to hear more about it.",
            'amusement': "I love that you're finding humor in things!",
            'excitement': "Your enthusiasm comes through clearly!",
            'contentment': "You seem to be in a peaceful place right now."
        }
        
        return fallback_responses.get(emotion, "I'm here to chat with you and understand how you're feeling.")
        
        # Get top 3 emotions
        top_emotions = [f"{e[0]} ({e[1]:.2f})" for e in sorted_emotions[:3]]
        
        emotion_context_prompt = f"""
        The user's message suggests the following emotional context (top 3 emotions):
        {', '.join(top_emotions)}
        
        Please respond in a way that is appropriate for these emotions. If the emotions are 
        negative, be supportive and understanding. If positive, be engaging and enthusiastic.
        """
        
        return base_prompt + "\n\n" + emotion_context_prompt
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        emotion_context: Optional[Dict[str, float]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response using OpenAI's API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            emotion_context: Optional dictionary of emotion scores for the user's message.
            temperature: Controls randomness in the response generation (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            The generated response text.
            
        Raises:
            Exception: If the API request fails.
        """
        try:
            system_prompt = {
                "role": "system",
                "content": self._build_system_prompt(emotion_context)
            }
            
            # Add the system prompt to the beginning of the messages
            messages_with_system = [system_prompt] + messages
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages_with_system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message['content'].strip()
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            # Fallback response if API call fails
            return "I'm having trouble generating a response right now. Could you try rephrasing your question?"
    
    def format_messages_for_api(
        self, 
        conversation_history: List[Dict[str, Any]], 
        max_history: int = 10
    ) -> List[Dict[str, str]]:
        """Format conversation history for the OpenAI API.
        
        Args:
            conversation_history: List of message dictionaries from ConversationManager.
            max_history: Maximum number of historical messages to include.
            
        Returns:
            List of formatted message dictionaries for the OpenAI API.
        """
        # Only include the most recent messages to stay within token limits
        recent_messages = conversation_history[-max_history:]
        
        formatted_messages = []
        for msg in recent_messages:
            # Skip system messages as we'll add our own
            if msg.get('role') == 'system':
                continue
                
            formatted_msg = {
                'role': msg['role'],
                'content': msg['content']
            }
            formatted_messages.append(formatted_msg)
            
        return formatted_messages
