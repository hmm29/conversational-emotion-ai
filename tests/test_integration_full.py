import pytest
import asyncio
import json
from datetime import datetime
from src.conversation_manager import ConversationManager
from src.visualization import EmotionVisualizer
from src.emotion_analyzer import EmotionResult
from src.response_generator import EmotionAwareResponseGenerator

class TestFullIntegration:
    """Comprehensive integration tests for the entire system"""
    
    @pytest.fixture
    async def conversation_manager(self):
        """Create a test conversation manager"""
        manager = ConversationManager(
            openai_api_key="test_key",
            hume_api_key="test_key"
        )
        return manager
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, conversation_manager):
        """Test complete conversation flow with multiple exchanges"""
        test_messages = [
            "I'm really excited about my new job!",
            "But I'm also a bit nervous about the first day",
            "Do you have any advice for starting at a new company?",
            "Thank you, that's really helpful!"
        ]
        
        responses = []
        for message in test_messages:
            # Process message through full pipeline
            response, emotion_result = await conversation_manager.process_user_input(message)
            responses.append((message, response, emotion_result))
        
        # Verify conversation tracking
        assert len(responses) == len(test_messages)
        assert len(conversation_manager.conversation_turns) == len(test_messages)
        
        # Verify analytics generation
        analytics = conversation_manager.get_conversation_analytics()
        assert 'session_info' in analytics
        assert analytics['session_info']['total_turns'] == len(test_messages)
        
        # Verify emotion tracking
        assert 'emotion_history' in analytics
        assert len(analytics['emotion_history']) > 0
        
        # Verify personality profile
        assert 'personality_profile' in analytics
        assert len(analytics['personality_profile']['traits']) > 0
    
    def test_emotion_visualizer(self):
        """Test emotion visualization components"""
        visualizer = EmotionVisualizer()
        
        # Test radar chart creation
        emotion_data = {
            'joy': 0.8,
            'excitement': 0.6,
            'sadness': 0.1,
            'anger': 0.0
        }
        
        radar_fig = visualizer.create_emotion_radar_chart(emotion_data)
        assert radar_fig is not None
        assert len(radar_fig.data) > 0
        
        # Test timeline visualization
        test_history = [
            {
                'emotion': 'joy',
                'confidence': 0.8,
                'timestamp': datetime.now()
            },
            {
                'emotion': 'excitement',
                'confidence': 0.7,
                'timestamp': datetime.now()
            }
        ]
        
        timeline_fig = visualizer.create_emotion_timeline(test_history)
        assert timeline_fig is not None
        assert len(timeline_fig.data) > 0
    
    def test_conversation_export(self, conversation_manager):
        """Test conversation export functionality"""
        test_history = [
            {
                'user': 'Hello!',
                'bot': 'Hi there!',
                'emotion': 'joy',
                'confidence': 0.8,
                'timestamp': datetime.now().isoformat(),
                'emotion_details': {
                    'joy': 0.8,
                    'excitement': 0.6,
                    'sadness': 0.1
                }
            }
        ]
        
        # Test JSON serialization
        export_data = {
            'conversation_history': test_history,
            'analytics': conversation_manager.get_conversation_analytics(),
            'exported_at': datetime.now().isoformat(),
            'settings': conversation_manager.conversation_settings
        }
        
        json_str = json.dumps(export_data, indent=2)
        assert json_str is not None
        
        # Test deserialization
        loaded_data = json.loads(json_str)
        assert loaded_data['conversation_history'] == test_history
        assert 'analytics' in loaded_data
        assert 'exported_at' in loaded_data
    
    def test_personality_profile_updates(self, conversation_manager):
        """Test personality profile learning over time"""
        initial_traits = conversation_manager.personality_profile.traits.copy()
        
        # Simulate emotional conversations
        test_emotions = [
            ('joy', 0.9, 'excited'),
            ('excitement', 0.8, 'optimistic'),
            ('amusement', 0.7, 'playful'),
            ('contentment', 0.8, 'satisfied')
        ]
        
        for emotion, confidence, trait in test_emotions:
            emotion_result = EmotionResult(
                emotions={emotion: confidence},
                dominant_emotion=emotion,
                confidence=confidence,
                timestamp=datetime.now(),
                text="test message"
            )
            
            conversation_manager.personality_profile.update_from_emotion(emotion_result)
        
        # Verify traits have been updated
        updated_traits = conversation_manager.personality_profile.traits
        assert updated_traits != initial_traits
        
        # Verify learning has occurred
        assert conversation_manager.personality_profile.update_count > 0
        
        # Verify trait confidence scores
        for trait, score in updated_traits.items():
            assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_response_generator_integration(self, conversation_manager):
        """Test response generator with emotion context"""
        # Create test context
        test_context = {
            'user_message': "I'm feeling really down today",
            'emotion_result': EmotionResult(
                emotions={'sadness': 0.9, 'disappointment': 0.7},
                dominant_emotion='sadness',
                confidence=0.9,
                timestamp=datetime.now(),
                text="I'm feeling really down today"
            ),
            'conversation_history': [],
            'personality_profile': conversation_manager.personality_profile
        }
        
        # Generate response
        response_generator = EmotionAwareResponseGenerator()
        response = await response_generator.generate_response(test_context)
        
        assert response is not None
        assert len(response) > 0
        
        # Verify response strategy
        assert hasattr(conversation_manager, 'last_strategy_used')
        assert conversation_manager.last_strategy_used == 'empathetic_support'

if __name__ == "__main__":
    pytest.main([__file__])
