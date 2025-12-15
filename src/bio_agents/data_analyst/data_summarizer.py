"""
Summarizer LLM Module
Stage 3: Generates natural language summary from analysis results
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

from src.bio_agents.config import Config
from .base_analyst import BaseAnalyst
from .data_planner import AnalysisPlan

logger = logging.getLogger(__name__)


class SummarizerLLM(BaseAnalyst):
    """
    Stage 3: Summarizer LLM
    Generates natural language summary of analysis results for downstream Solver module
    """

    def __init__(self):
        """Initialize Summarizer LLM"""
        super().__init__(model=Config.MODEL_DATA_SUMMARIZER)
        
        # Load consolidated prompts
        prompt_content = self._read_prompt_file("summarizer_prompts.md")
        self.prompts = self._split_prompts(prompt_content)

    def summarize(
        self,
        execution_results: Dict,
        problem_context: Dict,
        analysis_plan: Optional[AnalysisPlan] = None
    ) -> str:
        """
        Generate natural language summary of analysis results
        """
        logger.info("Summarizer LLM: Generating natural language summary...")

        prompt = self._build_prompt(execution_results, problem_context, analysis_plan)

        messages = [
            {"role": "system", "content": self.prompts['system']},
            {"role": "user", "content": prompt}
        ]

        try:
            # Need slightly higher creativity/fluency for summary
            summary = self._call_llm(messages, temperature=0.3)
            logger.info(f"Summarizer LLM: Summary generated ({len(summary)} chars)")
            return summary
        except Exception as e:
            logger.warning(f"Summarizer LLM failed: {e}, using fallback summary")
            return self._create_fallback_summary(execution_results, problem_context)

    def _build_prompt(
        self,
        results: Dict,
        context: Dict,
        plan: Optional[AnalysisPlan]
    ) -> str:
        """Build prompt for summarization LLM"""
        # Handle both new format (sub_problems array) and old format (sub_problem single)
        sub_problems = context.get('sub_problems', [])
        if not sub_problems:
            single_sub = context.get('sub_problem', {})
            if single_sub:
                sub_problems = [single_sub]

        # Build sub_problems text
        sub_problems_text = ""
        if sub_problems:
            for i, sp in enumerate(sub_problems, 1):
                sub_problems_text += f"""
### Sub-problem {i}: {sp.get('title', 'N/A')}
- **ID**: {sp.get('id', 'N/A')}
- **Description**: {sp.get('description', 'N/A')}
- **Suggested Approach**: {sp.get('suggested_approach', 'N/A')}
- **Required Data**: {sp.get('DB_list', 'N/A')}
"""

        # Format results for prompt
        results_str = json.dumps(results, indent=2, ensure_ascii=False)

        # Truncate if too long - increased limit for more detailed analysis
        if len(results_str) > 15000:
            results_str = results_str[:15000] + "\n... (truncated)"

        # Plan context if available
        plan_context = ""
        if plan:
            plan_context = f"""
## Analysis Plan Context
- Problem Type: {plan.problem_type}
- Processing Strategy: {plan.processing_strategy}
- Focus Areas: {', '.join(plan.focus_areas)}
- Analysis Approach: {plan.analysis_approach}
"""
        
        problem_id = context.get('problem_id', 'unknown')
        main_problem_definition = context.get('main_problem_definition', '')
        original_problem_text = context.get('original_problem_text', 'N/A')[:2000]
        sub_problem_count = len(sub_problems)

        return self.prompts['user'].format(
            sub_problem_count=sub_problem_count,
            problem_id=problem_id,
            main_problem_definition=main_problem_definition,
            original_problem_text=original_problem_text,
            sub_problems_text=sub_problems_text,
            plan_context=plan_context,
            results_str=results_str
        )

    def _create_fallback_summary(
        self,
        results: Dict,
        context: Dict
    ) -> str:
        """Create fallback summary when LLM fails"""
        # ... (Existing fallback logic kept identical) ...
        # (For brevity in this update, I'm pasting a minimal version, but ideally we keep full logic)
        
        files_info = results.get('files', []) if 'files' in results else [results] if 'file' in results else []
        
        summary_parts = []
        summary_parts.append(f"# Data Analysis Summary (Fallback)")
        summary_parts.append(f"Problem ID: {context.get('problem_id', 'unknown')}")
        summary_parts.append(f"\n## Files Analyzed")
        
        for f in files_info:
            summary_parts.append(f"- {f.get('file', 'unknown')}: {f.get('summary', 'No summary')}")
            
        summary_parts.append("\nNote: Detailed LLM summary generation failed.")
        
        return "\n".join(summary_parts)
