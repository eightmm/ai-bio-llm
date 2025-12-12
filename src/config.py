import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Descrption: Central configuration for the AI Bio LLM project.
    
    # Common API Settings
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Client Settings
    TIMEOUT = 120
    MAX_RETRIES = 5
    RETRY_BACKOFF = 2
    
    # Model Configuration per Agent
    # You can override these via environment variables (e.g. MODEL_BRAIN=gpt-4)
    
    # Brain Agent: Decomposes problems
    # Defaulting to a high-reasoning model
    MODEL_BRAIN = os.getenv("MODEL_BRAIN", "openai/gpt-5.2-chat")
    
    # Search Agent: Searches and synthesizes literature
    MODEL_SEARCH = os.getenv("MODEL_SEARCH", "perplexity/sonar-deep-research")
    
    # Blue Agent: Writes initial reports
    MODEL_BLUE = os.getenv("MODEL_BLUE", "openai/gpt-5.2-chat")
    
    # BlueX Agent: Revises reports based on feedback
    MODEL_BLUEX = os.getenv("MODEL_BLUEX", "openai/gpt-5.2-chat")
    
    # Red Agent: Critiques reports
    MODEL_RED = os.getenv("MODEL_RED", "google/gemini-3-pro-preview")
