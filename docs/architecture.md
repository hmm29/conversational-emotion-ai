# Architecture

This document describes what the code does today.

## Flow

```
app.py (Streamlit)
  │  user message
  ▼
ConversationManager.process_message
  ├─ analyzer.analyze_emotion        → EmotionResult
  │     HumeEmotionAnalyzer            WebSocket to Hume's streaming API
  │     └─ on any failure: keyword_emotions
  │     KeywordEmotionAnalyzer         used when no Hume key is set
  ├─ EmotionHistory.get_emotion_trend  average of the last five results
  ├─ generator.generate_response     → GeneratedResponse
  │     choose_approach                dominant emotion → approach
  │     build_system_prompt            approach + emotion + trend
  │     OpenAI chat completion
  │     └─ on any failure, or no key: canned reply for the approach
  ├─ PersonalityProfile.update
  └─ append ConversationTurn
```

## Components

| Component | File | Notes |
|---|---|---|
| Hume client | `src/emotion_analyzer.py` | Sends `{"models": {"language": {}}, "raw_text": true, "data": text}` to `wss://api.hume.ai/v0/stream/models`, authenticated with the `X-Hume-Api-Key` header. Text is cut to Hume's 10,000-character limit. Scores are averaged over the returned predictions. |
| Keyword matcher | `src/emotion_analyzer.py` | Whole-word matches against nine short keyword lists, 0.3 per match, capped at 1.0. No matches means "neutral". |
| Approach selection | `src/response_generator.py` | Looks the dominant emotion up in `config/emotions_config.yaml`. Unlisted emotions and scores under 0.1 get balanced engagement. |
| Prompts | `src/response_generator.py` | One base prompt, one paragraph per approach, plus the detected emotion and trend. The last six turns are sent as history. |
| Conversation state | `src/conversation_manager.py` | Turns, a ten-result emotion history, approach counts, summary and JSON export. |
| Profile | `src/conversation_manager.py` | Four values between 0 and 1, nudged by simple rules (emotion strength, amusement, negative emotion, message length). |
| Charts | `src/visualization.py` | Functions that take data and return Plotly figures. |

## Design choices

- **Dependencies passed in.** The analyzer takes its connect function and the generator takes its client, so tests replace Hume and OpenAI with in-memory fakes.
- **Degrade, don't stall.** A failed external call falls back for that one message and is labeled in the interface.
- **Synchronous code.** One message is processed at a time per browser session, so plain blocking calls are simpler than an event loop inside Streamlit.
- **Charts separate from Streamlit.** The figure builders can be tested without a running app.

## Not built

- Evaluation of whether the adapted replies are better than unadapted ones
- Calibrated thresholds per emotion
- Persistent storage, accounts or authentication
- Voice or facial expression input
