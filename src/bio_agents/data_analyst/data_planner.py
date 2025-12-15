"""
Planner LLM Module
Stage 1: Generates high-level execution plan based on problem and file list
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

from src.bio_agents.config import Config
from .base_analyst import BaseAnalyst

logger = logging.getLogger(__name__)

class AnalysisPlan:
    """Structure for Analysis Plan"""
    def __init__(self, plan_dict: Dict):
        self.processing_strategy = plan_dict.get('processing_strategy', 'sequential')
        self.file_priority = plan_dict.get('file_priority', [])
        self.analysis_approach = plan_dict.get('analysis_approach', '')
        self.problem_type = plan_dict.get('problem_type', 'unknown')
        self.focus_areas = plan_dict.get('focus_areas', [])
        self.derived_metrics = plan_dict.get('derived_metrics_needed', [])
        self.integration_strategy = plan_dict.get('integration_strategy', {})
        self.code_flow = plan_dict.get('code_flow', [])

class PlannerLLM(BaseAnalyst):
    """
    Stage 1: Planner LLM
    Generates high-level execution plan based on problem and file list
    """

    def __init__(self):
        """Initialize Planner LLM"""
        super().__init__(model=Config.MODEL_DATA_PLANNER)
        
        # Load prompts
        prompt_content = self._read_prompt_file("planner_prompts.md")
        self.prompts = self._split_prompts(prompt_content)

    def create_plan(
        self,
        brain_output: Dict,
        files: List[Dict]
    ) -> AnalysisPlan:
        """
        Create an analysis plan
        """
        logger.info("Planner LLM: Creating analysis plan...")

        user_prompt = self._build_user_prompt(brain_output, files)
        
        messages = [
            {"role": "system", "content": self.prompts['system']},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._call_llm(messages)
            logger.info("Planner LLM: Plan generated")
            return self._parse_plan(response)
        except Exception as e:
            logger.error(f"Planner LLM failed: {e}")
            # Return basic default plan
            return AnalysisPlan({
                "processing_strategy": "sequential", 
                "analysis_approach": "Default sequential processing due to planner failure"
            })

    def _build_user_prompt(self, brain_output: Dict, files: List[Dict]) -> str:
        """Build user prompt based on template"""
        
        main_def = brain_output.get('main_problem_definition', '')
        sub_problems = brain_output.get('sub_problems', [])
        problem_id = brain_output.get('problem_id', 'unknown')
        
        # Create a summary of sub-problems
        sub_prob_text = ""
        if sub_problems:
             for sp in sub_problems:
                 sub_prob_text += f"- ID: {sp.get('id', '')}\n"
                 sub_prob_text += f"  Title: {sp.get('title', '')}\n"
                 sub_prob_text += f"  Goal: {sp.get('description', '')}\n"

        # Format file list
        file_list = []
        for f in files:
            file_list.append(f"- {f['name']} (path: {f['path']}, match: {f.get('match_type', 'unknown')})")
        file_list_str = "\n".join(file_list) if file_list else "No files available"

        return self.prompts['user'].format(
            problem_id=problem_id,
            main_problem_definition=main_def,
            sub_problems_overview=sub_prob_text,
            file_list_str=file_list_str
        )

    def _parse_plan(self, response: str) -> AnalysisPlan:
        """Parse LLM JSON response"""
        try:
            # Clean response (handle markdown code blocks)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            
            plan_dict = json.loads(cleaned)
            return AnalysisPlan(plan_dict)
        except json.JSONDecodeError:
            logger.warning("Planner LLM response was not valid JSON, creating fallback plan")
            return AnalysisPlan({"analysis_approach": response})
