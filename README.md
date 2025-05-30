# Conversational Emotion AI

An intelligent chatbot that analyzes emotional tone in real-time and adapts its responses based on detected emotions, combining psychology principles with advanced AI capabilities.

## Features

- Real-time emotion analysis of user input
- Emotion-aware response generation
- Conversation history and emotion tracking
- Interactive web interface
- Integration with Hume AI for emotion detection
- Powered by OpenAI's language models

## 📋 Day 3 Deliverables

- [x] Advanced real-time emotion visualization dashboard
- [x] Enhanced UI/UX with professional styling and animations
- [x] Conversation export and sharing functionality
- [x] Performance monitoring and optimization
- [x] Research mode for experimentation
- [x] Comprehensive testing framework

## 🚀 Advanced Features

### Real-time Emotion Dashboard
- **Interactive Radar Charts**: Live emotion state visualization
- **Emotion Timeline**: Track emotional journey throughout conversation
- **Personality Spider Charts**: Dynamic personality trait analysis
- **Emotion Heatmaps**: Intensity visualization over time

### Professional UI/UX
- **Gradient Designs**: Modern, professional interface
- **Smooth Animations**: Enhanced user experience with CSS animations
- **Status Indicators**: Real-time system status monitoring
- **Responsive Layout**: Optimized for different screen sizes

### Research & Experimentation
- **A/B Testing Framework**: Compare different AI configurations
- **Performance Analytics**: Monitor system performance and response times
- **Export Functionality**: Download conversation data for analysis
- **Settings Optimization**: Fine-tune AI behavior for specific use cases

## 🔧 Technical Excellence

- **Async Architecture**: Non-blocking operations for optimal performance
- **Comprehensive Testing**: Unit tests, integration tests, and performance tests
- **Error Handling**: Robust error recovery and fallback systems
- **Monitoring**: Real-time performance tracking and analytics
- **Scalability**: Designed for production deployment

## 📊 Analytics & Insights

The system provides comprehensive analytics including:
- Emotion distribution analysis
- Response strategy effectiveness
- Conversation engagement metrics
- Personality trait evolution
- Performance benchmarks

## 🧠 Advanced Features

### Emotion-Aware Response Generation
- **Adaptive Prompting**: System prompts change based on detected emotional state
- **Context Preservation**: Maintains emotional context across conversation
- **Strategy Selection**: Different response approaches for different emotional needs

### Personality Tracking
- **Dynamic Profiling**: Learns user personality traits over time
- **Confidence Scoring**: Tracks reliability of personality assessments
- **Conversation Adaptation**: Tailors responses to individual personality

### Analytics Dashboard
- **Real-time Metrics**: Emotion distribution, response strategies, engagement
- **Trend Analysis**: Emotional patterns over conversation
- **Session Insights**: Comprehensive conversation analytics

## Strategic Value

This project demonstrates:

- **Multimodal AI Integration**: Combining text analysis with emotion detection to create more empathetic interactions
- **Real-time Processing**: Live emotion analysis and response generation for natural, fluid conversations
- **Human-Centered Design**: Psychology-informed conversation strategies that adapt to user emotions
- **Production-Ready Code**: Comprehensive error handling, fallback mechanisms, and robust testing
- **Scalable Architecture**: Modular design that allows for easy extension and maintenance
- **Data-Driven Insights**: Detailed emotion tracking and visualization for understanding conversation patterns

## Project Structure

```
conversational-emotion-ai/
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── src/                     # Source code
│   ├── __init__.py
│   ├── emotion_analyzer.py  # Emotion analysis logic
│   ├── conversation_manager.py  # Conversation handling
│   ├── response_generator.py    # Response generation
│   ├── visualization.py        # Real-time visualization components
│   ├── performance.py         # Performance monitoring
│   └── utils.py                # Utility functions
├── app.py                   # Main Streamlit application
├── config/
│   └── emotions_config.yaml  # Emotion configuration
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_emotion_analyzer.py
│   ├── test_conversation_manager.py
│   └── test_integration_full.py  # Comprehensive integration tests
├── data/                    # Data storage
│   └── conversation_history/
└── docs/                    # Documentation
    └── architecture.md
```

```
conversational-emotion-ai/
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── src/                     # Source code
│   ├── __init__.py
│   ├── emotion_analyzer.py  # Emotion analysis logic
│   ├── conversation_manager.py  # Conversation handling
│   ├── response_generator.py    # Response generation
│   └── utils.py                # Utility functions
├── app.py                   # Main Streamlit application
├── config/
│   └── emotions_config.yaml  # Emotion configuration
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_emotion_analyzer.py
│   └── test_conversation_manager.py
├── data/                    # Data storage
│   └── conversation_history/
└── docs/                    # Documentation
    └── architecture.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- API keys for OpenAI and Hume AI

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/conversational-emotion-ai.git
   cd conversational-emotion-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys to `.env`
   - Required API keys:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `HUME_API_KEY`: Your Hume AI API key
     - `HUME_SECRET_KEY`: Your Hume AI secret key

## Usage

### Development

```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with auto-reload
streamlit run app.py
```

### Production

```bash
# Using Docker
docker-compose up -d

# Or directly with Python
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Access the application at `http://localhost:8501`

## Configuration

Edit `config/emotions_config.yaml` to customize:
- Emotion detection thresholds
- Response strategies
- Model parameters

## Testing

Run the test suite:
```bash
pytest
```

Generate coverage report:
```bash
pytest --cov=src --cov-report=html
```

## Development

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Hume AI for emotion analysis
- OpenAI for language models
- Streamlit for the web interface
