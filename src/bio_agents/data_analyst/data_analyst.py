"""
Data Analyst Agent
3-Stage LLM Pipeline for database analysis:
  Stage 1: Planner LLM - Creates analysis plan
  Stage 2: Executor - Runs LLM-generated code
  Stage 3: Summarizer LLM - Generates natural language summary
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd

from src.bio_agents.config import Config
from .data_utils import DataLoader, FileResolver
from .data_executor import CodeExecutor
from .data_planner import PlannerLLM, AnalysisPlan
from .data_summarizer import SummarizerLLM

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
        output_format: str = 'natural_language',
        temperature: float = None,
    ):
        """
        Initialize DataAnalystAgent

        Args:
            use_planner: Enable Stage 1 Planner LLM (default: True)
            use_summarizer: Enable Stage 3 Summarizer LLM (default: True)
            output_format: Output format - 'natural_language' or 'json' (default: 'natural_language')
            temperature: Temperature for LLM calls (default: Config.DEFAULT_TEMPERATURE)
        """
        self.temperature = temperature

        # Initialize components using global Config
        self.file_resolver = FileResolver(Config.DATA_DIR)
        self.data_loader = DataLoader()
        self.code_executor = CodeExecutor(temperature=temperature)

        # 3-Stage Pipeline configuration
        self.use_planner = use_planner
        self.use_summarizer = use_summarizer
        self.output_format = output_format

        # Initialize Stage 1: Planner LLM
        if use_planner:
            self.planner = PlannerLLM(temperature=temperature)
            logger.info("Stage 1 (Planner LLM) enabled")

        # Initialize Stage 3: Summarizer LLM
        if use_summarizer:
            self.summarizer = SummarizerLLM(temperature=temperature)
            logger.info("Stage 3 (Summarizer LLM) enabled")

        logger.info(f"DataAnalystAgent initialized with data_dir: {Config.DATA_DIR}")
        logger.info(f"Pipeline: Planner={use_planner}, Summarizer={use_summarizer}, Format={output_format}")

    def run_for_problem(self, problem_path: Union[str, Path], problem_dir: Union[str, Path, None] = None) -> Dict[str, Any]:
        """
        Standard entry point for the pipeline.
        Reads a problem JSON file (output from BrainAgent), performs analysis,
        and saves the result to a corresponding analysis file.
        
        Args:
            problem_path: Path to the problem JSON file.
            problem_dir: Optional explicit problem directory where data files are located.
                        If not provided, will be inferred from problem_path.
            
        Returns:
            Dict containing the analysis results.
        """
        start_time = time.time()
        problem_path = Path(problem_path)
        logger.info("=" * 80)
        logger.info(f"[DataAnalystAgent] Starting analysis for problem: {problem_path}")
        logger.info(f"[DataAnalystAgent] Problem directory: {problem_dir}")
        logger.info("=" * 80)
        
        # Load problem JSON (Brain output)
        logger.info(f"[Step 0] Loading Brain output JSON from: {problem_path}")
        load_start = time.time()
        with open(problem_path, 'r', encoding='utf-8') as f:
            brain_output = json.load(f)
        load_time = time.time() - load_start
        logger.info(f"[Step 0] ✓ Loaded Brain output in {load_time:.2f}s")
        logger.info(f"[Step 0]   - Problem ID: {brain_output.get('problem_id', 'unknown')}")
        logger.info(f"[Step 0]   - Sub-problems: {len(brain_output.get('sub_problems', []))}")

        # Update FileResolver to look in the problem directory first.
        # problem_path is the Brain output JSON. In the current pipeline it may live under
        # .../problem_X/01_brain/brain_decomposition.json, while data files live in .../problem_X/.
        logger.info(f"[Step 0.5] Determining problem data directory...")
        resolver_start = time.time()
        candidate_dirs = []
        if problem_path.parent.exists():
            candidate_dirs.append(problem_path.parent)
            logger.info(f"[Step 0.5]   Candidate 1: {problem_path.parent}")
        if problem_path.parent.parent.exists() and problem_path.parent.parent != problem_path.parent:
            candidate_dirs.append(problem_path.parent.parent)
            logger.info(f"[Step 0.5]   Candidate 2: {problem_path.parent.parent}")
        if problem_dir:
            candidate_dirs.insert(0, Path(problem_dir))
            logger.info(f"[Step 0.5]   Explicit directory (priority): {problem_dir}")

        def has_supported_data_files(d: Path) -> bool:
            try:
                file_count = 0
                for p in d.iterdir():
                    if p.is_file() and p.suffix.lower() in {
                        ".csv", ".tsv", ".txt", ".tab", ".xlsx", ".xls", ".json", ".parquet",
                        ".md", ".markdown",  # Markdown files
                        ".fa", ".fasta", ".fna", ".faa", ".ffn", ".frn",  # FASTA files
                        ".fq", ".fastq",  # FASTQ files (uncompressed)
                        ".gz"
                    }:
                        # Treat pure agent artifacts folder as "no data" if it contains only JSON
                        if p.suffix.lower() != ".json":
                            file_count += 1
                logger.info(f"[Step 0.5]   Directory {d}: {file_count} supported data files")
                return file_count > 0
            except Exception as e:
                logger.warning(f"[Step 0.5]   Error checking {d}: {e}")
                return False

        chosen_dir = None
        for d in candidate_dirs:
            if has_supported_data_files(d):
                chosen_dir = d
                logger.info(f"[Step 0.5]   ✓ Selected directory: {chosen_dir}")
                break

        if chosen_dir is None and candidate_dirs:
            chosen_dir = candidate_dirs[0]
            logger.info(f"[Step 0.5]   Using first candidate (no data files found): {chosen_dir}")

        if chosen_dir and chosen_dir.exists():
            logger.info(f"[Step 0.5] Initializing FileResolver with directory: {chosen_dir}")
            self.file_resolver = FileResolver(chosen_dir)
            resolver_time = time.time() - resolver_start
            logger.info(f"[Step 0.5] ✓ FileResolver initialized in {resolver_time:.2f}s")
        else:
            logger.warning(f"[Step 0.5] ⚠ No valid directory found, using default FileResolver")
            
        # Run analysis
        logger.info(f"[Step 1] Starting main analysis pipeline...")
        analysis_start = time.time()
        output = self.analyze(brain_output)
        analysis_time = time.time() - analysis_start
        logger.info(f"[Step 1] ✓ Analysis completed in {analysis_time:.2f}s")
        
        # Construct output path: save to 03_data_analysis/ directory instead of 01_brain/
        logger.info(f"[Step 2] Preparing output file...")
        save_start = time.time()
        output_ext = '.md' if self.output_format == 'natural_language' and isinstance(output, str) else '.json'
        
        # Determine the 03_data_analysis directory path
        # problem_path is like .../01_brain/brain_decomposition.json
        # We want to save to .../03_data_analysis/brain_decomposition_analysis.{ext}
        problem_root = problem_path.parent.parent  # Go up from 01_brain/ to problem_X/
        data_analysis_dir = problem_root / "03_data_analysis"
        data_analysis_dir.mkdir(parents=True, exist_ok=True)
        output_path = data_analysis_dir / (problem_path.stem + f"_analysis{output_ext}")
        
        logger.info(f"[Step 2]   Output path: {output_path}")
        logger.info(f"[Step 2]   Output format: {self.output_format} ({output_ext})")
        logger.info(f"[Step 2]   Output size: {len(str(output))} chars")
        
        self.save_output(output, output_path)
        save_time = time.time() - save_start
        
        total_time = time.time() - start_time
        logger.info(f"[Step 2] ✓ Output saved in {save_time:.2f}s")
        logger.info("=" * 80)
        logger.info(f"[DataAnalystAgent] ✓ COMPLETED in {total_time:.2f}s")
        logger.info(f"[DataAnalystAgent]   - Analysis: {analysis_time:.2f}s")
        logger.info(f"[DataAnalystAgent]   - Output: {save_time:.2f}s")
        logger.info(f"[DataAnalystAgent]   - Output file: {output_path}")
        logger.info("=" * 80)
        
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
        # Only use DB_list explicitly provided by BrainAgent, no LLM or regex extraction
        logger.info(f"[DB Collection] Collecting DB_list from sub_problems...")
        logger.info(f"[DB Collection]   Total sub_problems: {len(sub_problems)}")
        all_db_refs = set()
        active_sub_problems = []
        for idx, sp in enumerate(sub_problems, 1):
            db_flag = sp.get('DB_flag', 0)
            sp_id = sp.get('id', f'sub_{idx}')
            logger.info(f"[DB Collection]   Sub-problem {idx}: ID={sp_id}, DB_flag={db_flag}")
            if db_flag == 1:
                active_sub_problems.append(sp)
                db_list_str = sp.get('DB_list', '')
                refs = [r.strip() for r in db_list_str.split(',') if r.strip()]
                all_db_refs.update(refs)
                logger.info(f"[DB Collection]     ✓ Active (DB_flag=1)")
                logger.info(f"[DB Collection]     ✓ DB_list: {db_list_str}")
                logger.info(f"[DB Collection]     ✓ Extracted {len(refs)} references: {refs}")
            else:
                logger.info(f"[DB Collection]     ⊘ Skipped (DB_flag={db_flag})")
        
        logger.info(f"[DB Collection] ✓ Total active sub_problems: {len(active_sub_problems)}")
        logger.info(f"[DB Collection] ✓ Total unique DB references: {len(all_db_refs)}")
        logger.info(f"[DB Collection] ✓ References: {sorted(all_db_refs)}")

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
        logger.info(f"[File Resolution] Resolving file paths from DB_list...")
        resolve_start = time.time()
        combined_db_list = ', '.join(sorted(all_db_refs))
        logger.info(f"[File Resolution]   Combined DB_list: {combined_db_list}")
        logger.info(f"[File Resolution]   Active sub_problems: {len(active_sub_problems)} of {len(sub_problems)}")
        logger.info(f"[File Resolution]   FileResolver data_dir: {self.file_resolver.data_dir}")
        resolved_files = self.file_resolver.resolve(combined_db_list)
        resolve_time = time.time() - resolve_start

        if not resolved_files:
            logger.warning(f"[File Resolution] ⚠ Could not resolve files from DB_list: {combined_db_list}")
            logger.info(f"[File Resolution] Attempting fallback: scanning problem directory for all data files...")

            # Fallback: Get all data files in the problem directory
            resolved_files = self._get_all_data_files_in_directory(self.file_resolver.data_dir)

            if resolved_files:
                logger.info(f"[File Resolution] ✓ Fallback successful: found {len(resolved_files)} data files")
                for idx, file_info in enumerate(resolved_files, 1):
                    logger.info(f"[File Resolution]   [{idx}] {file_info['name']} (fallback)")
            else:
                logger.error(f"[File Resolution] ✗ Fallback FAILED: No data files found in directory")
                logger.error(f"[File Resolution]   DB_list: {combined_db_list}")
                logger.error(f"[File Resolution]   Data directory: {self.file_resolver.data_dir}")
                return {
                    'status': 'error',
                    'reason': f'Could not resolve files from DB_list and no data files found in directory',
                    'problem_id': brain_output.get('problem_id', 'unknown')
                }
        
        logger.info(f"[File Resolution] ✓ Resolved {len(resolved_files)} files in {resolve_time:.2f}s")
        for idx, file_info in enumerate(resolved_files, 1):
            logger.info(f"[File Resolution]   [{idx}] {file_info['name']}")
            logger.info(f"[File Resolution]       Path: {file_info['path']}")
            logger.info(f"[File Resolution]       Match type: {file_info.get('match_type', 'unknown')}")

        # ========== Stage 1: Planner LLM ==========
        analysis_plan = None
        if self.use_planner:
            logger.info("=" * 80)
            logger.info("[Stage 1: Planner LLM] Starting...")
            logger.info("=" * 80)
            planner_start = time.time()
            try:
                logger.info(f"[Stage 1]   Model: {Config.MODEL_DATA_PLANNER}")
                logger.info(f"[Stage 1]   Input files: {len(resolved_files)}")
                logger.info(f"[Stage 1]   Sub-problems: {len(active_sub_problems)}")
                analysis_plan = self.planner.create_plan(brain_output, resolved_files)
                planner_time = time.time() - planner_start
                logger.info(f"[Stage 1] ✓ Plan created in {planner_time:.2f}s")
                logger.info(f"[Stage 1]   Problem type: {analysis_plan.problem_type}")
                logger.info(f"[Stage 1]   Processing strategy: {analysis_plan.processing_strategy}")
                logger.info(f"[Stage 1]   File priority: {analysis_plan.file_priority}")
                logger.info(f"[Stage 1]   Focus areas: {analysis_plan.focus_areas}")
                logger.info(f"[Stage 1]   Code flow steps: {len(analysis_plan.code_flow)}")
            except Exception as e:
                planner_time = time.time() - planner_start
                logger.warning(f"[Stage 1] ✗ FAILED in {planner_time:.2f}s: {type(e).__name__}: {e}")
                logger.warning(f"[Stage 1]   Continuing without plan...")
                analysis_plan = None
        else:
            logger.info("[Stage 1: Planner LLM] ⊘ Disabled (use_planner=False)")

        # ========== Stage 2: Executor ==========
        logger.info("=" * 80)
        logger.info("[Stage 2: Executor] Starting file analysis...")
        logger.info("=" * 80)
        executor_start = time.time()
        file_analyses = []

        # Determine file processing order from plan or use default
        if analysis_plan and analysis_plan.file_priority:
            logger.info(f"[Stage 2] Using file priority from plan: {analysis_plan.file_priority}")
            file_order = {name: idx for idx, name in enumerate(analysis_plan.file_priority)}
            resolved_files_ordered = sorted(
                resolved_files,
                key=lambda f: file_order.get(f['name'], len(file_order))
            )
        else:
            logger.info(f"[Stage 2] Using default file order (no plan priority)")
            resolved_files_ordered = resolved_files

        logger.info(f"[Stage 2] Processing {len(resolved_files_ordered)} files...")
        for file_idx, file_info in enumerate(resolved_files_ordered, 1):
            file_start = time.time()
            logger.info(f"[Stage 2] [{file_idx}/{len(resolved_files_ordered)}] Processing: {file_info['name']}")
            logger.info(f"[Stage 2]   File path: {file_info['path']}")

            try:
                analysis = self._analyze_single_file(file_info, brain_output, analysis_plan)
                file_analyses.append(analysis)
                file_time = time.time() - file_start
                logger.info(f"[Stage 2]   ✓ Completed in {file_time:.2f}s")
                logger.info(f"[Stage 2]   ✓ Analysis result: type={analysis.get('type', 'unknown')}, "
                           f"rows={analysis.get('rows', 'unknown')}, columns={len(analysis.get('columns', []))}")
            except Exception as e:
                file_time = time.time() - file_start
                logger.error(f"[Stage 2]   ✗ FAILED in {file_time:.2f}s")
                logger.error(f"[Stage 2]   ✗ Error: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"[Stage 2]   ✗ Traceback:\n{traceback.format_exc()}")
                file_analyses.append({
                    'file_path': file_info['path'],
                    'file_name': file_info['name'],
                    'status': 'error',
                    'error': str(e)
                })
        
        executor_time = time.time() - executor_start
        successful = len([a for a in file_analyses if 'error' not in a])
        failed = len([a for a in file_analyses if 'error' in a])
        logger.info(f"[Stage 2] ✓ Executor completed in {executor_time:.2f}s")
        logger.info(f"[Stage 2]   Successful: {successful}/{len(file_analyses)}")
        logger.info(f"[Stage 2]   Failed: {failed}/{len(file_analyses)}")

        # Build execution results
        logger.info(f"[Output Building] Building final output...")
        build_start = time.time()
        execution_results = self._build_output(brain_output, file_analyses)
        build_time = time.time() - build_start
        logger.info(f"[Output Building] ✓ Output built in {build_time:.2f}s")
        if isinstance(execution_results, dict):
            if 'files' in execution_results:
                logger.info(f"[Output Building]   Output type: multi-file ({len(execution_results['files'])} files)")
            else:
                logger.info(f"[Output Building]   Output type: single-file")
            if 'integration' in execution_results:
                logger.info(f"[Output Building]   Integration strategy: present")

        # ========== Stage 3: Summarizer LLM ==========
        if self.use_summarizer and self.output_format == 'natural_language':
            logger.info("=" * 80)
            logger.info("[Stage 3: Summarizer LLM] Starting...")
            logger.info("=" * 80)
            summarizer_start = time.time()
            try:
                logger.info(f"[Stage 3]   Model: {Config.MODEL_DATA_SUMMARIZER}")
                logger.info(f"[Stage 3]   Input: {len(str(execution_results))} chars")
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
                summarizer_time = time.time() - summarizer_start
                logger.info(f"[Stage 3] ✓ Summary generated in {summarizer_time:.2f}s")
                logger.info(f"[Stage 3]   Summary length: {len(summary)} chars")
                return summary
            except Exception as e:
                summarizer_time = time.time() - summarizer_start
                logger.warning(f"[Stage 3] ✗ FAILED in {summarizer_time:.2f}s: {type(e).__name__}: {e}")
                logger.warning(f"[Stage 3]   Returning JSON output instead")
                import traceback
                logger.warning(f"[Stage 3]   Traceback:\n{traceback.format_exc()}")
                return execution_results
        else:
            if not self.use_summarizer:
                logger.info("[Stage 3: Summarizer LLM] ⊘ Disabled (use_summarizer=False)")
            elif self.output_format != 'natural_language':
                logger.info(f"[Stage 3: Summarizer LLM] ⊘ Skipped (output_format={self.output_format}, not 'natural_language')")

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
        file_name = file_info['name']

        # Load data
        logger.info(f"[File Analysis] Loading data file: {file_name}")
        logger.info(f"[File Analysis]   Path: {file_path}")
        load_start = time.time()
        try:
            df, metadata = self.data_loader.load_file(file_path, sample=True)
            load_time = time.time() - load_start
            logger.info(f"[File Analysis]   ✓ Loaded in {load_time:.2f}s")
            logger.info(f"[File Analysis]   ✓ Rows: {metadata['loaded_rows']} (total: {metadata.get('total_rows', 'unknown')})")
            logger.info(f"[File Analysis]   ✓ Columns: {len(metadata['columns'])}")
            logger.info(f"[File Analysis]   ✓ Format: {metadata['format']}")
            logger.info(f"[File Analysis]   ✓ Size: {metadata.get('file_size_mb', 0):.2f} MB")
            logger.info(f"[File Analysis]   ✓ Encoding: {metadata.get('encoding', 'unknown')}")
        except Exception as e:
            load_time = time.time() - load_start
            logger.error(f"[File Analysis]   ✗ Load FAILED in {load_time:.2f}s")
            logger.error(f"[File Analysis]   ✗ Error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[File Analysis]   ✗ Traceback:\n{traceback.format_exc()}")
            raise

        # Run LLM analysis with optional plan context
        logger.info(f"[File Analysis] Running LLM analysis...")
        logger.info(f"[File Analysis]   Model: {Config.MODEL_DATA_EXECUTOR}")
        logger.info(f"[File Analysis]   DataFrame shape: {df.shape}")
        logger.info(f"[File Analysis]   Has analysis plan: {analysis_plan is not None}")
        analysis_start = time.time()
        llm_analysis = self.code_executor.analyze_data(
            df=df,
            file_info=metadata,
            problem_context=brain_output,
            analysis_plan=analysis_plan
        )
        analysis_time = time.time() - analysis_start
        logger.info(f"[File Analysis]   ✓ LLM analysis completed in {analysis_time:.2f}s")
        
        # Safety check: ensure llm_analysis is a dictionary
        if not isinstance(llm_analysis, dict):
            logger.error(f"[File Analysis]   ✗ Executor returned non-dict result")
            logger.error(f"[File Analysis]   ✗ Type: {type(llm_analysis)}, Value: {llm_analysis}")
            llm_analysis = {"error": str(llm_analysis)}
        else:
            logger.info(f"[File Analysis]   ✓ Analysis keys: {list(llm_analysis.keys())}")
            logger.info(f"[File Analysis]   ✓ Data type: {llm_analysis.get('data_type', 'unknown')}")
            logger.info(f"[File Analysis]   ✓ Key columns: {llm_analysis.get('key_columns', [])}")

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

    def _has_supported_data_files(self, d: Path) -> bool:
        """Check if directory contains supported data files"""
        try:
            for p in d.iterdir():
                if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".txt", ".tab", ".xlsx", ".xls", ".json", ".parquet", ".fastq", ".fasta", ".fa", ".bam", ".sam", ".vcf", ".bed", ".pod5"}:
                    # Treat pure agent artifacts folder as "no data" if it contains only JSON
                    if p.suffix.lower() != ".json":
                        return True
            return False
        except Exception:
            return False

    def _get_all_data_files_in_directory(self, directory: Path) -> List[Dict[str, str]]:
        """
        Fallback: Get all supported data files in the problem directory.
        Excludes pipeline directories (01_brain ~ 08_answer) and problem/answer text files.
        If no files found in the current directory, also checks parent directory.

        Args:
            directory: The problem directory to scan

        Returns:
            List of file info dicts with 'path', 'name', and 'match_type' keys
        """
        # Directories to exclude (pipeline output directories)
        excluded_dirs = {
            '01_brain', '02_search', '03_data_analysis', '04_blue_draft',
            '05_red_critique', '06_bluex_revision', '07_red_review', '08_answer'
        }

        # Supported data file extensions
        supported_extensions = {
            '.csv', '.tsv', '.txt', '.tab', '.xlsx', '.xls', '.parquet',
            '.md', '.markdown',
            '.fa', '.fasta', '.fna', '.faa', '.ffn', '.frn',
            '.fq', '.fastq',
            '.gz', '.bam', '.sam', '.vcf', '.bed', '.pod5'
        }

        data_files = self._scan_directory_for_data_files(directory, excluded_dirs, supported_extensions)

        # If no files found, try parent directory (for temp_* subdirectory case)
        if not data_files and directory.parent.exists():
            logger.info(f"[Fallback] No data files in {directory.name}, checking parent directory: {directory.parent}")
            data_files = self._scan_directory_for_data_files(directory.parent, excluded_dirs, supported_extensions)
            if data_files:
                logger.info(f"[Fallback] ✓ Found {len(data_files)} data files in parent directory")

        return data_files

    def _scan_directory_for_data_files(
        self,
        directory: Path,
        excluded_dirs: set,
        supported_extensions: set
    ) -> List[Dict[str, str]]:
        """
        Scan a single directory for data files.

        Args:
            directory: Directory to scan
            excluded_dirs: Set of directory names to exclude
            supported_extensions: Set of supported file extensions

        Returns:
            List of file info dicts
        """
        data_files = []

        try:
            for item in directory.iterdir():
                # Skip excluded directories (including temp_* pattern)
                if item.is_dir():
                    if item.name in excluded_dirs or item.name.startswith('temp_'):
                        logger.debug(f"[Fallback] Skipping pipeline/temp directory: {item.name}")
                        continue
                    # Optionally scan subdirectories (non-pipeline)
                    for subitem in item.iterdir():
                        if subitem.is_file():
                            if self._is_valid_data_file(subitem, supported_extensions):
                                data_files.append({
                                    'path': str(subitem),
                                    'name': subitem.name,
                                    'match_type': 'directory_fallback'
                                })
                    continue

                # Process files in the root directory
                if item.is_file():
                    if self._is_valid_data_file(item, supported_extensions):
                        data_files.append({
                            'path': str(item),
                            'name': item.name,
                            'match_type': 'directory_fallback'
                        })
        except Exception as e:
            logger.error(f"[Fallback] Error scanning directory {directory}: {e}")

        return data_files

    def _is_valid_data_file(self, file_path: Path, supported_extensions: set) -> bool:
        """
        Check if a file is a valid data file (not problem/answer text files).

        Args:
            file_path: Path to the file
            supported_extensions: Set of supported file extensions

        Returns:
            True if the file is a valid data file, False otherwise
        """
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Exclude problem*.txt and answer*.txt files
        if suffix == '.txt':
            if name.startswith('problem') or name.startswith('answer'):
                logger.debug(f"[Fallback] Skipping problem/answer file: {file_path.name}")
                return False

        # Check if extension is supported
        if suffix in supported_extensions:
            return True

        # Handle double extensions like .fastq.gz
        if name.endswith('.fastq.gz') or name.endswith('.fq.gz'):
            return True

        return False

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

