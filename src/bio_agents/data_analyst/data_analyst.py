"""
Data Analyst Agent
3-Stage LLM Pipeline for database analysis:
  Stage 1: Planner LLM - Creates analysis plan
  Stage 2: Executor - Runs LLM-generated code
  Stage 3: Summarizer LLM - Generates natural language summary
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd

from src.bio_agents.config import Config
from .data_utils import DataLoader, FileResolver
from .data_executor import CodeExecutor
from .data_planner import PlannerLLM, AnalysisPlan
from .data_summarizer import SummarizerLLM
from .db_list_extractor import DBListExtractor

logger = logging.getLogger(__name__)


class DataAnalystAgent:
    """
    Main class for LLM-based database analysis

    3-Stage Pipeline:
      Stage 1: Planner LLM - Creates analysis plan
      Stage 2: Executor - Runs LLM-generated code
      Stage 3: Summarizer LLM - Generates natural language summary

    Takes Brain module JSON output and produces analysis for downstream LLM modules
    """

    def __init__(
        self,
        use_planner: bool = True,
        use_summarizer: bool = True,
        output_format: str = 'natural_language'
    ):
        """
        Initialize DataAnalystAgent

        Args:
            use_planner: Enable Stage 1 Planner LLM (default: True)
            use_summarizer: Enable Stage 3 Summarizer LLM (default: True)
            output_format: Output format - 'natural_language' or 'json' (default: 'natural_language')
        """
        # Initialize components using global Config
        self.file_resolver = FileResolver(Config.DATA_DIR)
        self.data_loader = DataLoader()
        self.code_executor = CodeExecutor()  # No longer takes config arg
        self.db_list_extractor = DBListExtractor()  # LLM-based extraction

        # 3-Stage Pipeline configuration
        self.use_planner = use_planner
        self.use_summarizer = use_summarizer
        self.output_format = output_format

        # Initialize Stage 1: Planner LLM
        if use_planner:
            self.planner = PlannerLLM()  # No longer takes config arg
            logger.info("Stage 1 (Planner LLM) enabled")

        # Initialize Stage 3: Summarizer LLM
        if use_summarizer:
            self.summarizer = SummarizerLLM()  # No longer takes config arg
            logger.info("Stage 3 (Summarizer LLM) enabled")

        logger.info(f"DataAnalystAgent initialized with data_dir: {Config.DATA_DIR}")
        logger.info(f"Pipeline: Planner={use_planner}, Summarizer={use_summarizer}, Format={output_format}")

    def run_for_problem(self, problem_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Standard entry point for the pipeline.
        Reads a problem JSON file (output from BrainAgent), performs analysis,
        and saves the result to a corresponding analysis file.
        
        Args:
            problem_path: Path to the problem JSON file.
            
        Returns:
            Dict containing the analysis results.
        """
        problem_path = Path(problem_path)
        logger.info(f"Running DataAnalystAgent for problem: {problem_path}")
        
        # Load problem JSON (Brain output)
        with open(problem_path, 'r', encoding='utf-8') as f:
            brain_output = json.load(f)

        # Update FileResolver to look in the problem directory first.
        # problem_path is the Brain output JSON. In the current pipeline it may live under
        # .../problem_X/01_brain/brain_decomposition.json, while data files live in .../problem_X/.
        candidate_dirs = []
        if problem_path.parent.exists():
            candidate_dirs.append(problem_path.parent)
        if problem_path.parent.parent.exists() and problem_path.parent.parent != problem_path.parent:
            candidate_dirs.append(problem_path.parent.parent)

        def has_supported_data_files(d: Path) -> bool:
            try:
                for p in d.iterdir():
                    if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".txt", ".tab", ".xlsx", ".xls", ".json", ".parquet"}:
                        # Treat pure agent artifacts folder as "no data" if it contains only JSON
                        if p.suffix.lower() != ".json":
                            return True
                return False
            except Exception:
                return False

        chosen_dir = None
        for d in candidate_dirs:
            if has_supported_data_files(d):
                chosen_dir = d
                break

        if chosen_dir is None and candidate_dirs:
            chosen_dir = candidate_dirs[0]

        if chosen_dir and chosen_dir.exists():
            logger.info(f"Updating FileResolver to use problem directory: {chosen_dir}")
            self.file_resolver = FileResolver(chosen_dir)
            
        # Run analysis
        output = self.analyze(brain_output)
        
        # Construct output path (replace .json with _analysis.json/md)
        output_ext = '.md' if self.output_format == 'natural_language' and isinstance(output, str) else '.json'
        output_path = problem_path.parent / (problem_path.stem + f"_analysis{output_ext}")
        
        self.save_output(output, output_path)
        
        return {
            "output": output,
            "output_path": str(output_path),
            "status": "success"
        }

    def analyze(self, input_json: Union[str, Dict]) -> Union[str, Dict]:
        """
        Analyze database based on Brain module JSON using 3-stage pipeline
        """
        # Load input JSON
        if isinstance(input_json, str):
            input_path = Path(input_json)
            with open(input_path, 'r', encoding='utf-8') as f:
                brain_output = json.load(f)
            logger.info(f"Loaded input JSON from: {input_path}")
        else:
            brain_output = input_json

        # Handle both new format (sub_problems array) and old format (sub_problem single)
        sub_problems = brain_output.get('sub_problems', [])
        if not sub_problems:
            # Backward compatibility: convert single sub_problem to list
            single_sub = brain_output.get('sub_problem', {})
            if single_sub:
                sub_problems = [single_sub]

        # Collect DB_list from all sub_problems with DB_flag=1
        all_db_refs = set()
        active_sub_problems = []
        for sp in sub_problems:
            if sp.get('DB_flag') == 1:
                active_sub_problems.append(sp)
                db_list_str = sp.get('DB_list', '')
                refs = [r.strip() for r in db_list_str.split(',') if r.strip()]
                all_db_refs.update(refs)

        # ========== 2-Stage Extraction Strategy ==========

        # Stage 1: LLM-based extraction (primary method)
        logger.info("=== Stage 1: LLM-based DB_list extraction ===")
        llm_extracted_refs = self.db_list_extractor.extract_db_list(brain_output)

        if llm_extracted_refs:
            all_db_refs.update(llm_extracted_refs)
            logger.info(f"LLM extracted {len(llm_extracted_refs)} references: {llm_extracted_refs}")
        else:
            logger.warning("LLM extraction returned no results")

        # Stage 2: Regex-based extraction (fallback method)
        # Extract additional data references from original_problem_text using regex
        text = brain_output.get('original_problem_text', '')

        # 1. Extract Q patterns (Q1, Q2, ..., Q9)
        q_patterns = set(re.findall(r'Q\d+', text, re.IGNORECASE))
        regex_refs = set(q_patterns)

        # 2. Extract file names with extensions
        file_patterns = re.findall(
            r'([A-Za-z0-9_\-\.]+\.(?:pod5|bam|sam|csv|tsv|fastq|fasta|vcf|bed|bigWig))',
            text,
            re.IGNORECASE
        )
        regex_refs.update(file_patterns)

        # 3. Extract keywords from bullet points
        bullet_keywords = re.findall(r'\*\s+([A-Za-z0-9_\-]+)', text)
        regex_refs.update(bullet_keywords)

        # 4. Create Q-prefixed combinations
        expanded_refs = set()
        for ref in regex_refs.copy():
            expanded_refs.add(ref)
            # Add Q-prefixed variants (Q5.exhaustion_signature, Q1.features, etc.)
            for q_num in q_patterns:
                if not ref.upper().startswith('Q'):  # Don't double-prefix
                    expanded_refs.add(f"{q_num}.{ref}")

        # Combine LLM and regex results
        all_db_refs.update(expanded_refs)
        logger.info(f"Total data references (LLM + Regex): {len(all_db_refs)} candidates")

        # Check if any active sub_problems exist
        if not active_sub_problems:
            logger.info("No sub_problem with DB_flag=1, skipping database analysis")
            return {
                'status': 'skipped',
                'reason': 'No sub_problem with DB_flag=1',
                'problem_id': brain_output.get('problem_id', 'unknown')
            }

        # Check if we have any DB references
        if not all_db_refs:
            logger.warning("DB_list is empty in all active sub_problems")
            return {
                'status': 'error',
                'reason': 'DB_list is empty',
                'problem_id': brain_output.get('problem_id', 'unknown')
            }

        # Resolve file paths from combined DB_list
        combined_db_list = ', '.join(all_db_refs)
        logger.info(f"Resolving combined DB_list: {combined_db_list}")
        logger.info(f"Active sub_problems: {len(active_sub_problems)} of {len(sub_problems)}")
        resolved_files = self.file_resolver.resolve(combined_db_list)

        if not resolved_files:
            logger.error(f"Could not resolve any files from DB_list: {combined_db_list}")
            return {
                'status': 'error',
                'reason': f'Could not resolve files from DB_list: {combined_db_list}',
                'problem_id': brain_output.get('problem_id', 'unknown')
            }

        # ========== Stage 1: Planner LLM ==========
        analysis_plan = None
        if self.use_planner:
            logger.info("=== Stage 1: Planner LLM ===")
            try:
                analysis_plan = self.planner.create_plan(brain_output, resolved_files)
                logger.info(f"Analysis plan created: type={analysis_plan.problem_type}, "
                           f"strategy={analysis_plan.processing_strategy}")
            except Exception as e:
                logger.warning(f"Stage 1 (Planner) failed: {e}, continuing without plan")
                analysis_plan = None

        # ========== Stage 2: Executor ==========
        logger.info("=== Stage 2: Executor ===")
        file_analyses = []

        # Determine file processing order from plan or use default
        if analysis_plan and analysis_plan.file_priority:
            # Reorder resolved_files based on plan priority
            file_order = {name: idx for idx, name in enumerate(analysis_plan.file_priority)}
            resolved_files_ordered = sorted(
                resolved_files,
                key=lambda f: file_order.get(f['name'], len(file_order))
            )
        else:
            resolved_files_ordered = resolved_files

        for file_info in resolved_files_ordered:
            logger.info(f"Analyzing file: {file_info['name']}")

            try:
                analysis = self._analyze_single_file(file_info, brain_output, analysis_plan)
                file_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing {file_info['name']}: {str(e)}")
                file_analyses.append({
                    'file_path': file_info['path'],
                    'file_name': file_info['name'],
                    'status': 'error',
                    'error': str(e)
                })

        # Build execution results
        execution_results = self._build_output(brain_output, file_analyses)

        # ========== Stage 3: Summarizer LLM ==========
        if self.use_summarizer and self.output_format == 'natural_language':
            logger.info("=== Stage 3: Summarizer LLM ===")
            try:
                # Enhanced context with sub_problems array for integrated analysis
                enhanced_context = {
                    **brain_output,
                    'sub_problems': sub_problems,
                    'active_sub_problems': active_sub_problems
                }
                summary = self.summarizer.summarize(
                    execution_results=execution_results,
                    problem_context=enhanced_context,
                    analysis_plan=analysis_plan
                )
                logger.info(f"Natural language summary generated ({len(summary)} chars)")
                return summary
            except Exception as e:
                logger.warning(f"Stage 3 (Summarizer) failed: {e}, returning JSON instead")
                return execution_results

        return execution_results

    def _analyze_single_file(
        self,
        file_info: Dict,
        brain_output: Dict,
        analysis_plan: Optional[AnalysisPlan] = None
    ) -> Dict:
        """
        Analyze a single file - produces compact output for LLM prompt insertion

        Args:
            file_info: File information from resolver
            brain_output: Full Brain module output for context
            analysis_plan: Optional analysis plan from Planner stage

        Returns:
            Compact analysis result for this file (no sample data)
        """
        file_path = file_info['path']

        # Load data
        df, metadata = self.data_loader.load_file(file_path, sample=True)

        # Run LLM analysis with optional plan context
        llm_analysis = self.code_executor.analyze_data(
            df=df,
            file_info=metadata,
            problem_context=brain_output,
            analysis_plan=analysis_plan
        )
        
        # Safety check: ensure llm_analysis is a dictionary
        if not isinstance(llm_analysis, dict):
            logger.error(f"Executor returned non-dict result for {file_info['name']}: {llm_analysis}")
            llm_analysis = {"error": str(llm_analysis)}

        # Build enriched column info with biological context
        enriched_columns = self._build_enriched_columns(df, llm_analysis.get('columns', []))

        result = {
            'file': metadata['file_name'],
            'type': llm_analysis.get('data_type', 'unknown'),
            'rows': metadata['total_rows'],
            'columns': enriched_columns,
            'keys': llm_analysis.get('key_columns', []),
            'summary': llm_analysis.get('data_summary', '')
        }

        # Add integration strategy if present
        integration = llm_analysis.get('integration_strategy')
        if integration:
            result['integration'] = integration

        # Add derived metrics if present
        derived_metrics = llm_analysis.get('derived_metrics', [])
        if derived_metrics:
            result['derived_metrics'] = derived_metrics

        return result

    def _build_enriched_columns(self, df: pd.DataFrame, llm_columns: List[Dict]) -> List[Dict]:
        """
        Build enriched column info with biological context

        Args:
            df: DataFrame
            llm_columns: Column info from LLM analysis

        Returns:
            List of enriched column dictionaries
        """
        llm_lookup = {}
        for col in llm_columns:
            if isinstance(col, dict) and 'name' in col:
                llm_lookup[col['name']] = col
            elif isinstance(col, str):
                llm_lookup[col] = {'name': col}
        enriched = []

        for col in df.columns:
            dtype = 'num' if pd.api.types.is_numeric_dtype(df[col]) else 'str'
            llm_col = llm_lookup.get(col, {})

            col_info = {
                'name': col,
                'type': dtype,
                'bio': llm_col.get('bio_meaning', ''),
                'use': llm_col.get('usage_hint', '')
            }

            # Only include non-empty fields
            if not col_info['bio']:
                col_info['bio'] = f"{dtype} column"
            if not col_info['use']:
                col_info['use'] = f"Use for {llm_col.get('role', 'analysis')}"

            enriched.append(col_info)

        return enriched

    def _generate_integration_code(
        self,
        file_analyses: List[Dict],
        brain_output: Dict
    ) -> Optional[Dict]:
        """
        Generate code to integrate multiple data files if needed

        Args:
            file_analyses: List of file analysis results
            brain_output: Brain module output for context

        Returns:
            Integration info dict or None
        """
        # Check if any file has integration strategy
        integration_files = [
            f for f in file_analyses
            if f.get('integration') and f['integration'].get('target_files')
        ]

        if not integration_files or len(file_analyses) < 2:
            return None

        # Get the main file's integration strategy
        main_file = integration_files[0]
        strategy = main_file.get('integration', {})

        # Generate integration code using LLM
        prompt = f"""Generate Python code to integrate these data files:

Files:
{json.dumps([{'file': f['file'], 'type': f['type'], 'keys': f.get('keys', [])} for f in file_analyses], indent=2)}

Integration Strategy:
- Join key: {strategy.get('join_key', 'unknown')}
- Join type: {strategy.get('join_type', 'left')}
- Strategy: {strategy.get('strategy', '')}

Problem Context: {brain_output.get('sub_problem', {}).get('description', '')}

Generate code that:
1. Loads each file
2. Merges them on the join key
3. Saves the result to 'integrated_data.csv'

Output the code as a single Python script. Use pandas as pd.
"""

        try:
            response = self.code_executor._call_llm(prompt)
            code = self.code_executor._extract_code(response)

            return {
                'code': code,
                'join_key': strategy.get('join_key'),
                'files': [f['file'] for f in file_analyses],
                'description': f"Integration of {len(file_analyses)} files on {strategy.get('join_key')}"
            }
        except Exception as e:
            logger.warning(f"Failed to generate integration code: {e}")
            return None

    def _build_output(self, brain_output: Dict, file_analyses: List[Dict]) -> Dict:
        """
        Build compact final output JSON for direct LLM prompt insertion

        Args:
            brain_output: Original Brain module output
            file_analyses: List of file analysis results

        Returns:
            Compact output dictionary
        """
        # Filter out error entries
        valid_analyses = [a for a in file_analyses if 'error' not in a]
        error_analyses = [a for a in file_analyses if 'error' in a]

        if not valid_analyses:
            # Return error info if all failed
            return {
                'error': error_analyses[0].get('error', 'Analysis failed') if error_analyses else 'No files analyzed'
            }

        # Single file: return directly without wrapper
        if len(valid_analyses) == 1:
            return valid_analyses[0]

        # Multiple files: generate integration code if needed
        output = {'files': valid_analyses}

        # Check if integration is needed and generate code
        integration_info = self._generate_integration_code(valid_analyses, brain_output)
        if integration_info:
            output['integration'] = integration_info

        return output

    def save_output(self, output: Union[str, Dict], output_path: Union[str, Path]) -> None:
        """
        Save analysis output to file

        Args:
            output: Analysis output (dict for JSON, str for natural language)
            output_path: Path to save file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(output, str):
            # Natural language output - save as text/markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
        else:
            # JSON output
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"Output saved to: {output_path}")

    def analyze_and_save(
        self,
        input_json: Union[str, Dict],
        output_path: str
    ) -> Union[str, Dict]:
        """
        Analyze and save results in one call

        Args:
            input_json: Input JSON path or dict
            output_path: Output path (JSON for dict, text for natural language)

        Returns:
            Analysis output (dict for JSON, str for natural language)
        """
        output = self.analyze(input_json)
        self.save_output(output, output_path)
        return output

