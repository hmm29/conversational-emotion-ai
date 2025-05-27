"""
Response Generator Module

This module handles generating contextually appropriate and emotionally aware responses
using OpenAI's API.
"""
import os
from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv

load_dotenv()

class ResponseGenerator:
    """Generates responses using OpenAI's API with emotional context awareness."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize the ResponseGenerator with API credentials.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to load from environment.
            model: The OpenAI model to use for response generation.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in environment variables")
            
        openai.api_key = self.api_key
    
    def _build_system_prompt(self, emotion_context: Optional[Dict[str, float]] = None) -> str:
        """Build the system prompt with emotional context.
        
        Args:
            emotion_context: Dictionary of emotion scores for the user's message.
            
        Returns:
            A formatted system prompt string.
        """
        base_prompt = """You are an emotionally intelligent AI assistant. Your goal is to have natural, 
        empathetic conversations while being helpful and informative. Pay attention to the emotional 
        context of the conversation and respond appropriately."""
        
        if not emotion_context:
            return base_prompt
            
        # Sort emotions by score in descending order
        sorted_emotions = sorted(
            emotion_context.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
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
