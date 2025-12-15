import os
import json
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import sys
from pathlib import Path

# Add project root to sys.path
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from src.bio_agents.config import Config
from openai import OpenAI

class BlueXAgent:
    
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
        self.model = model or Config.MODEL_BLUEX

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=Config.TIMEOUT,
        )


    def _build_user_prompt(
        self,
        brain_data: dict,
        full_report: str,
        data_analysis_results: str,
        red_report: str,
        system_template: str,
        user_template: str,
    ) -> tuple[str, str]:

        user_prompt = user_template

        # Replace placeholders exactly as in original code
        user_prompt = user_prompt.replace(
            "{RAW_QUESTION}",
            brain_data.get("original_problem_text", "")
        )

        user_prompt = user_prompt.replace(
            "{COMPLETED_REPORT}",
            full_report
        )
        
        user_prompt = user_prompt.replace(
            "{RED_TEAM_FEEDBACK}",
            red_report
        )
        
        user_prompt = user_prompt.replace(
            "{DATA_ANALYSIS_RESULTS}",
            data_analysis_results
        )

        return system_template, user_prompt

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
        full_report_path: Path | str,
        red_report_path: Path | str,
        data_analysis_results_path: Path | str,
        output_dir: Path | str = ".",
    ) -> None:

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        brain_path = Path(brain_path)
        system_path = Path(system_path)
        user_template_path = Path(user_template_path)
        red_report_path = Path(red_report_path)
        full_report_path = Path(full_report_path)
        data_analysis_results_path = Path(data_analysis_results_path)


        with brain_path.open("r", encoding="utf-8") as f:
            brain_data = json.load(f)

        with system_path.open("r", encoding="utf-8") as f:
            system_prompt = f.read()

        with user_template_path.open("r", encoding="utf-8") as f:
            user_template = f.read()

        with full_report_path.open("r", encoding="utf-8") as f:
            full_report = f.read()
            
        with red_report_path.open("r", encoding="utf-8") as f:
            red_report = f.read()

        with data_analysis_results_path.open("r", encoding="utf-8") as f:
            data_analysis_results = f.read()

        system_prompt, user_prompt = self._build_user_prompt(
            brain_data=brain_data,
            full_report=full_report,
            data_analysis_results=data_analysis_results,
            red_report=red_report,
            system_template=system_prompt,
            user_template=user_template,
        )

        user_prompt_file = output_dir / f"user_prompt.txt"
        output_file = output_dir / "output.txt"
        system_prompt_file = output_dir / "system_prompt.md"

        with system_prompt_file.open("w", encoding="utf-8") as f:
            f.write(system_prompt)


        with user_prompt_file.open("w", encoding="utf-8") as f:
            f.write(user_prompt)
        print(f"[IO] User prompt saved at: {user_prompt_file}")

        # Call LLM
        results = self._call_llm(system_prompt, user_prompt)

        # Standardized output
        with output_file.open("w", encoding="utf-8") as f:
            f.write(results)

        print(f"[IO] Summarized results saved at: {output_file}")

        print("\n=== LLM Response ===\n")
        print(results)



if __name__ == "__main__":
    
    project_dir = Path("../..")
    src_dir = project_dir / "src"
    
    agent = BlueXAgent()

    agent.run_for_sub_problem(
        sub_problem_path= project_dir / "problems" / "chunked" / "01_t_cell_gene_functional_similarity" / "sub_problem_1.json",
        system_path= src_dir / "blue" / "bluex_system.md",
        user_template_path= src_dir / "blue" / "bluex_user_template.md",
        full_report_path= project_dir / "outputs" / "search" / "results_1.txt",
        red_report_path= project_dir / "outputs" / "red" / "red_results_1.txt",
        data_analysis_results_path= project_dir / "outputs" / "data_analizer" / "data_analysis_results_example.txt",
        output_dir= project_dir / "outputs" / "blueX",
    )
