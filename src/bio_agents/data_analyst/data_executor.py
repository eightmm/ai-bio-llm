"""
Code Executor Module
Stage 2: Generates and executes Python code for data analysis
"""

import sys
import io
import pandas as pd
import numpy as np
import logging
import traceback
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from src.bio_agents.config import Config
from .base_analyst import BaseAnalyst
from .data_planner import AnalysisPlan

logger = logging.getLogger(__name__)

class CodeExecutor(BaseAnalyst):
    """
    Stage 2: Code Executor
    Generates and executes Python code based on data and context
    """

    def __init__(self):
        """Initialize Code Executor"""
        # Code generation/execution model (override with MODEL_DATA_EXECUTOR)
        super().__init__(model=Config.MODEL_DATA_EXECUTOR)
        
        # Load consolidated prompts
        prompt_content = self._read_prompt_file("executor_prompts.md")
        self.prompts = self._split_prompts(prompt_content)

    def analyze_data(
        self,
        df: pd.DataFrame,
        file_info: Dict,
        problem_context: Dict,
        analysis_plan: Optional[AnalysisPlan] = None
    ) -> Dict:
        """
        Main method to analyze a specific data file/context
        """
        file_name = file_info.get('file_name', 'unknown')
        logger.info(f"Executor: Analyzing {file_name}...")

        # Prepare context
        column_info = self._format_column_info(file_info.get('columns', []))
        sample_data = str(file_info.get('sample_data', []))

        # 1. Generate Analysis Code
        prompt = self._create_analysis_prompt(
            file_info, column_info, sample_data, problem_context, analysis_plan
        )
        
        messages = [
            {"role": "system", "content": self.prompts['system']},
            {"role": "user", "content": prompt}
        ]

        code = self._generate_code(messages)
        
        if not code:
            return {"error": "Failed to generate code"}

        # 2. Execute Code (with Retry/Fix logic)
        result = self._execute_and_fix(code, df, file_info, column_info)
        
        return result

    def _create_analysis_prompt(
        self,
        file_info: Dict,
        column_info: str,
        sample_data: str,
        problem_context: Dict,
        analysis_plan: Optional['AnalysisPlan'] = None
    ) -> str:
        """Create prompt for analysis code generation"""
        sub_problem = problem_context.get('sub_problem', {})
        sub_problem_title = sub_problem.get('title', 'Data Analysis')
        sub_problem_description = sub_problem.get('description', '')
        
        file_name = file_info.get('file_name', 'unknown')
        total_rows = file_info.get('total_rows', 'unknown')
        columns = file_info.get('columns', [])

        # Build plan context if available
        plan_context = ""
        if analysis_plan:
            plan_context = f"""
Analysis Plan (from Planner stage):
- Problem Type: {analysis_plan.problem_type}
- Processing Strategy: {analysis_plan.processing_strategy}
- Focus Areas: {', '.join(analysis_plan.focus_areas)}
- Analysis Approach: {analysis_plan.analysis_approach}
- Code Flow: {'; '.join(analysis_plan.code_flow)}
"""

        return self.prompts['user'].format(
            sub_problem_title=sub_problem_title,
            plan_context=plan_context,
            sub_problem_description=sub_problem_description,
            file_name=file_name,
            total_rows=total_rows,
            columns=columns,
            column_info=column_info,
            sample_data=sample_data
        )

    def _generate_code(self, messages: List[Dict]) -> str:
        """Call LLM to generate code"""
        try:
            # Use lower temperature for code generation
            response = self._call_llm(messages, temperature=0.1)
            return self._extract_code(response)
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return ""

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown block"""
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].strip()
        return text.strip()

    def _execute_and_fix(
        self,
        code: str,
        df: pd.DataFrame,
        file_info: Dict,
        column_info: str,
        max_retries: int = 3
    ) -> Dict:
        """Execute code and attempt to fix errors using LLM"""
        
        for attempt in range(max_retries + 1):
            try:
                # Execute safely
                local_scope = self._execute_code_safely(code, df, file_info)
                
                # Check for 'result' variable
                if 'result' in local_scope:
                    return local_scope['result']
                else:
                    raise ValueError("Variable 'result' not found in executed code.")

            except Exception as e:
                logger.warning(f"Execution failed (Attempt {attempt+1}/{max_retries+1}): {e}")
                
                if attempt < max_retries:
                    logger.info("Requesting code fix from LLM...")
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    code = self._generate_fix_code(code, error_msg, file_info, column_info)
                    if not code:
                        break
                else:
                    logger.error("Max retries reached. Execution failed.")
                    return {"error": str(e), "code": code}
        
        return {"error": "Execution failed after retries"}

    def _generate_fix_code(
        self,
        previous_code: str,
        error_message: str,
        file_info: Dict,
        column_info: str
    ) -> str:
        """Generate fixed code based on error"""
        file_name = file_info.get('file_name', 'unknown')
        
        prompt = self.prompts['fix_user'].format(
            previous_code=previous_code,
            error_message=error_message,
            file_name=file_name,
            column_info=column_info
        )
        
        messages = [
            {"role": "system", "content": self.prompts['system']},
            {"role": "user", "content": prompt}
        ]

        try:
            # Low temp for fixes
            response = self._call_llm(messages, temperature=0.1)
            return self._extract_code(response)
        except Exception as e:
            logger.error(f"Fix code generation failed: {e}")
            return ""

    def _execute_code_safely(self, code: str, df: pd.DataFrame, file_info: Dict) -> Dict:
        """
        Execute code in a restricted namespace
        """
        # Define allowed modules
        file_path = file_info.get("file_path") or file_info.get("path") or ""
        file_name = file_info.get("file_name") or file_info.get("name") or ""

        allowed_scope = {
            "pd": pd,
            "np": np,
            "df": df,  # Inject dataframe
            "result": {},
            # Provide file metadata in case the generated code tries to reference the source file.
            # (Prefer using df directly, but this reduces avoidable FileNotFound errors.)
            "file_path": str(file_path),
            "file_name": str(file_name),
            "Path": Path,
        }
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # We use exec() here. In a production environment, this should be sandboxed (e.g., Docker)
            # For this local agent, we rely on the restricted globals/locals
            # IMPORTANT: use the same dict for globals/locals so that functions defined in the
            # executed code can still access injected variables like `df`.
            exec(code, allowed_scope, allowed_scope)
        finally:
            sys.stdout = old_stdout
            
        return allowed_scope

    def _format_column_info(self, columns: List[Dict]) -> str:
        """Format column info for prompt"""
        info = []
        for col in columns[:20]: # Limit to avoid token overflow
            info.append(f"- {col['name']} ({col['dtype']}): {col['non_null_count']} non-null, {col['unique_count']} unique")
            if 'sample_values' in col:
                info.append(f"  Samples: {col['sample_values']}")
        return "\n".join(info)
