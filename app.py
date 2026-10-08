"""Streamlit chat app. Run with: streamlit run app.py"""
import os

import streamlit as st
from dotenv import load_dotenv

from src.conversation_manager import ConversationManager
from src.emotion_analyzer import HumeEmotionAnalyzer, KeywordEmotionAnalyzer
from src.response_generator import DEFAULT_MODEL, EmotionAwareResponseGenerator
from src.visualization import approach_pie, emotion_radar, emotion_timeline, profile_bars

load_dotenv()
st.set_page_config(page_title="Conversational Emotion AI", page_icon="💬", layout="wide")


def build_manager() -> ConversationManager:
    """Use Hume and OpenAI when their keys are set, offline stand-ins otherwise."""
    hume_key = os.getenv("HUME_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    analyzer = HumeEmotionAnalyzer(hume_key) if hume_key else KeywordEmotionAnalyzer()
    generator = EmotionAwareResponseGenerator(
        api_key=openai_key or None,
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
    )
    return ConversationManager(analyzer, generator)


if "manager" not in st.session_state:
    st.session_state.manager = build_manager()
manager: ConversationManager = st.session_state.manager

prompt = st.chat_input("Say something")
if prompt and prompt.strip():
    manager.process_message(prompt)

with st.sidebar:
    st.header("Setup")
    if manager.analyzer.name == "hume":
        st.success("Emotion analysis: Hume AI")
    else:
        st.warning("Emotion analysis: keyword matcher (set HUME_API_KEY to use Hume AI)")
    if manager.generator.has_model:
        st.success(f"Replies: OpenAI {manager.generator.model}")
    else:
        st.warning("Replies: canned text (set OPENAI_API_KEY to use OpenAI)")

    st.header("Conversation")
    st.download_button(
        "Download as JSON",
        data=manager.export_json(),
        file_name="conversation.json",
        mime="application/json",
        disabled=not manager.turns,
    )
    if st.button("Start over"):
        manager.clear()
        st.rerun()

st.title("Conversational Emotion AI")
st.caption("A chatbot that reads the emotional tone of each message and adapts how it replies.")

chat_tab, analytics_tab = st.tabs(["Conversation", "Analytics"])

with chat_tab:
    chat_column, emotion_column = st.columns([3, 2])

    with chat_column:
        if not manager.turns:
            st.info("Type a message below to start.")
        for turn in manager.turns:
            with st.chat_message("user"):
                st.write(turn.user_message)
            with st.chat_message("assistant"):
                st.write(turn.bot_response)
                note = f"{turn.emotion_result.dominant_emotion} · {turn.approach.replace('_', ' ')}"
                if turn.used_fallback:
                    note += " · canned reply"
                st.caption(note)

    with emotion_column:
        if manager.turns:
            latest = manager.turns[-1].emotion_result
            st.metric("Dominant emotion", latest.dominant_emotion.title(), f"score {latest.confidence:.2f}", delta_color="off")
            if latest.source == "keywords" and manager.analyzer.name == "hume":
                st.caption("Hume AI was unreachable for this message, so the keyword matcher was used.")
            if latest.confidence > 0:
                st.plotly_chart(emotion_radar(latest.emotions), key="radar")

with analytics_tab:
    if not manager.turns:
        st.info("Charts appear here once the conversation has started.")
    else:
        summary = manager.summary()
        first, second, third = st.columns(3)
        first.metric("Messages", summary["turns"])
        second.metric("Most common emotion", summary["most_common_emotion"].title())
        third.metric("Average top score", f"{summary['average_confidence']:.2f}")

        st.plotly_chart(emotion_timeline(manager.turns), key="timeline")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(approach_pie(manager.approach_counts()), key="approaches")
        with right:
            st.plotly_chart(profile_bars(manager.profile.traits), key="profile")
            st.caption("The profile is a heuristic summary of this conversation, not a psychological assessment.")
