import json
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

from src.bio_agents.config import Config


class AnswerAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or Config.API_KEY
        if not self.api_key:
            raise ValueError("api_key must be provided or set in OPENROUTER_API_KEY environment variable.")

        self.base_url = base_url or Config.BASE_URL
        self.model = model or Config.MODEL_ANSWER

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=Config.TIMEOUT,
        )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        last_err: Optional[Exception] = None

        for attempt in range(1, Config.MAX_RETRIES + 1):
            try:
                print(f"[LLM] Request attempt={attempt}, model={self.model}", flush=True)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                print("[LLM] Response received", flush=True)
                return response.choices[0].message.content
            except Exception as e:
                last_err = e
                wait = Config.RETRY_BACKOFF ** (attempt - 1)
                print(f"[LLM] Error: {e}. Retrying in {wait} sec...", flush=True)
                time.sleep(wait)

        raise last_err

    def run_for_problem(
        self,
        brain_path: Path | str,
        system_path: Path | str,
        user_template_path: Path | str,
        search_output_path: Path | str,
        completed_answer_path: Path | str,
        red_review_path: Path | str,
        output_dir: Path | str = ".",
    ) -> None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        brain_path = Path(brain_path)
        system_path = Path(system_path)
        user_template_path = Path(user_template_path)
        search_output_path = Path(search_output_path)
        completed_answer_path = Path(completed_answer_path)
        red_review_path = Path(red_review_path)

        with brain_path.open("r", encoding="utf-8") as f:
            brain_data = json.load(f)

        with system_path.open("r", encoding="utf-8") as f:
            system_prompt = f.read()

        with user_template_path.open("r", encoding="utf-8") as f:
            user_template = f.read()

        with search_output_path.open("r", encoding="utf-8") as f:
            search_output = f.read()

        with completed_answer_path.open("r", encoding="utf-8") as f:
            completed_answer = f.read()

        with red_review_path.open("r", encoding="utf-8") as f:
            red_review = f.read()

        user_prompt = user_template
        user_prompt = user_prompt.replace("{original_problem_text}", brain_data.get("original_problem_text", ""))
        user_prompt = user_prompt.replace("{SEARCH_REPORT}", search_output)
        user_prompt = user_prompt.replace("{COMPLETED_ANSWER}", completed_answer)
        user_prompt = user_prompt.replace("{RED_REVIEW}", red_review)

        (output_dir / "system_prompt.md").write_text(system_prompt, encoding="utf-8")
        (output_dir / "user_prompt.txt").write_text(user_prompt, encoding="utf-8")

        results = self._call_llm(system_prompt, user_prompt)

        (output_dir / "output.txt").write_text(results, encoding="utf-8")


