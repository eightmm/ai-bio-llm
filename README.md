# Bio LLM Brain Agent

This project implements a multi-agent biological analysis system. The core component is the **Brain Agent**, which analyzes complex biological problems and decomposes them into executable sub-tasks.

## 📂 System Architecture

The system operates as a **Batch Processing Pipeline**:

1.  **Input (`problems/given/`)**: Raw biological problems are stored here as `.txt` files.
2.  **Processing (`main.py`)**: The central script that:
    - Scans the input directory.
    - Runs in **parallel** (multi-threaded).
    - Calls `BrainAgent` (`src/brain/brain.py`) for analysis.
    - Intelligently determines if a problem is **Atomic** (single step) or **Complex** (needs decomposition).
3.  **Output (`problems/chunked/`)**: Results are saved as JSON files in a dedicated folder for each problem.
    - **Atomic Problems**: Saved as a single `problem_analysis.json`.
    - **Complex Problems**: Split into multiple files (e.g., `sub_problem_A.json`, `sub_problem_B.json`).

## 🛠 Directory Structure

```
ai-bio-llm/
├── main.py                 # Batch processing entry point
├── src/
│   ├── brain/              # Brain Agent logic (refactored)
│   ├── blue/               # Blue Agent (Placeholder)
│   ├── red/                # Red Agent (Placeholder)
│   └── data_analizer/      # Data Analizer (Placeholder)
└── problems/
    ├── given/              # Input text files (Split from total_example.txt)
    └── chunked/            # Output JSON results
```

## 🚀 Usage

### 1. Prepare Input
Place your problem text files in `problems/given/`.
(Note: `problems/total_example.txt` contains the raw dataset).

### 2. Run Batch Analysis
Execute the batch processor to analyze all files in parallel:
```bash
python main.py
```

### 3. Check Results
Go to `problems/chunked/` to see the generated JSON plans.
