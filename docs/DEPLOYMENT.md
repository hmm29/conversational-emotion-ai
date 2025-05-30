# Deployment Guide: Conversational AI with Emotion Analysis

## 🚀 Quick Start

### Option 1: Local Development
1. Clone the repository
```bash
git clone https://github.com/hmm29/conversational-emotion-ai.git
cd conversational-emotion-ai
```

2. Set up environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
```
OPENAI_API_KEY=your-openai-key
HUME_API_KEY=your-hume-key
HUME_SECRET_KEY=your-hume-secret
```

4. Run the application
```bash
streamlit run app.py
```

### Option 2: Docker Deployment
1. Build and run with Docker Compose
```bash
docker-compose up -d
```

Or build manually:
```bash
docker build -t conversational-ai .
docker run -p 8501:8501 --env-file .env conversational-ai
```

## 🔧 Configuration

### Required Environment Variables
```bash
OPENAI_API_KEY=your-openai-key
HUME_API_KEY=your-hume-key
HUME_SECRET_KEY=your-hume-secret
```

### Optional Configuration
- Performance settings:
```bash
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200
```

- Security settings:
```bash
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

## ☁️ Cloud Deployment

### AWS Deployment (ECS Fargate)

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name conversational-ai
```

2. **Build and Push Image**
```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t conversational-ai .
docker tag conversational-ai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/conversational-ai:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/conversational-ai:latest
```

3. **Deploy with ECS**
```json
{
    "family": "conversational-ai",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "conversational-ai",
            "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/conversational-ai:latest",
            "portMappings": [
                {
                    "containerPort": 8501,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "OPENAI_API_KEY",
                    "value": "your-api-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/conversational-ai",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
```

### Google Cloud Deployment (Cloud Run)
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/conversational-ai
gcloud run deploy conversational-ai \
    --image gcr.io/PROJECT_ID/conversational-ai \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars OPENAI_API_KEY=your-key,HUME_API_KEY=your-key
```

### Azure Deployment (Container Instances)
```bash
az container create \
    --resource-group myResourceGroup \
    --name conversational-ai \
    --image yourusername/conversational-ai \
    --dns-name-label conversational-ai-unique \
    --ports 8501 \
    --environment-variables OPENAI_API_KEY=your-key HUME_API_KEY=your-key
```

## 🔒 Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables or secure key management services
- Rotate keys regularly
- Implement rate limiting

### Application Security
- Enable HTTPS in production
- Implement proper authentication if needed
- Sanitize all user inputs
- Enable security headers
- Regular security audits

### Infrastructure Security
- Use VPC and security groups
- Enable logging and monitoring
- Implement backup strategies
- Use least privilege access

## 📊 Monitoring & Logging

### Application Metrics
- Response times
- Error rates
- API usage
- User engagement metrics

### Infrastructure Metrics
- CPU and memory usage
- Network performance
- Storage utilization
- Container health

### Logging Setup
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_entry)

# Apply to your loggers
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify keys are correctly set
   - Check key permissions and quotas
   - Ensure proper environment variable format

2. **Performance Issues**
   - Monitor API response times
   - Implement caching for repeated requests
   - Scale horizontally if needed

3. **Memory Issues**
   - Monitor conversation history size
   - Implement data cleanup routines
   - Optimize model loading

### Debug Mode
```bash
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run app.py
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy Conversational AI

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          # Your deployment script here
          echo "Deploying to production..."
```
