from pathlib import Path
import json
import time
import argparse
from typing import Optional

from openai import OpenAI

MAX_RETRIES = 5
RETRY_BACKOFF = 2
READ_TIMEOUT = 120


class SearchAgent:

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-oss-20b:free",
    ):
        if not api_key:
            raise ValueError("api_key must be provided.")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model

        # 클라이언트 생성
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=READ_TIMEOUT,
        )


    def _build_user_prompt(
        self,
        brain_data: dict,
        system_template: str,
        user_template: str,
    ) -> tuple[str, str]:

        user_prompt = user_template

        user_prompt = user_prompt.replace(
            "{original_problem_text}",
            brain_data.get("original_problem_text", "")
        )
        user_prompt = user_prompt.replace(
            "{main_problem_definition}",
            brain_data.get("main_problem_definition", "")
        )

        sub_problem = brain_data.get("sub_problem", {})
        user_prompt = user_prompt.replace(
            "{sub_problem.description}",
            sub_problem.get("description", "")
        )
        user_prompt = user_prompt.replace(
            "{sub_problem.suggested_approach}",
            sub_problem.get("suggested_approach", "")
        )

        return system_template, user_prompt


    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:

        last_err: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
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
                wait = RETRY_BACKOFF ** (attempt - 1)
                print(f"[LLM] Error: {e}. Retrying in {wait} sec...", flush=True)
                time.sleep(wait)

        raise last_err

    def run_for_sub_problem(
        self,
        sub_problem_path: Path | str,
        system_path: Path | str,
        user_template_path: Path | str,
        output_dir: Path | str = ".",
    ) -> None:

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        sub_problem_path = Path(sub_problem_path)
        system_path = Path(system_path)
        user_template_path = Path(user_template_path)

        # 입력 파일 읽기
        with sub_problem_path.open("r", encoding="utf-8") as f:
            brain_data = json.load(f)

        with system_path.open("r", encoding="utf-8") as f:
            system_prompt = f.read()

        with user_template_path.open("r", encoding="utf-8") as f:
            user_template = f.read()

        # 프롬프트 구성
        system_prompt, user_prompt = self._build_user_prompt(
            brain_data, system_prompt, user_template
        )

        sub_id = brain_data.get("sub_problem", {}).get("id", "1")
        safe_id = str(sub_id).replace("/", "_").replace("\\", "_")

        user_prompt_file = output_dir / f"user_prompt_{safe_id}.txt"
        results_file = output_dir / f"results_{safe_id}.txt"

        with user_prompt_file.open("w", encoding="utf-8") as f:
            f.write(user_prompt)

        print(f"[IO] User prompt saved at: {user_prompt_file}")

        results = self._call_llm(system_prompt, user_prompt)

        with results_file.open("w", encoding="utf-8") as f:
            f.write(results)

        print(f"[IO] Results saved at: {results_file}")
        print("\n=== LLM Response ===\n")
        print(results)


if __name__ == "__main__":
    
    project_dir = Path("../..")
    src_dir = project_dir / "src"
    

    agent = SearchAgent(
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-oss-20b:free"
    )

    agent.run_for_sub_problem(
        sub_problem_path= project_dir / "problems" / "chunked" / "01_t_cell_gene_functional_similarity" / "sub_problem_1.json",
        system_path= src_dir / "search" / "search_system.txt",
        user_template_path= src_dir / "search" / "search_user_template.txt",
        output_dir= project_dir / "outputs" / "search",
    )
