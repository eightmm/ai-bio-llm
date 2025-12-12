import os
import glob
import json
import concurrent.futures
import time
from src.brain.brain import BrainAgent

# Configuration
INPUT_DIR = "problems/given"
OUTPUT_BASE_DIR = "problems/chunked"
MAX_WORKERS = 3  # Adjust based on API rate limits/parallelism needs

def process_file(file_path):
    """
    Reads a file, analyzes it using BrainAgent, and saves the result.
    """
    file_name = os.path.basename(file_path)
    print(f"[{file_name}] Starting analysis...")
    
    try:
        # 1. Read input
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 2. Analyze
        agent = BrainAgent()
        result = agent.analyze_question(content)
        
        # 3. Create Output Directory
        problem_id = result.problem_id
        # Use problem_id, or fallback to filename if needed
        if not problem_id:
             problem_id = os.path.splitext(file_name)[0]
             
        output_dir = os.path.join(OUTPUT_BASE_DIR, problem_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # 4. Save Logic (Single vs Multiple)
        sub_problems = result.sub_problems
        
        # Condition: If atomic (1 sub-problem) and ID suggests single/atomic
        is_atomic = False
        if len(sub_problems) == 1:
            # Check if ID is expressly 'SINGLE' or just one item
            is_atomic = True
            
        if is_atomic:
            # Save as one consolidated file
            output_file = os.path.join(output_dir, "problem_analysis.json")
            data = {
                "original_problem_text": result.original_problem_text,
                "problem_id": result.problem_id,
                "main_problem_definition": result.main_problem_definition,
                "analysis": sub_problems[0].model_dump()
            }
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{file_name}] Saved SINGLE output to {output_file}")
            
        else:
            # Save split files
            print(f"[{file_name}] Saved {len(sub_problems)} sub-problems to {output_dir}")
            for sub in sub_problems:
                sub_data = {
                    "original_problem_text": result.original_problem_text,
                    "problem_id": result.problem_id,
                    "main_problem_definition": result.main_problem_definition,
                    "sub_problem": sub.model_dump()
                }
                
                safe_id = sub.id.replace("/", "_").replace("\\", "_")
                output_file = os.path.join(output_dir, f"sub_problem_{safe_id}.json")
                
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(sub_data, f, indent=2, ensure_ascii=False)

        return f"[{file_name}] Success"

    except Exception as e:
        error_msg = f"[{file_name}] Failed: {str(e)}"
        print(error_msg)
        return error_msg

def main():
    # Ensure directories exist
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    # Get list of files
    txt_files = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in {INPUT_DIR}")
        return

    print(f"Found {len(txt_files)} files to process in {INPUT_DIR}")
    print(f"Processing with {MAX_WORKERS} threads...")
    
    start_time = time.time()
    
    # Parallel Execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_file, f): f for f in txt_files}
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            # Results are printed inside process_file, but we can capture return vals here
            
    elapsed = time.time() - start_time
    print(f"\nBatch processing complete in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
