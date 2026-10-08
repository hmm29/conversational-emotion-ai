"""Plotly figures for the app. Pure functions: data in, figure out."""
from typing import Dict, List

import plotly.graph_objects as go

from .conversation_manager import ConversationTurn

LAYOUT = dict(margin=dict(l=30, r=30, t=50, b=30), height=340)


def emotion_radar(emotions: Dict[str, float], top_n: int = 8) -> go.Figure:
    """Radar chart of the strongest emotions in one message."""
    ranked = sorted(emotions.items(), key=lambda item: item[1], reverse=True)[:top_n]
    names = [name.title() for name, _ in ranked]
    scores = [score for _, score in ranked]
    figure = go.Figure(
        go.Scatterpolar(r=scores + scores[:1], theta=names + names[:1], fill="toself", name="Score")
    )
    upper = max(scores) * 1.1 if scores and max(scores) > 0 else 1.0
    figure.update_layout(
        title="Emotions in the last message",
        polar=dict(radialaxis=dict(range=[0, upper], visible=True)),
        showlegend=False,
        **LAYOUT,
    )
    return figure


def emotion_timeline(turns: List[ConversationTurn], top_n: int = 4) -> go.Figure:
    """Line chart of the most prominent emotions across the conversation."""
    totals: Dict[str, float] = {}
    for turn in turns:
        for name, score in turn.emotion_result.emotions.items():
            totals[name] = totals.get(name, 0.0) + score
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:top_n]
    leaders = [name for name, total in ranked if total > 0]

    figure = go.Figure()
    messages = list(range(1, len(turns) + 1))
    for name in leaders:
        figure.add_trace(
            go.Scatter(
                x=messages,
                y=[turn.emotion_result.emotions.get(name, 0.0) for turn in turns],
                mode="lines+markers",
                name=name.title(),
            )
        )
    figure.update_layout(
        title="Emotions over the conversation",
        xaxis=dict(title="Message", dtick=1),
        yaxis=dict(title="Score", rangemode="tozero"),
        **LAYOUT,
    )
    return figure


def approach_pie(counts: Dict[str, int]) -> go.Figure:
    """Share of replies generated with each response approach."""
    labels = [name.replace("_", " ").title() for name in counts]
    figure = go.Figure(go.Pie(labels=labels, values=list(counts.values()), hole=0.45))
    figure.update_layout(title="Response approaches used", **LAYOUT)
    return figure


def profile_bars(traits: Dict[str, float]) -> go.Figure:
    """Horizontal bars for the running conversation profile."""
    labels = [name.replace("_", " ").title() for name in traits]
    figure = go.Figure(go.Bar(x=list(traits.values()), y=labels, orientation="h"))
    figure.update_layout(
        title="Conversation profile (heuristic)",
        xaxis=dict(range=[0, 1]),
        **LAYOUT,
    )
    return figure
