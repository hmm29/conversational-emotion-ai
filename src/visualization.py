import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
import streamlit as st

class EmotionVisualizer:
    """Advanced visualization components for emotion analysis"""
    
    def __init__(self):
        self.color_palette = {
            'joy': '#FFD700',
            'excitement': '#FF6B35',
            'amusement': '#FF9F1C',
            'contentment': '#7FB069',
            'satisfaction': '#A8DADC',
            'interest': '#457B9D',
            'enthusiasm': '#E63946',
            'sadness': '#1D3557',
            'anger': '#FF4500',
            'fear': '#6A4C93',
            'disappointment': '#8D99AE',
            'shame': '#2B2D42',
            'doubt': '#6C757D',
            'tiredness': '#495057',
            'surprise': '#F72585',
            'disgust': '#560BAD',
            'contempt': '#3A0CA3',
            'sympathy': '#4361EE'
        }
        self.update_interval = 1  # seconds for real-time updates
        self.max_points = 50  # Maximum points to show in real-time charts
        
    def create_emotion_radar_chart(self, emotion_data: Dict[str, float]) -> go.Figure:
        """Create a radar chart showing current emotion distribution"""
        emotions = list(emotion_data.keys())
        values = list(emotion_data.values())
        
        # Add the first emotion at the end to close the radar chart
        emotions_closed = emotions + [emotions[0]]
        values_closed = values + [values[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=emotions_closed,
            fill='toself',
            fillcolor='rgba(66, 165, 245, 0.2)',
            line=dict(color='rgba(66, 165, 245, 1)', width=2),
            name='Current Emotions'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title={
                'text': 'Current Emotional State',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            height=400
        )
        
        return fig
    
    def create_emotion_timeline(self, conversation_history: List[Dict[str, Any]]) -> go.Figure:
        """Create timeline showing emotion changes over conversation"""
        if not conversation_history:
            return go.Figure()
        
        # Extract data for timeline
        timestamps = []
        emotions = []
        confidences = []
        messages = []
        
        for i, exchange in enumerate(conversation_history):
            timestamps.append(i + 1)  # Message number
            emotions.append(exchange.get('emotion', 'neutral'))
            confidences.append(exchange.get('confidence', 0.5))
            messages.append(exchange.get('user', '')[:50] + '...' if len(exchange.get('user', '')) > 50 else exchange.get('user', ''))
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add emotion confidence line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=confidences,
                mode='lines+markers',
                name='Confidence',
                line=dict(color='#2E8B57', width=3),
                marker=dict(size=8),
                hovertemplate='<b>Message %{x}</b><br>Confidence: %{y:.2f}<extra></extra>'
            ),
            secondary_y=False,
        )
        
        # Add emotion markers with colors
        emotion_colors = [self.color_palette.get(emotion, '#666666') for emotion in emotions]
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[0.5] * len(timestamps),  # Fixed y position for emotion markers
                mode='markers+text',
                name='Emotions',
                marker=dict(
                    size=15,
                    color=emotion_colors,
                    line=dict(width=2, color='white')
                ),
                text=emotions,
                textposition='top center',
                hovertemplate='<b>Message %{x}</b><br>Emotion: %{text}<br>Message: %{customdata}<extra></extra>',
                customdata=messages
            ),
            secondary_y=True,
        )
        
        # Update layout
        fig.update_xaxes(title_text="Message Number")
        fig.update_yaxes(title_text="Confidence Score", secondary_y=False)
        fig.update_yaxes(title_text="Emotions", showticklabels=False, secondary_y=True)
        
        fig.update_layout(
            title={
                'text': 'Emotional Journey Throughout Conversation',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            height=400,
            hovermode='x unified'
        )
        
        return fig
    
    def create_personality_spider_chart(self, personality_data: Dict[str, float]) -> go.Figure:
        """Create spider chart for personality traits"""
        traits = list(personality_data.keys())
        values = list(personality_data.values())
        
        # Clean up trait names for display
        display_traits = [trait.replace('_', ' ').title() for trait in traits]
        
        # Close the spider chart
        display_traits_closed = display_traits + [display_traits[0]]
        values_closed = values + [values[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=display_traits_closed,
            fill='toself',
            fillcolor='rgba(156, 39, 176, 0.2)',
            line=dict(color='rgba(156, 39, 176, 1)', width=3),
            name='Personality Profile'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    tickmode='linear',
                    tick0=0,
                    dtick=0.2
                )),
            showlegend=False,
            title={
                'text': 'Personality Profile',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            height=400
        )
        
        return fig
    
    def create_response_strategy_pie(self, strategy_data: Dict[str, int]) -> go.Figure:
        """Create pie chart for response strategies used"""
        if not strategy_data:
            return go.Figure()
        
        strategies = list(strategy_data.keys())
        counts = list(strategy_data.values())
        
        # Clean up strategy names
        display_strategies = [strategy.replace('_', ' ').title() for strategy in strategies]
        
        fig = go.Figure(data=[go.Pie(
            labels=display_strategies,
            values=counts,
            hole=0.4,
            marker=dict(
                colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
                line=dict(color='#FFFFFF', width=2)
            )
        )])
        
        fig.update_layout(
            title={
                'text': 'AI Response Strategies',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        return fig
    
    def create_emotion_heatmap(self, conversation_history: List[Dict[str, Any]]) -> go.Figure:
        """Create heatmap showing emotion intensity over time"""
        if not conversation_history:
            return go.Figure()
        
        # Extract emotion data
        emotions_over_time = {}
        primary_emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'excitement', 'amusement', 'contentment']
        
        for i, exchange in enumerate(conversation_history):
            if 'emotion_details' in exchange:
                for emotion in primary_emotions:
                    if emotion not in emotions_over_time:
                        emotions_over_time[emotion] = []
                    emotions_over_time[emotion].append(exchange['emotion_details'].get(emotion, 0))
            else:
                # Fallback for basic emotion data
                current_emotion = exchange.get('emotion', 'neutral')
                for emotion in primary_emotions:
                    if emotion not in emotions_over_time:
                        emotions_over_time[emotion] = []
                    emotions_over_time[emotion].append(1.0 if emotion == current_emotion else 0.0)
        
        # Create heatmap data
        z_data = []
        y_labels = []
        
        for emotion in primary_emotions:
            if emotion in emotions_over_time:
                z_data.append(emotions_over_time[emotion])
                y_labels.append(emotion.title())
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=[f'Msg {i+1}' for i in range(len(conversation_history))],
            y=y_labels,
            colorscale='Viridis',
            showscale=True,
            hoverongaps=False
        ))
        
        fig.update_layout(
            title={
                'text': 'Emotion Intensity Heatmap',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            xaxis_title="Messages",
            yaxis_title="Emotions",
            height=400
        )
        
        return fig
    
    def create_real_time_dashboard(self, container: st.delta_generator.DeltaGenerator):
        """Create real-time visualization dashboard"""
        if 'emotion_history' not in st.session_state:
            st.session_state.emotion_history = []
        
        # Create three columns for different visualizations
        col1, col2, col3 = container.columns(3)
        
        with col1:
            # Real-time emotion radar
            if st.session_state.emotion_history:
                current_emotions = st.session_state.emotion_history[-1]
                radar_fig = self.create_emotion_radar_chart(current_emotions)
                st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            # Personality profile
            if 'personality_profile' in st.session_state:
                personality_fig = self.create_personality_spider_chart(st.session_state.personality_profile)
                st.plotly_chart(personality_fig, use_container_width=True)
        
        with col3:
            # Response strategy
            if 'response_strategies' in st.session_state:
                strategy_fig = self.create_response_strategy_pie(st.session_state.response_strategies)
                st.plotly_chart(strategy_fig, use_container_width=True)
        
        # Create a full-width heatmap
        st.plotly_chart(self.create_emotion_heatmap(st.session_state.emotion_history), use_container_width=True)
        
    def add_emotion_data(self, emotions: Dict[str, float]):
        """Add new emotion data to session state for real-time updates"""
        if len(st.session_state.emotion_history) > self.max_points:
            st.session_state.emotion_history.pop(0)
        st.session_state.emotion_history.append(emotions)
        
    def update_personality_profile(self, traits: Dict[str, float]):
        """Update personality profile in session state"""
        if 'personality_profile' not in st.session_state:
            st.session_state.personality_profile = traits
        else:
            # Update existing profile with new data
            for trait, value in traits.items():
                if trait in st.session_state.personality_profile:
                    # Average the new value with existing value
                    st.session_state.personality_profile[trait] = (
                        st.session_state.personality_profile[trait] + value) / 2
                else:
                    st.session_state.personality_profile[trait] = value
    
    def update_response_strategy(self, strategy: str):
        """Track response strategy usage"""
        if 'response_strategies' not in st.session_state:
            st.session_state.response_strategies = {}
        
        if strategy in st.session_state.response_strategies:
            st.session_state.response_strategies[strategy] += 1
        else:
            st.session_state.response_strategies[strategy] = 1
