""
Main Streamlit application for the Conversational Emotion AI.
"""
import os
import asyncio
import streamlit as st
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

# Add the src directory to the Python path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.emotion_analyzer import EmotionAnalyzer
from src.conversation_manager import ConversationManager
from src.response_generator import ResponseGenerator
from src.utils import (
    get_emotion_analysis_summary,
    validate_environment_variables,
    format_timestamp,
    ensure_directory_exists
)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Conversational Emotion AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        max-width: 1200px;
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        padding: 10px;
        font-size: 16px;
    }
    .stButton button {
        width: 100%;
        padding: 0.5rem;
        font-weight: bold;
    }
    .emotion-chart {
        margin-top: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = ConversationManager()

if 'emotion_analyzer' not in st.session_state:
    try:
        st.session_state.emotion_analyzer = EmotionAnalyzer()
    except Exception as e:
        st.error(f"Failed to initialize emotion analyzer: {e}")
        st.stop()

if 'response_generator' not in st.session_state:
    try:
        st.session_state.response_generator = ResponseGenerator()
    except Exception as e:
        st.error(f"Failed to initialize response generator: {e}")
        st.stop()

# Sidebar for settings and info
with st.sidebar:
    st.title("Conversation Settings")
    
    # Model selection
    model_options = ["gpt-4", "gpt-3.5-turbo"]
    selected_model = st.selectbox(
        "Select AI Model",
        model_options,
        index=0
    )
    
    # Temperature control
    temperature = st.slider(
        "Creativity (Temperature)",
        min_value=0.1,
        max_value=1.5,
        value=0.7,
        step=0.1,
        help="Higher values make the output more random, while lower values make it more deterministic."
    )
    
    # Conversation controls
    if st.button("New Conversation"):
        st.session_state.conversation = ConversationManager()
        st.experimental_rerun()
    
    # Display conversation info
    st.markdown("---")
    st.markdown("### Conversation Info")
    st.write(f"**Conversation ID:**")
    st.caption(st.session_state.conversation.conversation_id)
    st.write(f"**Messages:** {len(st.session_state.conversation.messages)}")
    
    # Display API status
    st.markdown("---")
    st.markdown("### API Status")
    if validate_environment_variables():
        st.success("All required API keys are set")
    else:
        st.error("Missing required API keys. Please check your .env file.")
    
    # Add some helpful links
    st.markdown("---")
    st.markdown("### Help & Resources")
    st.markdown("[View Documentation](https://github.com/yourusername/conversational-emotion-ai)")
    st.markdown("[Report an Issue](https://github.com/yourusername/conversational-emotion-ai/issues)")

# Main app
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
        height=100,
        max_chars=1000,
        help="Type your message and press Enter to send"
    )
    
    submit_button = st.form_submit_button("Send Message")

# Process user input
if submit_button and user_input.strip():
    with st.spinner("Analyzing your message..."):
        try:
            # Add user message to conversation
            st.session_state.conversation.add_message(
                role="user",
                content=user_input,
                emotions=None  # Will be updated after analysis
            )
            
            # Analyze emotion
            analysis = asyncio.run(
                st.session_state.emotion_analyzer.analyze_emotion(user_input)
            )
            emotions = st.session_state.emotion_analyzer.extract_primary_emotion(analysis)
            
            # Update the last message with emotion data
            if st.session_state.conversation.messages:
                st.session_state.conversation.messages[-1]['emotions'] = emotions
            
            # Generate response
            messages = st.session_state.response_generator.format_messages_for_api(
                st.session_state.conversation.messages
            )
            
            # Show typing indicator
            with st.spinner("Generating response..."):
                response = asyncio.run(
                    st.session_state.response_generator.generate_response(
                        messages=messages,
                        emotion_context=emotions,
                        temperature=temperature
                    )
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
                st.error(f"Error saving conversation: {e}")
            
            # Rerun to update the UI
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display conversation history
with conversation_container:
    for msg in st.session_state.conversation.messages:
        role = msg['role']
        content = msg['content']
        timestamp = format_timestamp(msg.get('timestamp'))
        
        if role == 'user':
            with st.chat_message("user"):
                st.markdown(f"**You** ({timestamp}):\n\n{content}")
        else:
            with st.chat_message("assistant"):
                st.markdown(f"**AI** ({timestamp}):\n\n{content}")

# Update emotion visualization
if st.session_state.conversation.emotion_history:
    try:
        # Get the latest emotion data
        latest_emotions = st.session_state.conversation.emotion_history[-1]
        
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
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # Display the chart
        emotion_chart.plotly_chart(fig, use_container_width=True)
        
        # Display emotion summary
        st.markdown("### Emotion Summary")
        st.markdown(get_emotion_analysis_summary(latest_emotions))
        
    except Exception as e:
        st.error(f"Error generating emotion visualization: {e}")

# Add some space at the bottom
st.markdown("\n\n---")
st.caption("Conversational Emotion AI - Built with ❤️ using Streamlit, OpenAI, and Hume AI")
