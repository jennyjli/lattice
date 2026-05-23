import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Preferred LLM provider (options: 'openai', 'anthropic', 'gemini')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')

# Model selection
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4')

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Frontend Configuration
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
