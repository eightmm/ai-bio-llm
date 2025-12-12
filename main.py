import os
import glob
import json
import time
import re
import shutil
from pathlib import Path

# Import Agents from src
from src.brain.brain import BrainAgent
from src.search.search_agent import SearchAgent
from src.blue.blue_agent import BlueAgent
from src.red.red_agent import RedAgent
from src.blue.bluex_agent import BlueXAgent

# Configuration
INPUT_DIR = "problems/given"
OUTPUT_BASE_DIR = "outputs"
FINAL_OUTPUT_BASE_DIR = "problems/results"
SRC_DIR = Path("src")

# Template Paths
TEMPLATE_PATHS = {
    "search": {
        "system": SRC_DIR / "search" / "search_system.md",
        "user": SRC_DIR / "search" / "search_user_template.md"
    },
    "blue": {
        "system": SRC_DIR / "blue" / "blue_system.md",
        "user": SRC_DIR / "blue" / "blue_user_template.md"
    },
    "red": {
        "system": SRC_DIR / "red" / "red_system.md",
        "user": SRC_DIR / "red" / "red_user_template.md"
    },
    "bluex": {
        "system": SRC_DIR / "blue" / "bluex_system.md",
        "user": SRC_DIR / "blue" / "bluex_user_template.md"
    }
}

DUMMY_DATA_ANALYSIS = Path("outputs/dummy_data_analysis.txt")

def ensure_dirs(problem_output_dir):
    for agent in ["brain", "search", "blue", "red", "bluex", "final_review"]:
        (problem_output_dir / agent).mkdir(parents=True, exist_ok=True)

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

def run_pipeline(file_path):
    file_name = os.path.basename(file_path)
    print(f"\n==================================================")
    print(f"[{file_name}] Starting Pipeline")
    print(f"==================================================")

    try:
        # 1. Read Input
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 2. Brain Phase
        print(f"[*] Brain Agent: Analyzing...")
        brain_agent = BrainAgent()
        brain_result = brain_agent.analyze_question(content)
        
        # Determine Problem ID & Directory
        problem_id = brain_result.problem_id
        if not problem_id:
            problem_id = os.path.splitext(file_name)[0]
        
        # Base Output Directory for this problem
        problem_output_dir = Path(OUTPUT_BASE_DIR) / problem_id
        problem_output_dir.mkdir(parents=True, exist_ok=True)

        # Save Brain Result (Global context)
        brain_output_path = problem_output_dir / "brain_decomposition.json"
        with open(brain_output_path, "w", encoding="utf-8") as f:
            f.write(brain_result.model_dump_json(indent=2))
        print(f"[*] Brain Analysis saved to {brain_output_path}")

        # Initialize Agents
        search_agent = SearchAgent()
        blue_agent = BlueAgent()
        red_agent = RedAgent()
        bluex_agent = BlueXAgent()

        # 3. Process each Sub-problem
        for i, sub in enumerate(brain_result.sub_problems, 1):
            sub_id = sub.id
            safe_sub_id = str(sub_id).replace("/", "_").replace("\\", "_")
            
            # Sub-problem Directory: outputs/{problem_id}/{sub_id}/
            # We group all steps for this sub-problem here
            sub_problem_dir = problem_output_dir / f"{safe_sub_id}"
            sub_problem_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n--- Processing Sub-problem {i}: {sub_id} ---")
            print(f"    Context Dir: {sub_problem_dir}")

            # Prepare Sub-problem JSON File (Step 0)
            # We save this in the sub-problem folder for easy reference
            sub_problem_input_file = sub_problem_dir / "00_problem_context.json"
            save_sub_problem_json(sub_problem_input_file, brain_result, sub)

            # --- Step 1: Search ---
            print(f"[1. Search] Searching literature...")
            step1_dir = sub_problem_dir / "01_search"
            search_agent.run_for_sub_problem(
                sub_problem_path=sub_problem_input_file,
                system_path=TEMPLATE_PATHS["search"]["system"],
                user_template_path=TEMPLATE_PATHS["search"]["user"],
                output_dir=step1_dir
            )
            # Find the result file (SearchAgent saves as results_{safe_id}.txt)
            search_result_file = step1_dir / f"results_{safe_sub_id}.txt"
            
            if not search_result_file.exists():
                print(f"[Error] Search result not found at {search_result_file}. Skipping.")
                continue

            # --- Step 2: Blue (Initial Draft) ---
            print(f"[2. Blue] Writing initial draft...")
            step2_dir = sub_problem_dir / "02_blue_draft"
            blue_agent.run_for_sub_problem(
                sub_problem_path=sub_problem_input_file,
                system_path=TEMPLATE_PATHS["blue"]["system"],
                user_template_path=TEMPLATE_PATHS["blue"]["user"],
                full_report_path=search_result_file,
                data_analysis_results_path=DUMMY_DATA_ANALYSIS,
                output_dir=step2_dir
            )
            blue_result_file = step2_dir / f"blue_results_{safe_sub_id}.txt"

            # --- Step 3: Red (Critique) ---
            print(f"[3. Red] Critiquing initial draft...")
            step3_dir = sub_problem_dir / "03_red_critique"
            red_agent.run_for_sub_problem(
                sub_problem_path=sub_problem_input_file,
                system_path=TEMPLATE_PATHS["red"]["system"],
                user_template_path=TEMPLATE_PATHS["red"]["user"],
                blue_report_path=blue_result_file,
                output_dir=step3_dir
            )
            red_result_file = step3_dir / f"red_results_{safe_sub_id}.txt"

            # --- Step 4: BlueX (Revision) ---
            print(f"[4. BlueX] Revising report...")
            step4_dir = sub_problem_dir / "04_bluex_revision"
            bluex_agent.run_for_sub_problem(
                sub_problem_path=sub_problem_input_file,
                system_path=TEMPLATE_PATHS["bluex"]["system"],
                user_template_path=TEMPLATE_PATHS["bluex"]["user"],
                full_report_path=blue_result_file,
                red_report_path=red_result_file,
                data_analysis_results_path=DUMMY_DATA_ANALYSIS,
                output_dir=step4_dir
            )
            # BlueX saves with same naming convention as BlueAgent
            bluex_result_file = step4_dir / f"blue_results_{safe_sub_id}.txt"

            # --- Step 5: Red (Final Review) ---
            print(f"[5. Red] Final review...")
            step5_dir = sub_problem_dir / "05_final_review"
            red_agent.run_for_sub_problem(
                sub_problem_path=sub_problem_input_file,
                system_path=TEMPLATE_PATHS["red"]["system"],
                user_template_path=TEMPLATE_PATHS["red"]["user"],
                blue_report_path=bluex_result_file,
                output_dir=step5_dir
            )
            final_review_file = step5_dir / f"red_results_{safe_sub_id}.txt"
            
            # --- Step 6: Save Final Results (Archiving) ---
            final_problems_dir = Path(FINAL_OUTPUT_BASE_DIR) / problem_id
            final_problems_dir.mkdir(parents=True, exist_ok=True)
            
            target_report = final_problems_dir / f"{safe_sub_id}_report.txt"
            target_review = final_problems_dir / f"{safe_sub_id}_review.txt"
            
            shutil.copy(bluex_result_file, target_report)
            shutil.copy(final_review_file, target_review)
            
            print(f"[Done] Sub-problem {sub_id} complete. Artifacts stored in {sub_problem_dir}")

        print(f"\n[Success] Pipeline finished for {file_name}")

    except Exception as e:
        print(f"[Error] Pipeline failed for {file_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    if not DUMMY_DATA_ANALYSIS.exists():
        # Ensure dummy file exists if not already created
        DUMMY_DATA_ANALYSIS.parent.mkdir(parents=True, exist_ok=True)
        with open(DUMMY_DATA_ANALYSIS, "w") as f:
             f.write("N/A: No specific data analysis was requested.")
             
    txt_files = glob.glob(os.path.join(INPUT_DIR, "*problem_1.txt"))
    if not txt_files:
        print(f"No .txt files found in {INPUT_DIR}")
        return

    print(f"Found {len(txt_files)} files to process.")
    
    # Process sequentially to avoid rate limits and confusion in logs
    for file_path in txt_files:
        run_pipeline(file_path)

if __name__ == "__main__":
    main()
