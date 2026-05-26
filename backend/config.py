import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
if OPENAI_API_KEY == 'sk_test_placeholder':
    OPENAI_API_KEY = ''

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_TEXT_MODEL = os.getenv('GEMINI_TEXT_MODEL', 'models/gemini-pro')
GEMINI_IMAGE_MODEL = os.getenv('GEMINI_IMAGE_MODEL', 'models/gemini-pro-vision')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Preferred LLM provider (options: 'openai', 'anthropic', 'gemini')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()
if LLM_PROVIDER not in {'openai', 'anthropic', 'gemini'}:
    LLM_PROVIDER = 'openai'

# Model selection
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4')

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Frontend Configuration
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Image Generation Configuration
ENABLE_IMAGE_GENERATION = os.getenv('ENABLE_IMAGE_GENERATION', 'True').lower() == 'true'
IMAGE_GEN_PROVIDER = os.getenv('IMAGE_GEN_PROVIDER', 'gemini')  # 'gemini' or 'openai'
IMAGE_SIZE = os.getenv('IMAGE_SIZE', '512x512')
