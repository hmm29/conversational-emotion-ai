"""
Advanced Emotion Analyzer Module

This module provides comprehensive emotion analysis functionality using Hume AI's API.
Includes fallback mechanisms and emotion history tracking.
"""
import os
import asyncio
import httpx
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmotionResult:
    """Data class for emotion analysis results"""
    emotions: Dict[str, float]
    dominant_emotion: str
    confidence: float
    timestamp: datetime
    text: str

class HumeEmotionAnalyzer:
    """
    Advanced emotion analyzer using Hume AI's emotion detection API
    Implements real-time emotion analysis for conversational AI
    """
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.hume.ai/v0"
        self.session: Optional[httpx.AsyncClient] = None
        
        # Emotion categories we track
        self.primary_emotions = [
            'joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust',
            'contempt', 'excitement', 'amusement', 'contentment',
            'disappointment', 'doubt', 'enthusiasm', 'interest',
            'satisfaction', 'shame', 'sympathy', 'tiredness'
        ]
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def analyze_emotion(self, text: str) -> EmotionResult:
        """
        Analyze emotion in text using Hume AI's advanced models
        
        Args:
            text: Input text to analyze
            
        Returns:
            EmotionResult with detected emotions and metadata
        """
        try:
            if not self.session:
                raise RuntimeError("Session not initialized. Use async context manager.")
                
            # Prepare the request
            headers = {
                "X-Hume-Api-Key": self.api_key,
                "X-Hume-Secret-Key": self.secret_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "models": {
                    "language": {
                        "granularity": "sentence"
                    }
                },
                "text": [text]
            }
            
            # Make API request
            response = await self.session.post(
                f"{self.base_url}/batch/jobs",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Hume API error: {response.status_code} - {response.text}")
                return self._fallback_emotion_analysis(text)
            
            # Parse response
            result = response.json()
            
            # Extract emotions from response
            emotions = self._extract_emotions(result)
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
            confidence = emotions[dominant_emotion]
            
            return EmotionResult(
                emotions=emotions,
                dominant_emotion=dominant_emotion,
                confidence=confidence,
                timestamp=datetime.now(),
                text=text
            )
            
        except Exception as e:
            logger.error(f"Error analyzing emotion: {str(e)}")
            return self._fallback_emotion_analysis(text)
    
    def _extract_emotions(self, api_response: Dict[str, Any]) -> Dict[str, float]:
        """Extract and normalize emotion scores from Hume API response"""
        try:
            # Navigate the Hume API response structure
            predictions = api_response.get("results", {}).get("predictions", [])
            if not predictions:
                return self._default_emotions()
            
            # Get language model predictions
            language_predictions = predictions[0].get("models", {}).get("language", {})
            grouped_predictions = language_predictions.get("grouped_predictions", [])
            
            if not grouped_predictions:
                return self._default_emotions()
            
            # Extract emotion scores
            emotions = {}
            emotion_predictions = grouped_predictions[0].get("predictions", [])
            
            for prediction in emotion_predictions:
                emotion_name = prediction.get("name", "").lower()
                emotion_score = prediction.get("score", 0.0)
                
                if emotion_name in self.primary_emotions:
                    emotions[emotion_name] = emotion_score
            
            # Ensure we have all primary emotions
            for emotion in self.primary_emotions:
                if emotion not in emotions:
                    emotions[emotion] = 0.0
                    
            return emotions
            
        except Exception as e:
            logger.error(f"Error extracting emotions: {str(e)}")
            return self._default_emotions()
    
    def _default_emotions(self) -> Dict[str, float]:
        """Return default emotion scores when API fails"""
        return {emotion: 0.0 for emotion in self.primary_emotions}
    
    def _fallback_emotion_analysis(self, text: str) -> EmotionResult:
        """
        Fallback emotion analysis using simple keyword detection
        Used when Hume API is unavailable
        """
        text_lower = text.lower()
        
        # Simple emotion keywords
        emotion_keywords = {
            'joy': ['happy', 'joy', 'excited', 'great', 'awesome', 'wonderful', 'amazing'],
            'sadness': ['sad', 'depressed', 'down', 'unhappy', 'disappointed', 'upset'],
            'anger': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', 'irritated'],
            'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified'],
            'surprise': ['surprised', 'shocked', 'unexpected', 'sudden', 'wow'],
            'amusement': ['funny', 'hilarious', 'laugh', 'haha', 'lol', 'amusing']
        }
        
        emotions = {emotion: 0.0 for emotion in self.primary_emotions}
        
        # Score based on keyword presence
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotions[emotion] += 0.3
        
        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
        if emotions[dominant_emotion] == 0.0:
            dominant_emotion = 'contentment'  # Default neutral emotion
            emotions[dominant_emotion] = 0.5
        
        return EmotionResult(
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            confidence=emotions[dominant_emotion],
            timestamp=datetime.now(),
            text=text
        )

class EmotionHistory:
    """Track emotion history over conversation"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[EmotionResult] = []
    
    def add_emotion(self, emotion_result: EmotionResult):
        """Add emotion result to history"""
        self.history.append(emotion_result)
        
        # Maintain max history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_emotion_trend(self) -> Dict[str, float]:
        """Calculate emotional trend over conversation"""
        if not self.history:
            return {}
        
        # Average emotions over recent history
        emotion_sums = {}
        for result in self.history[-5:]:  # Last 5 messages
            for emotion, score in result.emotions.items():
                emotion_sums[emotion] = emotion_sums.get(emotion, 0) + score
        
        # Calculate averages
        num_results = len(self.history[-5:])
        return {emotion: score / num_results for emotion, score in emotion_sums.items()}
    
    def get_dominant_emotion_sequence(self) -> List[str]:
        """Get sequence of dominant emotions"""
        return [result.dominant_emotion for result in self.history]

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def example():
        analyzer = HumeEmotionAnalyzer(
            api_key="your-api-key",
            secret_key="your-secret-key"
        )
        
        async with analyzer:
            result = await analyzer.analyze_emotion("I'm feeling really happy today!")
            print(result)
    
    asyncio.run(example())
