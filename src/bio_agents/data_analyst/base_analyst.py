from pathlib import Path
from typing import Dict, Optional, Any
import requests
import logging
import json

from src.bio_agents.config import Config

logger = logging.getLogger(__name__)

class BaseAnalyst:
    """
    Base class for Data Analyst LLM modules.
    Handles common LLM API interactions and prompt loading.
    """
    def __init__(self, model: str = Config.MODEL_BRAIN, timeout: int = Config.TIMEOUT):
        self.model = model
        self.timeout = timeout
        
    def _call_llm(self, messages: list[Dict[str, str]], temperature: float = 0.2) -> str:
        """
        Call OpenRouter LLM API with standard error handling.
        
        Args:
            messages: List of message dicts [{'role': 'system', 'content': '...'}, ...]
            temperature: Sampling temperature
            
        Returns:
            LLM response content string
        """
        url = f"{Config.BASE_URL}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        # Add max_tokens if explicitly needed, but default is usually fine for these models
        # unless strict output control is required. 

        headers = {
            "Authorization": f"Bearer {Config.API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/bioinformatics-llm",
            "X-Title": "LLM DB Analyst"
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM API HTTP Error: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM API Error: {str(e)}")
            raise

    def _read_prompt_file(self, filename: str) -> str:
        """Read a prompt file from the prompts directory relative to this file."""
        # Note: This assumes this file is in src/bio_agents/data_analyst/
        # and prompts are in src/bio_agents/data_analyst/prompts/
        prompt_path = Path(__file__).parent / "prompts" / filename
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _split_prompts(self, content: str) -> Dict[str, str]:
        """
        Split a consolidated prompt file into sections.
        Format expectation:
        
        # SYSTEM
        ... system prompt content ...
        
        # USER
        ... user prompt content ...
        """
        parts = {}
        current_section = None
        current_content = []
        
        for line in content.splitlines():
            if line.strip().startswith("# SYSTEM"):
                if current_section:
                    parts[current_section] = "\n".join(current_content).strip()
                current_section = "system"
                current_content = []
            elif line.strip().startswith("# USER"):
                if current_section:
                    parts[current_section] = "\n".join(current_content).strip()
                current_section = "user"
                current_content = []
            elif line.strip().startswith("# FIX_USER"): # For fix code specific
                if current_section:
                    parts[current_section] = "\n".join(current_content).strip()
                current_section = "fix_user"
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        if current_section:
            parts[current_section] = "\n".join(current_content).strip()
            
        return parts
