"""
Main Streamlit application for the Conversational Emotion AI.

This module provides the web interface for interacting with the Conversational Emotion AI,
allowing users to have conversations with an AI that can detect and respond to emotions.
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

try:
    from src.emotion_analyzer import EmotionAnalyzer
    from src.conversation_manager import ConversationManager
    from src.response_generator import ResponseGenerator
    from src.utils import (
        get_emotion_analysis_summary,
        validate_environment_variables,
        format_timestamp,
        ensure_directory_exists,
        with_retry,
    )
except ImportError as e:
    logging.error("Failed to import required modules: %s", e)
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    logger.error("Failed to load environment variables: %s", e)

# Constants
MODEL_OPTIONS = ["gpt-4", "gpt-3.5-turbo"]
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
