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
        system_prompt = """
        You are an expert Biological Problem Solver and Architect.
        Your goal is to take a complex, raw biological problem description and DECOMPOSE it into a structured hierarchy: a Main Problem Definition and several Sub-problems.

        ### Instructions:
        1.  **Define the Main Problem**: Synthesize the input into a clear, high-level problem statement (Main Problem).
        2.  **Decompose**: Break the problem down into logical, sequential, or parallel sub-problems.
        3.  **Structure & IDs**: 
            - Carefully analyze the input text for existing structure markers like (A), (B), 1, 2, etc.
            - **Use these markers as the `id`** for the sub-problems (e.g., "A", "B", "A-1").
            - If the text implies a hierarchy (e.g., A -> 1, 2), create combined IDs like "A-1", "A-2".
            - If no markers exist, use logical sequential IDs (e.g., "Step-1", "Step-2").
        4.  **Problem ID**:
            - Generate a short, descriptive **English** identifier for the problem in **snake_case** (e.g., "lung_fibrosis_target", "t_cell_similarity").
            - This will be used as the directory name.
        5.  **Data Usage (DB_flag & DB_list)**:
            - Analyze if the sub-problem requires specific data files or databases mentioned in the input text (e.g., "genelist.csv", "TPM expression file", "Q1 features").
            - **DB_flag**: Set to **1** if data/files are required, **0** otherwise.
            - **DB_list**: List the specific names of the files/data required (comma-separated). If none, use empty string "".
        5.  **Detail**: For each sub-problem, provide:
            - A concise **Title**.
            - A detailed **Description**.
            - A **Suggested Approach**.
        6.  **Language**: All output MUST be in **Korean**.

        ### Output Format:
        You must output a valid JSON object matching the schema.
        Note: You do NOT need to include 'original_problem_text' in your JSON output; the system will add it.
        
        {
            "problem_id": "t_cell_analysis",
            "main_problem_definition": "Clear definition of the overarching problem (Korean)",
            "sub_problems": [
                {
                    "id": "A",
                    "title": "Sub-problem Title (Korean)",
                    "description": "Detailed description (Korean)",
                    "suggested_approach": "How to solve this part (Korean)",
                    "DB_flag": 1,
                    "DB_list": "genelist.csv, Q1 features"
                },
                ...
            ]
        }
        
        Do not include markdown formatting (like ```json) in your response, just the raw JSON string.
        """

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

# ==========================================
# Main Execution Block (for testing)
# ==========================================
# ==========================================
# Main Execution Block (for testing/CLI)
# ==========================================
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Bio LLM Brain Agent - Problem Decomposition")
    parser.add_argument("input_file", nargs="?", help="Path to the text file containing the biological problem")
    args = parser.parse_args()

    agent = BrainAgent()
    
    problem_text = ""
    
    if args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                problem_text = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.input_file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        # Default test problem if no file provided
        print("No input file provided. Using default test problem...")
        problem_text = """
        [예시 문제1] T 세포 유전자 간 기능 유사성 정량화
        T 세포에서는 항원 인식, 활성화, 분화 등 다양한 기능을 수행하는 유전자들이 네트워크 형태로 작동한다. 일반적으로 기능적으로 유사한 유전자쌍은
        •	발현 패턴(expr_corr)이 비슷하거나,
        •	단백질 구조(struct_sim)가 유사하거나,
        •	진화적 계통(phylo_sim)이 가깝다는 특징을 가진다.
        문제의 목표는 발현 데이터(features)와 유전자 이름(genelist.csv, ENSMUSG+gene name)을 통합하여 유전자간 유사성 점수(Function Similarity Score)를 구축하고 이를 기준으로 유전자군을 정의하는 것이다.

        입력 데이터: Q1 features 파일 
        TPM expression 파일 포함
        genelist 포함
        CD4 T, CD8 T 세포 포함
        휴지 T 세포: naive, memory T 세포
        활성 T 세포: TH0, TH1, TH2, TH17, TREG, 0.5/1/2/4h 등


        위에 입력된 데이터를 기반으로 아래 요구 사항을 충족하는 분석 전략을 제시하라.
        (1) LLM 기반 유전자 기능 요약 생성
        (2) LLM 기반 phylogenic tree (knowledge-based) 생성
        (3) Expression 기반 유사성 점수 생성
        (4) (1,2,3) 을 통합한 Similarity Score에 따라 휴지기 T 세포 (naive or memory T 세포)조절에 주요한 유전자쌍을 제시하고, 근거와 생물학적 기능(없을시 생략 가능)을 제시하라. 
        (5) 휴지기 T 세포 내 상위 발현 300개 gene을 대상으로 공개된 단백질, 도메인 정보를 활용하여 단백질 구조 유사도 점수를 생성하고 휴지기 조절에 중요한 유전자 쌍을 예측하라.
        """
    
    try:
        print("Running analysis...")
        result = agent.analyze_question(problem_text)
        
        print(f"\n=== Main Problem ({result.problem_id}) ===\n{result.main_problem_definition}")
        
        # Create directory based on problem_id
        base_dir = "problems"
        output_dir = os.path.join(base_dir, result.problem_id)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n=== Saving Sub-problem Files to '{output_dir}' ===")
        
        for sub in result.sub_problems:
            # Create a dictionary for the individual file
            sub_problem_data = {
                "original_problem_text": result.original_problem_text,
                "problem_id": result.problem_id,
                "main_problem_definition": result.main_problem_definition,
                "sub_problem": sub.model_dump()
            }
            
            # Sanitize filename
            safe_id = sub.id.replace("/", "_").replace("\\", "_")
            filename = os.path.join(output_dir, f"sub_problem_{safe_id}.json")
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(sub_problem_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved: {filename} ([{sub.id}] {sub.title})")
            
    except Exception as e:
        print(f"Analysis failed: {e}")
