# Backend Configuration

Set your API keys and preferences in a `.env` file:

```bash
# LLM Configuration
LLM_PROVIDER=openai  # Options: openai, anthropic, gemini
MODEL_NAME=gpt-4
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Image Generation
ENABLE_IMAGE_GENERATION=True
IMAGE_GEN_PROVIDER=gemini  # Options: gemini, openai
IMAGE_SIZE=512x512

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
```

## Running the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`
Docs: `http://localhost:8000/docs`
