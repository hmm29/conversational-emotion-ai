"""
Emotion Analyzer Module

This module provides functionality to analyze emotional tone in text using the Hume AI API.
"""
import os
from typing import Dict, List, Optional, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

class EmotionAnalyzer:
    """Handles emotion analysis of text using Hume AI's API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the EmotionAnalyzer with API credentials.
        
        Args:
            api_key: Hume AI API key. If not provided, will try to load from environment.
        """
        self.api_key = api_key or os.getenv("HUME_API_KEY")
        self.base_url = "https://api.hume.ai/v0/emotion"
        self.headers = {
            "X-Hume-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        if not self.api_key:
            raise ValueError("Hume API key not provided and not found in environment variables")
    
    async def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """Analyze the emotional tone of the provided text.
        
        Args:
            text: The text to analyze for emotional content.
            
        Returns:
            A dictionary containing the emotion analysis results.
            
        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        if not text.strip():
            raise ValueError("Text cannot be empty or whitespace")
            
        payload = {
            "text": text,
            "models": ["emotion"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/predict",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    def extract_primary_emotion(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """Extract the primary emotion scores from the analysis results.
        
        Args:
            analysis: The raw emotion analysis results from Hume AI.
            
        Returns:
            A dictionary mapping emotion names to their confidence scores.
        """
        try:
            emotions = analysis.get("emotion", {})
            return emotions.get("predictions", [{}])[0].get("emotions", {})
        except (KeyError, IndexError, AttributeError):
            return {}


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def example():
        analyzer = EmotionAnalyzer()
        text = "I'm feeling really happy and excited about this project!"
        analysis = await analyzer.analyze_emotion(text)
        emotions = analyzer.extract_primary_emotion(analysis)
        print(f"Emotion analysis for: {text}")
        for emotion, score in emotions.items():
            print(f"{emotion}: {score:.2f}")
    
    asyncio.run(example())
