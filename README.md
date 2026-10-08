# Conversational Emotion AI

[![tests](https://github.com/hmm29/conversational-emotion-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/hmm29/conversational-emotion-ai/actions/workflows/ci.yml)

A Streamlit chatbot that reads the emotional tone of each message and adapts how it replies. Emotion scores come from Hume AI's language model, replies come from an OpenAI chat model, and the detected emotion decides which of four response approaches the model is prompted with.

It grew out of my Yale thesis work on human-computer interaction. It is a prototype for exploring emotion-aware conversation design, not a deployed product and not a mental-health tool.

## What happens on each message

1. **Analyze.** The text goes to Hume AI's Expression Measurement streaming API over a WebSocket. Scores are averaged across the returned predictions and the strongest emotion becomes the dominant one.
2. **Choose an approach.** The dominant emotion maps to one of four approaches: amplify positive, gentle encouragement, empathetic support, or balanced engagement. The mapping lives in [`config/emotions_config.yaml`](config/emotions_config.yaml).
3. **Reply.** The approach sets the system prompt and temperature for an OpenAI chat completion. The prompt also carries the detected emotion and the trend over the last five messages.
4. **Show.** The app displays the reply, a radar chart of the message's emotions, a timeline across the conversation, the approaches used so far, and a simple heuristic profile of the conversation.

The conversation can be downloaded as JSON.

## Runs without keys

Both API keys are optional, so you can try it immediately:

| Missing key | What the app uses instead |
|---|---|
| `HUME_API_KEY` | A keyword matcher covering nine emotions |
| `OPENAI_API_KEY` | One canned reply per approach |

The same stand-ins take over for a single message if a Hume or OpenAI call fails, and the app labels those messages.

## Run it

Python 3.10 or newer.

```bash
git clone https://github.com/hmm29/conversational-emotion-ai.git
cd conversational-emotion-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # optional: add your keys
streamlit run app.py
```

Or with Docker, after creating `.env`:

```bash
docker compose up --build
```

Then open `http://localhost:8501`.

## Layout

```
app.py                       Streamlit interface
src/
  emotion_analyzer.py        Hume client, keyword matcher, emotion history
  response_generator.py      approach selection, prompts, OpenAI call
  conversation_manager.py    turns, trend, profile, JSON export
  visualization.py           Plotly charts
config/emotions_config.yaml  emotion-to-approach mapping
tests/                       unit tests and a headless run of the app
```

More detail in [docs/architecture.md](docs/architecture.md).

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The tests run offline. They cover the keyword matcher, parsing of Hume responses, fallback behavior, approach selection, prompt construction, conversation state, the charts, and a headless run of the Streamlit app that sends a message. The WebSocket client is exercised against a local server that answers in Hume's documented response shape. No test calls Hume or OpenAI.

## Limitations

- Emotion scores describe the language of a message, not what a person actually feels.
- The emotion-to-approach mapping and the 0.1 minimum score are starting points. They have not been calibrated or evaluated against labeled conversations.
- The conversation profile is a set of simple running heuristics, not a personality assessment.
- State lives in the browser session. There are no accounts, no database and no authentication.
- Each message opens a new WebSocket to Hume, which adds connection time to every reply.

## License

MIT
