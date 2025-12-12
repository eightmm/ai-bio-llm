import os
import json
import time
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI

# Load environment variables
load_dotenv()

# ==========================================
# Data Models
# ==========================================

class SubProblem(BaseModel):
    id: str = Field(..., description="Unique ID for the sub-problem (e.g., SUB_01)")
    title: str = Field(..., description="Concise title of the sub-problem (Korean)")
    description: str = Field(..., description="Detailed description of what this sub-problem entails (Korean)")
    suggested_approach: str = Field(..., description="High-level approach to solve this specific sub-problem (Korean)")
    DB_flag: int = Field(..., description="1 if specific data/files mentioned in the problem are required, 0 otherwise")
    DB_list: str = Field(..., description="Comma-separated list of data/file names required (e.g., 'genelist.csv, features.txt'), or empty string if None")

class ProblemDecompositionResponse(BaseModel):
    original_problem_text: str = Field(..., description="The original raw input text")
    problem_id: str = Field(..., description="A short, English, snake_case identifier for the problem (e.g., 't_cell_analysis'), used for directory naming")
    main_problem_definition: str = Field(..., description="A clear definition of the overarching main problem (Korean)")
    sub_problems: List[SubProblem] = Field(..., description="List of decomposed sub-problems")

# ==========================================
# Brain Agent Logic
# ==========================================

MAX_RETRIES = 5
RETRY_BACKOFF = 2
READ_TIMEOUT = 120

class BrainAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-3-pro-preview")
        self.client = self._create_client()

    def _create_client(self) -> OpenAI:
        if not self.api_key:
            # You might want to handle this more gracefully or assume it's set
            print("Warning: OPENROUTER_API_KEY is missing in environment variables.")
        
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=READ_TIMEOUT,
        )

    def analyze_question(self, question: str) -> ProblemDecompositionResponse:
        """
        Analyzes the raw biological question and returns a structured decomposition.
        """
        # Load system prompt from file
        prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            # Fallback (Safety)
            print("Warning: system_prompt.md not found. Using minimal fallback.")
            system_prompt = "You are a biological problem solver. Decompose the problem into JSON."

        last_err = None

        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"[LLM] request attempt={attempt} model={self.model}", flush=True)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Decompose this biological problem:\n\n{question}"}
                    ],
                    response_format={"type": "json_object"},
                    timeout=READ_TIMEOUT
                )
                
                content = response.choices[0].message.content
                print("[LLM] response OK", flush=True)
                data = json.loads(content)
                
                # Inject the original question into the response object
                data['original_problem_text'] = question
                
                return ProblemDecompositionResponse(**data)
                
            except Exception as e:
                last_err = e
                print(f"[LLM] error: {type(e).__name__}: {e}", flush=True)
                sleep_time = RETRY_BACKOFF ** (attempt - 1)
                print(f"Sleeping for {sleep_time} seconds...", flush=True)
                time.sleep(sleep_time)
        
        raise last_err


