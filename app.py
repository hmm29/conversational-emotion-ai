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

class ConversationApp:
    """Enhanced Streamlit application with advanced conversation management"""
    
    def __init__(self):
        self.conversation_manager = None
        
        # Initialize session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'analytics_data' not in st.session_state:
            st.session_state.analytics_data = {}
        if 'manager_initialized' not in st.session_state:
            st.session_state.manager_initialized = False
    
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
        """Render the main header"""
        st.markdown('<h1 class="main-header">🤖💭 Conversational AI with Emotion Analysis</h1>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        **Experience next-generation conversational AI that understands and responds to emotions.**
        
        This advanced system combines real-time emotion analysis with sophisticated response generation,
        creating truly empathetic and contextually-aware conversations.
        """)
    
    def render_sidebar(self):
        """Enhanced sidebar with system status and controls"""
        with st.sidebar:
            st.header("🎛️ System Status")
            
            # API Status
            openai_status = "✅ Connected" if os.getenv("OPENAI_API_KEY") else "❌ Not Connected"
            hume_status = "✅ Connected" if os.getenv("HUME_API_KEY") else "❌ Not Connected"
            
            st.markdown(f"""
            **OpenAI API:** {openai_status}  
            **Hume AI API:** {hume_status}  
            **Manager:** {"✅ Ready" if st.session_state.manager_initialized else "❌ Not Ready"}
            """)
            
            st.markdown("---")
            
            # Controls
            st.subheader("🎮 Controls")
            if st.button("🗑️ Clear Conversation"):
                st.session_state.conversation_history = []
                st.session_state.analytics_data = {}
                if self.conversation_manager:
                    self.conversation_manager.conversation_turns = []
                    self.conversation_manager.emotion_history.history = []
                st.rerun()
            
            if st.button("📊 Refresh Analytics"):
                if self.conversation_manager:
                    st.session_state.analytics_data = self.conversation_manager.get_conversation_analytics()
                st.rerun()
            
            # Quick Stats
            if st.session_state.analytics_data:
                st.subheader("📈 Quick Stats")
                analytics = st.session_state.analytics_data
                
                if 'session_info' in analytics:
                    session_info = analytics['session_info']
                    st.metric("Total Exchanges", session_info.get('total_turns', 0))
                    st.metric("Avg Confidence", f"{session_info.get('avg_emotion_confidence', 0):.2f}")
                    st.metric("Duration (min)", session_info.get('duration_minutes', 0))
    
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
    
    def render_conversation(self):
        """Render the enhanced conversation interface"""
        st.subheader("💬 Conversation")
        
        # Input area
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message:",
                key="user_input",
                placeholder="How are you feeling today? Tell me what's on your mind..."
            )
        
        with col2:
            send_button = st.button("Send", type="primary")
        
        if (send_button and user_input) or (user_input and st.session_state.get('enter_pressed')):
            # Process the input
            asyncio.run(self.process_user_input(user_input))
            st.rerun()
        
        # Display conversation history
        if st.session_state.conversation_history:
            st.markdown("### Recent Conversation")
            
            for i, exchange in enumerate(reversed(st.session_state.conversation_history[-10:])):
                # User message
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {exchange['user']}
                    <br><small>🎭 Detected: {exchange['emotion']} (confidence: {exchange['confidence']:.2f})</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Bot message
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>AI Assistant:</strong> {exchange['bot']}
                </div>
                """, unsafe_allow_html=True)
                
                if i < len(st.session_state.conversation_history) - 1:
                    st.markdown("---")
        else:
            st.info("👋 Start a conversation! I'm here to listen and understand your emotions.")
    
    def render_analytics_dashboard(self):
        """Render comprehensive analytics dashboard"""
        if not st.session_state.analytics_data:
            st.info("Start a conversation to see detailed analytics!")
            return
        
        analytics = st.session_state.analytics_data
        
        # Session Overview
        if 'session_info' in analytics:
            st.subheader("📋 Session Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            session_info = analytics['session_info']
            
            with col1:
                st.metric("Total Exchanges", session_info.get('total_turns', 0))
            with col2:
                st.metric("Duration", f"{session_info.get('duration_minutes', 0):.1f} min")
            with col3:
                st.metric("Avg Confidence", f"{session_info.get('avg_emotion_confidence', 0):.2f}")
            with col4:
                st.metric("Session ID", session_info.get('session_id', 'N/A')[-8:])
        
        # Emotion Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            if 'emotion_distribution' in analytics and analytics['emotion_distribution']:
                st.subheader("🎭 Emotion Distribution")
                
                emotions_df = pd.DataFrame(
                    list(analytics['emotion_distribution'].items()),
                    columns=['Emotion', 'Count']
                ).sort_values('Count', ascending=True)
                
                fig = px.bar(
                    emotions_df,
                    x='Count',
                    y='Emotion',
                    orientation='h',
                    title="Emotions Throughout Conversation",
                    color='Count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'strategy_distribution' in analytics and analytics['strategy_distribution']:
                st.subheader("🎯 Response Strategies")
                
                strategies_df = pd.DataFrame(
                    list(analytics['strategy_distribution'].items()),
                    columns=['Strategy', 'Count']
                )
                
                fig = px.pie(
                    strategies_df,
                    values='Count',
                    names='Strategy',
                    title="AI Response Strategies Used"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Personality Profile
        if 'personality_profile' in analytics:
            st.subheader("🧠 Personality Insights")
            
            profile = analytics['personality_profile']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Detected Traits:**")
                traits_df = pd.DataFrame(
                    list(profile['traits'].items()),
                    columns=['Trait', 'Score']
                )
                
                fig = px.bar(
                    traits_df,
                    x='Trait',
                    y='Score',
                    title="Personality Trait Analysis",
                    color='Score',
                    color_continuous_scale='blues'
                )
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Confidence Levels:**")
                for trait, confidence in profile['confidence'].items():
                    st.progress(confidence, text=f"{trait.replace('_', ' ').title()}: {confidence:.2f}")
        
        # Recent Emotional Trend
        if 'recent_emotion_trend' in analytics and analytics['recent_emotion_trend']:
            st.subheader("📈 Recent Emotional Trend")
            
            trend_df = pd.DataFrame(
                list(analytics['recent_emotion_trend'].items()),
                columns=['Emotion', 'Average_Score']
            ).sort_values('Average_Score', ascending=False).head(8)
            
            fig = px.line(
                trend_df,
                x='Emotion',
                y='Average_Score',
                title="Emotional Trend (Recent Messages)",
                markers=True
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    async def run(self):
        """Main application runner"""
        # Initialize
        if not st.session_state.manager_initialized:
            await self.initialize_manager()
        
        # Render UI
        self.render_header()
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2 = st.tabs(["💬 Chat", "📊 Analytics"])
        
        with tab1:
            self.render_conversation()
        
        with tab2:
            self.render_analytics_dashboard()

# Run the app
if __name__ == "__main__":
    app = ConversationApp()
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
