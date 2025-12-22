import os
import glob
import json
import time
import re
import shutil
import sys
import argparse
import contextlib
import time as _time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import contextvars
from pathlib import Path

# Import Agents from src
from src.bio_agents.brain.brain import BrainAgent
from src.bio_agents.search.search_agent import SearchAgent
from src.bio_agents.blue.blue_agent import BlueAgent
from src.bio_agents.red.red_agent import RedAgent
from src.bio_agents.bluex.bluex_agent import BlueXAgent
from src.bio_agents.data_analyst import DataAnalystAgent
from src.bio_agents.answer import AnswerAgent

# Configuration
# INPUT_DIR will be set from CLI argument or default to "problems"
SRC_DIR = Path("src/bio_agents")

# Template Paths
TEMPLATE_PATHS = {
    "brain": {
        "system": SRC_DIR / "brain" / "prompts" / "system_prompt.md",
    },
    "search": {
        "system": SRC_DIR / "search" / "prompts" / "search_system.md",
        "user": SRC_DIR / "search" / "prompts" / "search_user_template.md"
    },
    "blue": {
        "system": SRC_DIR / "blue" / "prompts" / "blue_system.md",
        "user": SRC_DIR / "blue" / "prompts" / "blue_user_template.md"
    },
    "red": {
        "system": SRC_DIR / "red" / "prompts" / "red_system.md",
        "user": SRC_DIR / "red" / "prompts" / "red_user_template.md"
    },
    "bluex": {
        "system": SRC_DIR / "bluex" / "prompts" / "bluex_system.md",
        "user": SRC_DIR / "bluex" / "prompts" / "bluex_user_template.md"
    },
    "answer": {
        "system": SRC_DIR / "answer" / "prompts" / "answer_system.md",
        "user": SRC_DIR / "answer" / "prompts" / "answer_user_template.md",
    }
}

# Dummy file location (will be set after INPUT_DIR is determined)
DUMMY_DATA_ANALYSIS = None  # Will be set in main()

def ensure_dirs(problem_output_dir):
    # Kept for compatibility; current pipeline uses numbered step directories.
    for step_dir in [
        "01_brain",
        "02_search",
        "03_data_analysis",
        "04_blue_draft",
        "05_red_critique",
        "06_bluex_revision",
        "07_red_review",
        "08_answer",
    ]:
        (problem_output_dir / step_dir).mkdir(parents=True, exist_ok=True)

def save_sub_problem_json(output_path, brain_data, sub_problem):
    """
    Saves a specific sub-problem as a JSON file, including the parent context.
    """
    data = {
        "original_problem_text": brain_data.original_problem_text,
        "main_problem_definition": brain_data.main_problem_definition,
        "sub_problem": sub_problem.model_dump()
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


_stdout_lock = threading.Lock()
_suppress_stdout_flag = contextvars.ContextVar("suppress_stdout", default=False)
_ORIGINAL_STDOUT = sys.stdout


class _StdoutRouter:
    """
    Thread/context-aware stdout router.

    - When suppress flag is set in the current context, stdout writes are discarded.
    - Otherwise, writes are forwarded to the original stdout with a global lock to
      avoid interleaved writes across threads.

    This avoids changing sys.stdout per-thread (which is not thread-safe).
    """

    def write(self, s: str) -> int:
        if _suppress_stdout_flag.get():
            return len(s)
        with _stdout_lock:
            return _ORIGINAL_STDOUT.write(s)

    def flush(self) -> None:
        if _suppress_stdout_flag.get():
            return
        with _stdout_lock:
            return _ORIGINAL_STDOUT.flush()

    def isatty(self) -> bool:
        return getattr(_ORIGINAL_STDOUT, "isatty", lambda: False)()

    def fileno(self) -> int:
        return getattr(_ORIGINAL_STDOUT, "fileno")()

    def __getattr__(self, name: str):
        return getattr(_ORIGINAL_STDOUT, name)


# Install router once so suppression works safely under threading.
if not isinstance(sys.stdout, _StdoutRouter):
    sys.stdout = _StdoutRouter()


@contextlib.contextmanager
def suppress_stdout(enabled: bool):
    """
    Suppress stdout (prints) when enabled=True, in a thread-safe way.
    Stderr is intentionally not suppressed so exceptions remain visible.
    """
    if not enabled:
        yield
        return

    token = _suppress_stdout_flag.set(True)
    try:
        yield
    finally:
        _suppress_stdout_flag.reset(token)


_status_lock = threading.Lock()
_current_problem = contextvars.ContextVar("current_problem", default="")


def status(message: str) -> None:
    """
    Minimal progress output to stderr so it remains visible even when stdout is suppressed.
    """
    prefix = _current_problem.get()
    line = f"[{prefix}] {message}" if prefix else message
    with _status_lock:
        print(line, file=sys.stderr, flush=True)


@contextlib.contextmanager
def progress_step(label: str):
    """
    Emit minimal progress to stderr with elapsed time.
    """
    start = _time.time()
    status(f"{label} ...")
    try:
        yield
    finally:
        elapsed = _time.time() - start
        status(f"{label} done ({elapsed:.1f}s)")


def run_pipeline(file_path, *, verbose: bool = False):
    file_name = os.path.basename(file_path)
    token = _current_problem.set(os.path.splitext(file_name)[0])
    pipeline_start = _time.time()
    status(f"\n[{file_name}] Pipeline start")

    try:
        # Determine Problem ID from filename (e.g., problem_1.txt -> problem_1)
        problem_id = os.path.splitext(file_name)[0]
        
        # Base Output Directory is the same as the problem file's directory
        # structure: problems/problem_1/01_search/ ...
        problem_output_dir = Path(file_path).parent

        # Check if final answer already exists - skip entire pipeline if so
        answer_id = problem_id
        if answer_id.lower().startswith("problem_"):
            answer_id = answer_id[len("problem_"):]
        if not answer_id:
            answer_id = problem_id
        final_answer_path = problem_output_dir / f"answer_{answer_id}.txt"
        
        if final_answer_path.exists():
            status(f"[Skip] Final answer already exists: {final_answer_path}")
            status(f"[Total] {file_name} skipped (already completed) in {(_time.time() - pipeline_start):.1f}s")
            return

        # 1. Read Input (only if needed)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 2. Brain Phase
        step1_dir = problem_output_dir / "01_brain"
        step1_dir.mkdir(parents=True, exist_ok=True)
        brain_output_path = step1_dir / "brain_decomposition.json"

        if brain_output_path.exists():
            status(f"[Skip] Brain output already exists: {brain_output_path}")
        else:
            with progress_step("[1/7] Brain: analyzing question"):
                with suppress_stdout(not verbose):
                    brain_agent = BrainAgent(system_prompt_path=TEMPLATE_PATHS["brain"]["system"])
                    brain_result = brain_agent.analyze_question(content)
            
            # Save Brain Result (Global context)
            with open(brain_output_path, "w", encoding="utf-8") as f:
                f.write(brain_result.model_dump_json(indent=2))
            status(f"      saved: {brain_output_path}")

        # Initialize Agents (lazy initialization - only when needed)
        search_agent = None
        data_analyst_agent = None
        blue_agent = None
        red_agent = None
        bluex_agent = None
        answer_agent = None

        # --- Step 2: Search ---
        step2_dir = problem_output_dir / "02_search"
        search_result_file = step2_dir / "output.txt"
        
        if search_result_file.exists():
            status(f"[Skip] Search output already exists: {search_result_file}")
        else:
            # Backward-compatible fallback
            legacy = step2_dir / "search_results.txt"
            if legacy.exists():
                search_result_file = legacy
                status(f"[Skip] Search output already exists (legacy): {search_result_file}")
            else:
                if search_agent is None:
                    with suppress_stdout(not verbose):
                        search_agent = SearchAgent()
                with progress_step("[2/7] SearchAgent: generating literature report"):
                    with suppress_stdout(not verbose):
                        search_agent.run_for_problem(
                            brain_path=brain_output_path,
                            system_path=TEMPLATE_PATHS["search"]["system"],
                            user_template_path=TEMPLATE_PATHS["search"]["user"],
                            output_dir=step2_dir
                        )
                search_result_file = step2_dir / "output.txt"
                if not search_result_file.exists():
                    # Backward-compatible fallback
                    legacy = step2_dir / "search_results.txt"
                    if legacy.exists():
                        search_result_file = legacy
                    else:
                        raise FileNotFoundError(f"[Error] Search result not found at {search_result_file}.")
                status(f"      saved: {search_result_file}")

        # --- Step 3: Data Analysis ---
        step3_dir = problem_output_dir / "03_data_analysis"
        step3_dir.mkdir(parents=True, exist_ok=True)

        # Always produce a stable downstream artifact (text) even if analysis is skipped/errored.
        data_analysis_results_txt = step3_dir / "data_analysis_results.txt"
        data_analysis_file = data_analysis_results_txt  # downstream uses this path

        analysis_result = None
        if data_analysis_results_txt.exists():
            status(f"[Skip] Data analysis output already exists: {data_analysis_results_txt}")
        else:
            if data_analyst_agent is None:
                with suppress_stdout(not verbose):
                    data_analyst_agent = DataAnalystAgent()
            with progress_step("[3/7] DataAnalystAgent: analyzing referenced data files"):
                try:
                    with suppress_stdout(not verbose):
                        # Pass problem_output_dir explicitly to ensure data files are found correctly
                        analysis_result = data_analyst_agent.run_for_problem(
                            problem_path=brain_output_path,
                            problem_dir=problem_output_dir
                        )
                except Exception as e:
                    status(f"      warning: data analysis failed; continuing with N/A ({type(e).__name__}: {e})")
                    analysis_result = None

        # Move/copy the agent-produced artifact into 03_data_analysis/ when available,
        # but always write a human-readable .txt summary for downstream prompts.
        # Only process if file doesn't already exist
        if not data_analysis_results_txt.exists():
            try:
                if isinstance(analysis_result, dict):
                    output_path_str = analysis_result.get("output_path", "")
                    output_obj = analysis_result.get("output", None)

                    # Store the original analysis output file under 03_data_analysis/ if it exists
                    if output_path_str:
                        produced_path = Path(output_path_str)
                        if produced_path.exists():
                            ext = produced_path.suffix or ".txt"
                            moved_path = step3_dir / f"data_analysis{ext}"
                            if produced_path.resolve() != moved_path.resolve():
                                try:
                                    shutil.move(str(produced_path), str(moved_path))
                                except Exception:
                                    shutil.copy2(str(produced_path), str(moved_path))
                                    os.remove(str(produced_path))
                            status(f"      saved: {moved_path}")

                    # Build text for downstream consumption
                    # If output_path exists and is a file, read it; otherwise use output_obj
                    if output_path_str:
                        produced_path = Path(output_path_str)
                        if produced_path.exists() and produced_path.is_file():
                            # Read the file content if it's a text file
                            if produced_path.suffix in ['.txt', '.md']:
                                with open(produced_path, "r", encoding="utf-8") as f:
                                    text = f.read()
                            else:
                                # For other formats, use output_obj or convert
                                if isinstance(output_obj, str):
                                    text = output_obj
                                elif isinstance(output_obj, (dict, list)):
                                    text = json.dumps(output_obj, indent=2, ensure_ascii=False)
                                else:
                                    text = str(output_obj) if output_obj else "N/A: No specific data analysis was produced."
                        else:
                            # File doesn't exist, use output_obj
                            if isinstance(output_obj, str):
                                text = output_obj
                            elif isinstance(output_obj, (dict, list)):
                                text = json.dumps(output_obj, indent=2, ensure_ascii=False)
                            elif output_obj is None:
                                text = "N/A: No specific data analysis was produced."
                            else:
                                text = str(output_obj)
                    else:
                        # No output_path, use output_obj
                        if isinstance(output_obj, str):
                            text = output_obj
                        elif isinstance(output_obj, (dict, list)):
                            text = json.dumps(output_obj, indent=2, ensure_ascii=False)
                        elif output_obj is None:
                            text = "N/A: No specific data analysis was produced."
                        else:
                            text = str(output_obj)
                else:
                    # No result (exception or unexpected return)
                    with open(DUMMY_DATA_ANALYSIS, "r", encoding="utf-8") as src:
                        text = src.read()

                with open(data_analysis_results_txt, "w", encoding="utf-8") as f:
                    f.write(text)
                status(f"      saved: {data_analysis_results_txt}")

            except Exception as e:
                # Last-resort fallback: ensure file exists
                status(f"      warning: failed to write analysis summary; using dummy ({type(e).__name__}: {e})")
                with open(DUMMY_DATA_ANALYSIS, "r", encoding="utf-8") as src:
                    dummy_text = src.read()
                with open(data_analysis_results_txt, "w", encoding="utf-8") as dst:
                    dst.write(dummy_text)
                status(f"      saved: {data_analysis_results_txt}")

        # --- Step 4: Blue (Initial Draft) ---
        step4_dir = problem_output_dir / "04_blue_draft"
        blue_result_file = step4_dir / "output.txt"
        
        if blue_result_file.exists():
            status(f"[Skip] Blue draft already exists: {blue_result_file}")
        else:
            legacy = step4_dir / "blue_results.txt"
            if legacy.exists():
                blue_result_file = legacy
                status(f"[Skip] Blue draft already exists (legacy): {blue_result_file}")
            else:
                if blue_agent is None:
                    with suppress_stdout(not verbose):
                        blue_agent = BlueAgent()
                with progress_step("[4/7] BlueAgent: writing initial draft"):
                    with suppress_stdout(not verbose):
                        blue_agent.run_for_problem(
                            brain_path=brain_output_path,
                            system_path=TEMPLATE_PATHS["blue"]["system"],
                            user_template_path=TEMPLATE_PATHS["blue"]["user"],
                            full_report_path=search_result_file,
                            data_analysis_results_path=data_analysis_file,
                            output_dir=step4_dir
                        )
                blue_result_file = step4_dir / "output.txt"
                if not blue_result_file.exists():
                    legacy = step4_dir / "blue_results.txt"
                    if legacy.exists():
                        blue_result_file = legacy
                status(f"      saved: {blue_result_file}")

        # --- Step 5: Red (Critique) ---
        step5_dir = problem_output_dir / "05_red_critique"
        red_result_file = step5_dir / "output.txt"
        
        if red_result_file.exists():
            status(f"[Skip] Red critique already exists: {red_result_file}")
        else:
            legacy = step5_dir / "red_results.txt"
            if legacy.exists():
                red_result_file = legacy
                status(f"[Skip] Red critique already exists (legacy): {red_result_file}")
            else:
                if red_agent is None:
                    with suppress_stdout(not verbose):
                        red_agent = RedAgent()
                with progress_step("[5/7] RedAgent: critiquing draft"):
                    with suppress_stdout(not verbose):
                        red_agent.run_for_problem(
                            brain_path=brain_output_path,
                            system_path=TEMPLATE_PATHS["red"]["system"],
                            user_template_path=TEMPLATE_PATHS["red"]["user"],
                            blue_report_path=blue_result_file,
                            output_dir=step5_dir
                        )
                red_result_file = step5_dir / "output.txt"
                if not red_result_file.exists():
                    legacy = step5_dir / "red_results.txt"
                    if legacy.exists():
                        red_result_file = legacy
                status(f"      saved: {red_result_file}")

        # --- Step 6: BlueX (Revision) ---
        step6_dir = problem_output_dir / "06_bluex_revision"
        bluex_result_file = step6_dir / "output.txt"
        
        if bluex_result_file.exists():
            status(f"[Skip] BlueX revision already exists: {bluex_result_file}")
        else:
            legacy = step6_dir / "blue_results.txt"
            if legacy.exists():
                bluex_result_file = legacy
                status(f"[Skip] BlueX revision already exists (legacy): {bluex_result_file}")
            else:
                if bluex_agent is None:
                    with suppress_stdout(not verbose):
                        bluex_agent = BlueXAgent()
                with progress_step("[6/7] BlueXAgent: revising using red feedback"):
                    with suppress_stdout(not verbose):
                        bluex_agent.run_for_problem(
                            brain_path=brain_output_path,
                            system_path=TEMPLATE_PATHS["bluex"]["system"],
                            user_template_path=TEMPLATE_PATHS["bluex"]["user"],
                            full_report_path=blue_result_file,
                            red_report_path=red_result_file,
                            data_analysis_results_path=data_analysis_file,
                            output_dir=step6_dir
                        )
                bluex_result_file = step6_dir / "output.txt"
                if not bluex_result_file.exists():
                    legacy = step6_dir / "blue_results.txt"
                    if legacy.exists():
                        bluex_result_file = legacy
                status(f"      saved: {bluex_result_file}")

        # --- Step 7: Red (Final Review) ---
        step7_dir = problem_output_dir / "07_red_review"
        final_review_file = step7_dir / "output.txt"
        
        if final_review_file.exists():
            status(f"[Skip] Red final review already exists: {final_review_file}")
        else:
            legacy = step7_dir / "red_results.txt"
            if legacy.exists():
                final_review_file = legacy
                status(f"[Skip] Red final review already exists (legacy): {final_review_file}")
            else:
                if red_agent is None:
                    with suppress_stdout(not verbose):
                        red_agent = RedAgent()
                with progress_step("[7/7] RedAgent: final review"):
                    with suppress_stdout(not verbose):
                        red_agent.run_for_problem(
                            brain_path=brain_output_path,
                            system_path=TEMPLATE_PATHS["red"]["system"],
                            user_template_path=TEMPLATE_PATHS["red"]["user"],
                            blue_report_path=bluex_result_file,
                            output_dir=step7_dir
                        )
                final_review_file = step7_dir / "output.txt"
                if not final_review_file.exists():
                    legacy = step7_dir / "red_results.txt"
                    if legacy.exists():
                        final_review_file = legacy
                status(f"      saved: {final_review_file}")

        # --- Step 8: Answer (Final Deliverable) ---
        step8_dir = problem_output_dir / "08_answer"
        answer_output_file = step8_dir / "output.txt"
        
        if answer_output_file.exists():
            status(f"[Skip] Answer output already exists: {answer_output_file}")
        else:
            if answer_agent is None:
                with suppress_stdout(not verbose):
                    answer_agent = AnswerAgent()
            with progress_step("[8/8] AnswerAgent: composing final deliverable"):
                with suppress_stdout(not verbose):
                    answer_agent.run_for_problem(
                        brain_path=brain_output_path,
                        system_path=TEMPLATE_PATHS["answer"]["system"],
                        user_template_path=TEMPLATE_PATHS["answer"]["user"],
                        search_output_path=search_result_file,
                        completed_answer_path=bluex_result_file,
                        red_review_path=final_review_file,
                        output_dir=step8_dir,
                    )
            answer_output_file = step8_dir / "output.txt"
            status(f"      saved: {answer_output_file}")

        status(f"[Done] Artifacts stored in: {problem_output_dir}")

        # --- Write Final Answer File ---
        # problems/problem_X/answer_{id}.txt  (e.g., problem_1 -> answer_1.txt)
        answer_id = problem_id
        if answer_id.lower().startswith("problem_"):
            answer_id = answer_id[len("problem_"):]
        if not answer_id:
            answer_id = problem_id

        final_answer_path = problem_output_dir / f"answer_{answer_id}.txt"
        if answer_output_file.exists():
            shutil.copy2(str(answer_output_file), str(final_answer_path))
        else:
            # Fallback: keep previous behavior if agent output is missing
            with open(final_answer_path, "w", encoding="utf-8") as f:
                f.write("Error: AnswerAgent output not found.\n")

        status(f"[Success] Final answer saved: {final_answer_path}")
        status(f"[Total] {file_name} finished in {(_time.time() - pipeline_start):.1f}s")

    except Exception as e:
        status(f"[Error] Pipeline failed for {file_name}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        _current_problem.reset(token)

def main():
    parser = argparse.ArgumentParser(description="Run the AI Bio LLM pipeline.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full agent outputs (disables stdout suppression and enables INFO logging).",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        default=None,
        help=(
            "Run only specific problem(s). Accepts problem stem (e.g., problem_1), "
            "filename (problem_1.txt), number (1), or an explicit path."
        ),
    )
    parser.add_argument(
        "--problem-dir",
        type=str,
        default="problems",
        help="Directory containing problem files (default: 'problems').",
    )
    args = parser.parse_args()
    
    # Configure logging
    # Logging goes to stderr (like status messages) so it's visible even when stdout is suppressed
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,  # Use stderr to match status() output behavior
        force=True  # Override any existing configuration
    )
    
    if args.verbose:
        status("Verbose mode enabled: INFO-level logging active")
    
    # Set INPUT_DIR from CLI argument (local variable)
    input_dir = args.problem_dir
    
    # Set dummy file location now that INPUT_DIR is known (update global)
    global DUMMY_DATA_ANALYSIS
    DUMMY_DATA_ANALYSIS = Path(input_dir) / "dummy_data_analysis.txt"

    # Ensure dummy data file exists for agents
    if not DUMMY_DATA_ANALYSIS.exists():
        DUMMY_DATA_ANALYSIS.parent.mkdir(parents=True, exist_ok=True)
        with open(DUMMY_DATA_ANALYSIS, "w") as f:
             f.write("N/A: No specific data analysis was requested.")
             
    # Look for problem_*.txt in subdirectories (problems/problem_X/problem_X.txt)
    # Using recursive glob pattern
    pattern = os.path.join(input_dir, "**", "problem_*.txt")
    txt_files = glob.glob(pattern, recursive=True)
    
    if not txt_files:
        status(f"No files matching 'problem_*.txt' found in {input_dir} and its subdirectories")
        return

    # Optional filtering to run only specific problems
    if args.only:
        want: set[str] = set()
        want_paths: set[str] = set()

        for item in args.only:
            item = str(item).strip().strip("\"'")
            if not item:
                continue

            # If it looks like a path, keep it as a path candidate
            if any(sep in item for sep in ("/", "\\", ":")):
                want_paths.add(os.path.normpath(item))
                # Also allow passing just ".../problem_1.txt" and matching by stem
                base = os.path.basename(item)
                stem = os.path.splitext(base)[0]
                if stem:
                    want.add(stem)
                continue

            # If number like "1" -> "problem_1"
            if item.isdigit():
                want.add(f"problem_{item}")
                continue

            # If "problem_1.txt" -> "problem_1"
            if item.lower().endswith(".txt"):
                want.add(os.path.splitext(item)[0])
                continue

            # Otherwise treat as stem, e.g. "problem_1"
            want.add(item)

        filtered: list[str] = []
        for p in txt_files:
            norm_p = os.path.normpath(p)
            stem = os.path.splitext(os.path.basename(p))[0]

            if norm_p in want_paths:
                filtered.append(p)
                continue

            if stem in want:
                filtered.append(p)
                continue

        # Preserve original discovery order (glob order) while de-duping
        seen = set()
        txt_files = [p for p in filtered if not (p in seen or seen.add(p))]

        if not txt_files:
            status(f"No matching problems for --only={args.only}")
            status("Available candidates:")
            for p in sorted(glob.glob(pattern, recursive=True)):
                status(f"  - {os.path.splitext(os.path.basename(p))[0]} ({p})")
            return

    status(f"Found {len(txt_files)} files to process: {[os.path.basename(f) for f in txt_files]}")
    
    # Process problems (parallel by default when there are multiple files)
    if len(txt_files) <= 1:
        for file_path in txt_files:
            run_pipeline(file_path, verbose=args.verbose)
        return

    cpu_count = os.cpu_count() or 1
    if len(txt_files) > cpu_count:
        max_workers = max(1, cpu_count // 2)
    else:
        max_workers = len(txt_files)

    status(f"Running in parallel: jobs={max_workers}")

    failures = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(run_pipeline, file_path, verbose=args.verbose): file_path
            for file_path in txt_files
        }

        for future in as_completed(future_to_path):
            file_path = future_to_path[future]
            try:
                future.result()
            except Exception as e:
                failures += 1
                status(f"[Error] Unhandled exception for {os.path.basename(file_path)}: {type(e).__name__}: {e}")

    if failures:
        status(f"Completed with failures: {failures}/{len(txt_files)}")

if __name__ == "__main__":
    main()
