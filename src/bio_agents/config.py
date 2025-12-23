import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Description: Central configuration for the AI Bio LLM project.
    
    # Common API Settings
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Client Settings
    TIMEOUT = 120
    MAX_RETRIES = 5
    RETRY_BACKOFF = 2
    
    # Data Settings
    DATA_DIR = os.getenv("DATA_DIR", "problems")

    # Model Configuration per Agent
    # You can override any of these via environment variables.
    # Examples:
    #   MODEL_BRAIN=google/gemini-2.5-flash
    #   MODEL_SEARCH=google/gemini-2.5-flash
    #   MODEL_ANSWER=google/gemini-2.5-flash
    
    # Brain Agent: Decomposes problems
    # Defaulting to a high-reasoning model
    MODEL_DB = "anthropic/claude-3.5-sonnet"

    MODEL_BRAIN = os.getenv("MODEL_BRAIN", "openai/gpt-5.2-pro")
    
    # Search Agent: Searches and synthesizes literature
    MODEL_SEARCH = os.getenv("MODEL_SEARCH", "perplexity/sonar-deep-research")
    
    # Blue Agent: Writes initial reports
    MODEL_BLUE = os.getenv("MODEL_BLUE", "openai/gpt-5.2-pro")
    
    # BlueX Agent: Revises reports based on feedback
    MODEL_BLUEX = os.getenv("MODEL_BLUEX", "openai/gpt-5.2-pro")
    
    # Red Agent: Critiques reports
    MODEL_RED = os.getenv("MODEL_RED", "anthropic/claude-opus-4.5")

    # Answer Agent: Composes final deliverable (answer + red review + references when available)
    # Defaults to the same model as BlueX unless overridden.
    MODEL_ANSWER = os.getenv("MODEL_ANSWER", MODEL_BLUEX)

    # Data Analyst Agent (3-stage LLM pipeline)
    # Defaults fall back to MODEL_BRAIN unless overridden.
    MODEL_DATA_PLANNER = os.getenv("MODEL_DATA_PLANNER", MODEL_DB)
    MODEL_DATA_EXECUTOR = os.getenv("MODEL_DATA_EXECUTOR", MODEL_DB)
    MODEL_DATA_SUMMARIZER = os.getenv("MODEL_DATA_SUMMARIZER", MODEL_DB)

    # Temperature Settings
    # Default temperature for general agents (used when --temperature is not specified)
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

    # Red Agent specific temperature (independent from other agents)
    RED_TEMPERATURE = float(os.getenv("RED_TEMPERATURE", "0.3"))
