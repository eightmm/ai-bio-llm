import os
import glob
import json
import concurrent.futures
import time
import re
from src.brain.brain import BrainAgent

# Configuration
INPUT_DIR = "problems/given"
OUTPUT_BASE_DIR = "problems/json"
MAX_WORKERS = 3  # Adjust based on API rate limits

def process_file(file_path):
    """
    Reads a file, analyzes it using BrainAgent, and saves the result as a SINGLE JSON file.
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
        
        # 3. Determine Filename (Numbered)
        problem_id = result.problem_id
        if not problem_id:
             problem_id = os.path.splitext(file_name)[0]
             
        # Extract number from filename (e.g. problem_1.txt -> 1)
        match = re.search(r'\d+', file_name)
        if match:
            idx = match.group()
            prefix = f"{int(idx):02d}_"
            problem_id = prefix + problem_id

        # 4. Save as SINGLE JSON File in 'problems/json'
        output_file = os.path.join(OUTPUT_BASE_DIR, f"{problem_id}.json")
        
        data = {
            "original_problem_text": result.original_problem_text,
            "problem_id": result.problem_id,
            "main_problem_definition": result.main_problem_definition,
            "sub_problems": [sub.model_dump() for sub in result.sub_problems]
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"[{file_name}] Saved analysis to {output_file} ({len(result.sub_problems)} steps)")
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
            future.result()

    elapsed = time.time() - start_time
    print(f"\nBatch processing complete in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
