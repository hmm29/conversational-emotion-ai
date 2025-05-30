import pytest
import asyncio
import json
import time
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from datetime import datetime

from src.conversation_manager import ConversationManager, PersonalityProfile
from src.emotion_analyzer import HumeEmotionAnalyzer, EmotionResult, EmotionHistory
from src.response_generator import EmotionAwareResponseGenerator, ConversationContext
from src.visualization import EmotionVisualizer
from src.performance import PerformanceMonitor

class TestCompleteSystem:
    """Comprehensive test suite for the entire conversational AI system"""
    
    @pytest.fixture
    def sample_emotion_result(self):
        """Create sample emotion result for testing"""
        return EmotionResult(
            emotions={
                'joy': 0.8,
                'excitement': 0.6,
                'sadness': 0.1,
                'anger': 0.05
            },
            dominant_emotion='joy',
            confidence=0.8,
            timestamp=datetime.now(),
            text="I'm so excited about this new project!"
        )
    
    @pytest.fixture
    def mock_conversation_manager(self):
        """Create mock conversation manager"""
        manager = ConversationManager("test_api_key")
        manager.conversation_turns = []
        manager.emotion_history = EmotionHistory()
        manager.personality_profile = PersonalityProfile()
        return manager
    
    @pytest.mark.asyncio
    async def test_emotion_analysis_pipeline(self):
        """Test the complete emotion analysis pipeline"""
        # Test with mock API
        with patch('src.emotion_analyzer.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": {
                    "predictions": [{
                        "models": {
                            "language": {
                                "grouped_predictions": [{
                                    "predictions": [
                                        {"name": "joy", "score": 0.8},
                                        {"name": "excitement", "score": 0.6},
                                        {"name": "sadness", "score": 0.1}
                                    ]
                                }]
                            }
                        }
                    }]
                }
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            analyzer = HumeEmotionAnalyzer("test_key", "test_secret")
            async with analyzer as a:
                result = await a.analyze_emotion("I'm so happy today!")
                
                assert result.dominant_emotion == 'joy'
                assert result.confidence == 0.8
                assert 'joy' in result.emotions
                assert result.emotions['joy'] == 0.8
    
    def test_emotion_history_tracking(self, sample_emotion_result):
        """Test emotion history management"""
        history = EmotionHistory(max_history=5)
        
        # Add multiple emotions
        for i in range(7):  # More than max_history
            emotion_result = EmotionResult(
                emotions={'joy': 0.5 + i * 0.1},
                dominant_emotion='joy',
                confidence=0.5 + i * 0.1,
                timestamp=datetime.now(),
                text=f"Test message {i}"
            )
            history.add_emotion(emotion_result)
        
        # Verify max history is maintained
        assert len(history.history) == 5
        
        # Test trend calculation
        trend = history.get_emotion_trend()
        assert 'joy' in trend
        assert isinstance(trend['joy'], float)
    
    def test_personality_profile_learning(self):
        """Test personality profile updates over time"""
        profile = PersonalityProfile()
        initial_traits = profile.traits.copy()
        
        # Simulate emotional interactions
        test_emotions = [
            ('joy', 0.9, 0.8),
            ('amusement', 0.8, 0.7),
            ('sadness', 0.7, 0.6),
            ('excitement', 0.9, 0.9)
        ]
        
        for emotion, confidence, engagement in test_emotions:
            emotion_result = EmotionResult(
                emotions={emotion: confidence},
                dominant_emotion=emotion,
                confidence=confidence,
                timestamp=datetime.now(),
                text="test"
            )
            profile.update_from_emotion(emotion_result, engagement)
        
        # Verify learning occurred
        assert profile.update_count == len(test_emotions)
        assert profile.traits != initial_traits
        
        # Verify traits are within valid range
        for trait_value in profile.traits.values():
            assert 0 <= trait_value <= 1
    
    @pytest.mark.asyncio
    async def test_response_generation_strategies(self):
        """Test different response generation strategies"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            
            mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            generator = EmotionAwareResponseGenerator("test_key")
            
            # Test different emotional contexts
            test_contexts = [
                ('joy', 0.8, 'amplify_positive'),
                ('sadness', 0.7, 'empathetic_support'),
                ('anger', 0.6, 'empathetic_support'),
                ('contentment', 0.5, 'gentle_encouragement')
            ]
            
            for emotion, confidence, expected_strategy in test_contexts:
                emotion_result = EmotionResult(
                    emotions={emotion: confidence},
                    dominant_emotion=emotion,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    text="test"
                )
                
                strategy = generator._determine_response_strategy(emotion_result)
                assert strategy == expected_strategy
    
    def test_visualization_components(self):
        """Test all visualization components"""
        visualizer = EmotionVisualizer()
        
        # Test radar chart
        emotion_data = {
            'joy': 0.8,
            'sadness': 0.2,
            'anger': 0.1,
            'excitement': 0.7
        }
        
        radar_fig = visualizer.create_emotion_radar_chart(emotion_data)
        assert radar_fig is not None
        assert len(radar_fig.data) > 0
        
        # Test conversation history
        conversation_history = [
            {
                'emotion': 'joy',
                'confidence': 0.8,
                'user': 'Test message 1'
            },
            {
                'emotion': 'excitement',
                'confidence': 0.7,
                'user': 'Test message 2'
            }
        ]
        
        timeline_fig = visualizer.create_emotion_timeline(conversation_history)
        assert timeline_fig is not None
        
        # Test personality chart
        personality_data = {
            'openness': 0.7,
            'emotional_expressivity': 0.8,
            'humor_appreciation': 0.6
        }
        
        personality_fig = visualizer.create_personality_spider_chart(personality_data)
        assert personality_fig is not None
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, mock_conversation_manager):
        """Test complete conversation from input to response"""
        # Mock the emotion analysis and OpenAI calls
        with patch.object(mock_conversation_manager, '_analyze_emotion') as mock_emotion, \
             patch.object(mock_conversation_manager.response_generator, 'generate_response') as mock_response:
            
            mock_emotion.return_value = EmotionResult(
                emotions={'joy': 0.8},
                dominant_emotion='joy',
                confidence=0.8,
                timestamp=datetime.now(),
                text="Test message"
            )
            
            mock_response.return_value = "That's wonderful to hear!"
            
            # Process a message
            response, emotion_result = await mock_conversation_manager.process_user_input("I'm so happy today!")
            
            # Verify results
            assert response == "That's wonderful to hear!"
            assert emotion_result.dominant_emotion == 'joy'
            assert len(mock_conversation_manager.conversation_turns) == 1

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_api_failure_fallback(self):
        """Test fallback behavior when APIs fail"""
        # Test Hume API failure
        analyzer = HumeEmotionAnalyzer("invalid_key", "invalid_secret")
        result = analyzer._fallback_emotion_analysis("I'm sad")
        
        assert result is not None
        assert result.dominant_emotion is not None
        assert 0 <= result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_openai_failure_fallback(self):
        """Test OpenAI API failure handling"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
            
            generator = EmotionAwareResponseGenerator("test_key")
            emotion_result = EmotionResult(
                emotions={'sadness': 0.7},
                dominant_emotion='sadness',
                confidence=0.7,
                timestamp=datetime.now(),
                text="I'm feeling down"
            )
            
            response = generator._fallback_response(emotion_result)
            assert response is not None
            assert len(response) > 0
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs"""
        visualizer = EmotionVisualizer()
        
        # Test empty data
        empty_fig = visualizer.create_emotion_radar_chart({})
        assert empty_fig is not None
        
        # Test invalid conversation history
        invalid_timeline = visualizer.create_emotion_timeline([])
        assert invalid_timeline is not None

class TestPerformanceBenchmarks:
    """Performance benchmarking tests"""
    
    def test_emotion_analysis_performance(self):
        """Benchmark emotion analysis performance"""
        analyzer = HumeEmotionAnalyzer("", "")  # Use fallback mode
        
        start_time = time.time()
        for i in range(100):
            result = analyzer._fallback_emotion_analysis(f"Test message {i}")
            assert result is not None
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should process each message in under 10ms
        assert avg_time < 0.01
    
    def test_visualization_performance(self):
        """Benchmark visualization generation performance"""
        visualizer = EmotionVisualizer()
        
        emotion_data = {f'emotion_{i}': i/10 for i in range(10)}
        
        start_time = time.time()
        for _ in range(50):
            fig = visualizer.create_emotion_radar_chart(emotion_data)
            assert fig is not None
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 50
        
        # Should generate each chart in under 100ms
        assert avg_time < 0.1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
