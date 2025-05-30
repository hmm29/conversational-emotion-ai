"""
Main Streamlit application for the Conversational Emotion AI.

This module provides the web interface for interacting with the Conversational Emotion AI,
allowing users to have conversations with an AI that can detect and respond to emotions.
"""
import asyncio
import os
from datetime import datetime
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src.conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Conversational AI with Emotion Analysis",
    page_icon="🤖💭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .emotion-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    
    .analytics-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedConversationApp:
    """Enhanced Streamlit application with advanced features"""
    
    def __init__(self):
        self.conversation_manager = None
        self.visualizer = EmotionVisualizer()
        
        # Initialize session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'analytics_data' not in st.session_state:
            st.session_state.analytics_data = {}
        if 'manager_initialized' not in st.session_state:
            st.session_state.manager_initialized = False
        if 'real_time_mode' not in st.session_state:
            st.session_state.real_time_mode = False
        if 'conversation_settings' not in st.session_state:
            st.session_state.conversation_settings = {
                'response_style': 'balanced',
                'emotion_sensitivity': 0.5,
                'context_window': 5
            }
    
    async def initialize_manager(self):
        """Initialize the conversation manager"""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key:
            st.error("Please set OPENAI_API_KEY in your .env file")
            return False
        
        self.conversation_manager = ConversationManager(openai_api_key)
        st.session_state.manager_initialized = True
        return True
    
    def render_header(self):
        """Render enhanced header with status indicators"""
        st.markdown('<h1 class="main-header">🤖💭 Conversational AI with Emotion Analysis</h1>', 
                   unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            openai_status = "connected" if os.getenv("OPENAI_API_KEY") else "disconnected"
            hume_status = "connected" if os.getenv("HUME_API_KEY") else "disconnected"
            
            st.markdown(f"""
            <div style="text-align: center; margin: 1rem 0;">
                <span class="status-indicator status-{openai_status}"></span>OpenAI
                <span class="status-indicator status-{hume_status}" style="margin-left: 2rem;"></span>Hume AI
                <span class="status-indicator {'status-connected' if st.session_state.manager_initialized else 'status-disconnected'}" style="margin-left: 2rem;"></span>System Ready
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        **Experience next-generation conversational AI that understands and responds to emotions.**
        
        This advanced system combines real-time emotion analysis with sophisticated response generation,
        creating truly empathetic and contextually-aware conversations powered by cutting-edge AI.
        """)
    
    def render_advanced_sidebar(self):
        """Enhanced sidebar with advanced controls"""
        with st.sidebar:
            st.header("🎛️ Advanced Controls")
            
            # System Status Section
            st.subheader("📊 System Status")
            if st.session_state.manager_initialized and self.conversation_manager:
                analytics = self.conversation_manager.get_conversation_analytics()
                if 'session_info' in analytics:
                    session_info = analytics['session_info']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Messages", session_info.get('total_turns', 0))
                        st.metric("Avg Confidence", f"{session_info.get('avg_emotion_confidence', 0):.2f}")
                    with col2:
                        st.metric("Duration", f"{session_info.get('duration_minutes', 0):.1f}m")
                        st.metric("Session ID", session_info.get('session_id', 'N/A')[-6:])
            
            st.markdown("---")
            
            # Conversation Settings
            st.subheader("⚙️ Conversation Settings")
            
            st.session_state.conversation_settings['response_style'] = st.selectbox(
                "Response Style",
                ['empathetic', 'analytical', 'encouraging', 'balanced', 'humorous'],
                index=3,
                help="Choose the AI's conversational style"
            )
            
            st.session_state.conversation_settings['emotion_sensitivity'] = st.slider(
                "Emotion Sensitivity",
                0.1, 1.0, 0.5, 0.1,
                help="How sensitive the AI should be to emotional cues"
            )
            
            st.session_state.conversation_settings['context_window'] = st.slider(
                "Context Memory",
                1, 10, 5,
                help="How many previous messages to remember"
            )
            
            # Real-time Features
            st.subheader("🔄 Real-time Features")
            st.session_state.real_time_mode = st.toggle(
                "Real-time Emotion Tracking",
                st.session_state.real_time_mode,
                help="Enable continuous emotion monitoring"
            )
            
            # Advanced Actions
            st.subheader("🚀 Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.conversation_history = []
                    st.session_state.analytics_data = {}
                    if self.conversation_manager:
                        self.conversation_manager.conversation_turns = []
                        self.conversation_manager.emotion_history.history = []
                    st.rerun()
            
            with col2:
                if st.button("📊 Refresh", use_container_width=True):
                    if self.conversation_manager:
                        st.session_state.analytics_data = self.conversation_manager.get_conversation_analytics()
                    st.rerun()
            
            # Export conversation
            if st.session_state.conversation_history:
                if st.button("📥 Export Chat", use_container_width=True):
                    self.export_conversation()
    
    async def process_user_input(self, user_input: str):
        """Process user input through the conversation manager"""
        if not self.conversation_manager:
            st.error("Conversation manager not initialized")
            return
        
        try:
            # Process through conversation manager
            bot_response, emotion_result = await self.conversation_manager.process_user_input(user_input)
            
            # Update session state
            exchange = {
                'user': user_input,
                'bot': bot_response,
                'emotion': emotion_result.dominant_emotion if emotion_result else 'unknown',
                'confidence': emotion_result.confidence if emotion_result else 0.0,
                'timestamp': datetime.now().isoformat()
            }
            
            st.session_state.conversation_history.append(exchange)
            
            # Update analytics
            st.session_state.analytics_data = self.conversation_manager.get_conversation_analytics()
            
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")
    
    def render_enhanced_conversation(self):
        """Render enhanced conversation interface"""
        st.subheader("💬 Intelligent Conversation")
        
        # Enhanced input area
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                key="user_input",
                placeholder="Share your thoughts, feelings, or ask me anything...",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send 🚀", type="primary", use_container_width=True)
        
        with col3:
            voice_button = st.button("🎤", use_container_width=True, help="Voice input (coming soon)")
        
        if (send_button and user_input) or (user_input and st.session_state.get('enter_pressed')):
            asyncio.run(self.process_user_input(user_input))
            st.rerun()
        
        # Enhanced conversation display
        if st.session_state.conversation_history:
            st.markdown("### 💭 Conversation Flow")
            
            # Show conversation in reverse order (most recent first)
            for i, exchange in enumerate(reversed(st.session_state.conversation_history[-10:])):
                # User message with emotion analysis
                emotion_indicator = "🟢" if exchange['confidence'] > 0.7 else "🟡" if exchange['confidence'] > 0.4 else "🔴"
                
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {exchange['user']}
                    <br><small>{emotion_indicator} <strong>{exchange['emotion'].title()}</strong> 
                    (confidence: {exchange['confidence']:.2f}) • 
                    {datetime.fromisoformat(exchange['timestamp']).strftime('%H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Bot message with strategy info
                strategy_used = st.session_state.analytics_data.get('strategy_distribution', {})
                
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>AI Assistant:</strong> {exchange['bot']}
                    <br><small>💡 Response generated with {exchange.get('settings_used', {}).get('response_style', 'balanced')} style</small>
                </div>
                """, unsafe_allow_html=True)
                
                if i < len(st.session_state.conversation_history) - 1:
                    st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.3;'>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="analytics-card">
                <h3>👋 Welcome to Advanced Conversational AI!</h3>
                <p>I'm here to have meaningful conversations while understanding your emotions. 
                Share your thoughts, feelings, or ask me anything - I'll adapt my responses based on your emotional state.</p>
                <p><strong>Try saying:</strong></p>
                <ul>
                    <li>"I'm feeling excited about my new project!"</li>
                    <li>"I'm worried about an upcoming presentation"</li>
                    <li>"Tell me something interesting about AI"</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def render_advanced_analytics(self):
        """Render comprehensive analytics dashboard"""
        if not st.session_state.analytics_data:
            st.info("Start a conversation to see detailed analytics and visualizations!")
            return
        
        analytics = st.session_state.analytics_data
        
        # Key Metrics Row
        if 'session_info' in analytics:
            st.subheader("📋 Session Overview")
            session_info = analytics['session_info']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{session_info.get('total_turns', 0)}</h3>
                    <p>Total Exchanges</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{session_info.get('duration_minutes', 0):.1f}m</h3>
                    <p>Duration</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{session_info.get('avg_emotion_confidence', 0):.2f}</h3>
                    <p>Avg Confidence</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{session_info.get('session_id', 'N/A')[-6:]}</h3>
                    <p>Session ID</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Visualization Grid
        col1, col2 = st.columns(2)
        
        with col1:
            # Current emotion radar
            if st.session_state.conversation_history:
                latest_emotions = st.session_state.conversation_history[-1].get('emotion_details', {})
                if latest_emotions:
                    radar_fig = self.visualizer.create_emotion_radar_chart(latest_emotions)
                    st.plotly_chart(radar_fig, use_container_width=True)
            
            # Emotion timeline
            timeline_fig = self.visualizer.create_emotion_timeline(st.session_state.conversation_history)
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        with col2:
            # Personality spider chart
            if 'personality_profile' in analytics:
                personality_fig = self.visualizer.create_personality_spider_chart(
                    analytics['personality_profile']['traits']
                )
                st.plotly_chart(personality_fig, use_container_width=True)
            
            # Response strategy pie chart
            if 'strategy_distribution' in analytics:
                strategy_fig = self.visualizer.create_response_strategy_pie(
                    analytics['strategy_distribution']
                )
                st.plotly_chart(strategy_fig, use_container_width=True)
        
        # Full-width emotion heatmap
        if len(st.session_state.conversation_history) > 3:
            st.subheader("🔥 Emotion Intensity Heatmap")
            heatmap_fig = self.visualizer.create_emotion_heatmap(st.session_state.conversation_history)
            st.plotly_chart(heatmap_fig, use_container_width=True)
    
    async def run(self):
        """Main application runner with enhanced features"""
        # Initialize
        if not st.session_state.manager_initialized:
            await self.initialize_manager()
        
        # Render UI
        self.render_header()
        self.render_advanced_sidebar()
        
        # Main content with enhanced tabs
        tab1, tab2, tab3 = st.tabs(["💬 Conversation", "📊 Analytics", "🔬 Research Mode"])
        
        with tab1:
            self.render_enhanced_conversation()
        
        with tab2:
            self.render_advanced_analytics()
        
        with tab3:
            self.render_research_mode()
    
    def render_research_mode(self):
        """Render research and experimentation interface"""
        st.subheader("🔬 Research & Experimentation")
        
        st.markdown("""
        This mode allows you to experiment with different AI configurations and analyze the results.
        Perfect for understanding how different settings affect conversation quality and emotional understanding.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🧪 Experiment Settings")
            
            # Experiment configuration
            experiment_name = st.text_input("Experiment Name", "Emotion Sensitivity Test")
            
            sensitivity_values = st.multiselect(
                "Test Emotion Sensitivity Values",
                [0.1, 0.3, 0.5, 0.7, 0.9],
                default=[0.3, 0.5, 0.7]
            )
            
            response_styles = st.multiselect(
                "Test Response Styles",
                ['empathetic', 'analytical', 'encouraging', 'balanced', 'humorous'],
                default=['empathetic', 'balanced']
            )
            
            if st.button("🚀 Run Experiment"):
                st.info("Experiment framework ready! This would test different configurations automatically.")
        
        with col2:
            st.markdown("### 📈 Research Insights")
            
            if st.session_state.conversation_history:
                # Calculate some basic research metrics
                total_messages = len(st.session_state.conversation_history)
                avg_confidence = sum(msg['confidence'] for msg in st.session_state.conversation_history) / total_messages
                
                st.metric("Sample Size", total_messages)
                st.metric("Avg Emotion Confidence", f"{avg_confidence:.3f}")
                
                # Emotion distribution
                emotions = [msg['emotion'] for msg in st.session_state.conversation_history]
                emotion_counts = pd.Series(emotions).value_counts()
                
                st.markdown("**Emotion Distribution:**")
                for emotion, count in emotion_counts.head().items():
                    st.write(f"• {emotion.title()}: {count} ({count/total_messages*100:.1f}%)")

# Run the app
if __name__ == "__main__":
    app = AdvancedConversationApp()
    asyncio.run(app.run())
DEFAULT_TEMPERATURE = 0.7
MAX_INPUT_LENGTH = 1000

# Set page configuration
st.set_page_config(
    page_title="Conversational Emotion AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def setup_custom_css() -> None:
    """Inject custom CSS for better styling."""
    st.markdown("""
    <style>
        .main {
            max-width: 1200px;
            padding: 2rem;
        }
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            padding: 10px;
            font-size: 16px;
            min-height: 100px;
        }
        .stButton button {
            width: 100%;
            padding: 0.75rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .emotion-chart {
            margin: 1.5rem 0;
            border-radius: 8px;
            overflow: hidden;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
            padding: 1.5rem;
        }
        .conversation-message {
            margin-bottom: 1.5rem;
            padding: 1rem;
            border-radius: 8px;
            background-color: #f8f9fa;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 20%;
        }
        .ai-message {
            background-color: #f5f5f5;
            margin-right: 20%;
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state() -> None:
    """Initialize the Streamlit session state."""
    if 'conversation' not in st.session_state:
        st.session_state.conversation = ConversationManager()

    if 'emotion_analyzer' not in st.session_state:
        try:
            st.session_state.emotion_analyzer = EmotionAnalyzer()
        except Exception as e:
            logger.error("Failed to initialize emotion analyzer: %s", e)
            st.error(f"Failed to initialize emotion analyzer: {e}")
            st.stop()

    if 'response_generator' not in st.session_state:
        try:
            st.session_state.response_generator = ResponseGenerator()
        except Exception as e:
            logger.error("Failed to initialize response generator: %s", e)
            st.error(f"Failed to initialize response generator: {e}")
            st.stop()

    # Initialize other session state variables
    if 'temperature' not in st.session_state:
        st.session_state.temperature = DEFAULT_TEMPERATURE
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = MODEL_OPTIONS[0]  # Default to gpt-4

def render_sidebar() -> None:
    """Render the sidebar with settings and information."""
    with st.sidebar:
        st.title("Conversation Settings")
        
        # Model selection
        st.session_state.selected_model = st.selectbox(
            "Select AI Model",
            MODEL_OPTIONS,
            index=MODEL_OPTIONS.index(st.session_state.get('selected_model', MODEL_OPTIONS[0]))
        )
        
        # Temperature control
        st.session_state.temperature = st.slider(
            "Creativity (Temperature)",
            min_value=0.1,
            max_value=1.5,
            value=st.session_state.get('temperature', DEFAULT_TEMPERATURE),
            step=0.1,
            help=("Controls randomness in the AI's responses. "
                 "Lower values make responses more focused and deterministic, "
                 "while higher values make them more creative and varied.")
        )
        
        # Conversation controls
        if st.button("🧹 New Conversation", use_container_width=True):
            st.session_state.conversation = ConversationManager()
            st.rerun()
        
        # Display conversation info
        st.markdown("---")
        st.markdown("### Conversation Info")
        st.write(f"**Conversation ID:**")
        st.caption(st.session_state.conversation.conversation_id)
        st.write(f"**Messages:** {len(st.session_state.conversation.messages)}")
        
        # Display API status
        st.markdown("---")
        st.markdown("### API Status")
        try:
            if validate_environment_variables():
                st.success("✅ All required API keys are set")
            else:
                st.error("❌ Missing required API keys. Please check your .env file.")
        except Exception as e:
            logger.error("Error validating environment variables: %s", e)
            st.error(f"Error checking API status: {e}")
        
        # Add some helpful links
        st.markdown("---")
        st.markdown("### Help & Resources")
        st.page_link("https://github.com/hmm29/conversational-emotion-ai", 
                     label="📚 View Documentation", icon="📚")
        st.page_link("https://github.com/hmm29/conversational-emotion-ai/issues", 
                     label="🐛 Report an Issue", icon="🐛")

def render_main_interface() -> tuple[st.delta_generator.DeltaGenerator, st.delta_generator.DeltaGenerator]:
    """Render the main chat interface."""
    st.title("Conversational Emotion AI")
    st.markdown("An AI that understands and responds to your emotions in real-time.")
    
    # Display conversation history
    st.markdown("### Conversation")
    conversation_container = st.container()
    
    # Emotion visualization
    st.markdown("### Emotion Analysis")
    emotion_chart = st.empty()
    
    # User input
    with st.form("chat_input_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message here...",
            key="user_input",
            height=120,
            max_chars=MAX_INPUT_LENGTH,
            help=f"Type your message (max {MAX_INPUT_LENGTH} characters) and press Enter to send"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submit_button = st.form_submit_button("💬 Send Message", use_container_width=True)
        with col2:
            if st.form_submit_button("🔄 Clear Input", type="secondary", use_container_width=True):
                st.session_state.user_input = ""
                st.rerun()
    
    return conversation_container, emotion_chart

@with_retry(max_retries=3, backoff_factor=0.5)
async def process_user_input(user_input: str) -> None:
    """Process user input and generate a response."""
    try:
        # Add user message to conversation
        st.session_state.conversation.add_message(
            role="user",
            content=user_input,
            emotions=None  # Will be updated after analysis
        )
        
        # Analyze emotion
        analysis = await st.session_state.emotion_analyzer.analyze_emotion(user_input)
        emotions = st.session_state.emotion_analyzer.extract_primary_emotion(analysis)
        
        # Update the last message with emotion data
        if st.session_state.conversation.messages:
            st.session_state.conversation.messages[-1]['emotions'] = emotions
        
        # Generate response
        messages = st.session_state.response_generator.format_messages_for_api(
            st.session_state.conversation.messages
        )
        
        # Generate AI response
        response = await st.session_state.response_generator.generate_response(
            messages=messages,
            emotion_context=emotions,
            temperature=st.session_state.temperature,
            model=st.session_state.selected_model
        )
        
        # Add AI response to conversation
        st.session_state.conversation.add_message(
            role="assistant",
            content=response,
            emotions=None
        )
        
        # Save conversation
        try:
            st.session_state.conversation.save_conversation()
        except Exception as e:
            logger.error("Error saving conversation: %s", e)
            st.error(f"Error saving conversation: {e}")
        
    except Exception as e:
        logger.error("Error processing user input: %s", e, exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        raise

def render_conversation(container: st.delta_generator.DeltaGenerator) -> None:
    """Render the conversation history."""
    with container:
        for msg in st.session_state.conversation.messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            timestamp = format_timestamp(msg.get('timestamp'))
            
            if not all([role, content]):
                continue
                
            # Determine message styling
            if role == 'user':
                with st.chat_message("user"):
                    st.markdown(f"**You** ({timestamp})\n\n{content}")
            else:  # assistant
                with st.chat_message("assistant"):
                    st.markdown(f"**AI** ({timestamp})\n\n{content}")
                    
                    # Display emotions if available
                    emotions = msg.get('emotions')
                    if emotions and isinstance(emotions, dict):
                        with st.expander("Emotion Analysis"):
                            st.write(get_emotion_analysis_summary(emotions))

def render_emotion_visualization(container: st.delta_generator.DeltaGenerator) -> None:
    """Render the emotion visualization chart."""
    if not st.session_state.conversation.emotion_history:
        container.info("Emotion data will appear here after your first message.")
        return
    
    try:
        # Get the latest emotion data
        latest_emotions = st.session_state.conversation.emotion_history[-1]
        if not latest_emotions:
            container.warning("No emotion data available for the latest message.")
            return
        
        # Create a DataFrame for visualization
        df = pd.DataFrame(
            list(latest_emotions.items()),
            columns=['Emotion', 'Score']
        ).sort_values('Score', ascending=False).head(5)
        
        # Create a bar chart
        fig = px.bar(
            df,
            x='Emotion',
            y='Score',
            color='Score',
            color_continuous_scale='Bluered',
            title="Emotion Analysis"
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title="Emotion",
            yaxis_title="Score",
            showlegend=False,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(tickangle=-45)
        )
        
        # Display the chart
        container.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error("Error generating emotion visualization: %s", e, exc_info=True)
        container.error(f"Error generating emotion visualization: {e}")


def render_footer() -> None:
    """Render the application footer."""
    st.markdown("\n\n---")
    st.caption(
        "Conversational Emotion AI v1.0.0 | "
        "Built with ❤️ using Streamlit, OpenAI, and Hume AI | "
        "[Privacy Policy](#) | [Terms of Use](#)"
    )


def main() -> None:
    """Main entry point for the Streamlit application."""
    # Setup the page
    setup_custom_css()
    initialize_session_state()
    
    # Render the sidebar
    render_sidebar()
    
    # Render the main interface
    conversation_container, emotion_chart = render_main_interface()
    
    # Process user input if form is submitted
    if st.session_state.get('submit_button') and st.session_state.get('user_input', '').strip():
        with st.spinner("Processing your message..."):
            asyncio.run(process_user_input(st.session_state.user_input))
            st.rerun()
    
    # Render conversation history
    render_conversation(conversation_container)
    
    # Render emotion visualization
    render_emotion_visualization(emotion_chart)
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
