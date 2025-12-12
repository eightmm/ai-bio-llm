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
3.  **Output (`problems/json/`)**: Results are saved as a **single** flat JSON file for each problem (e.g., `01_problem_id.json`).

## 🛠 Directory Structure

```
ai-bio-llm/
├── main.py                 # Batch processing entry point
├── src/
│   ├── brain/              # Brain Agent logic (with system_prompt.md)
│   ├── literature/         # Literature Agent (New)
│   ├── blue/               # Blue Agent (Placeholder)
│   ├── red/                # Red Agent (Placeholder)
│   └── data_analizer/      # Data Analizer (Placeholder)
└── problems/
    ├── given/              # Input text files
    └── json/               # Output JSON results (Flat)
```

## 🚀 Usage

### 1. Prepare Input
Place your problem text files in `problems/given/`.

### 2. Run Batch Analysis
Execute the batch processor:
```bash
python main.py
```

### 3. Check Results
Go to `problems/json/` to see the generated JSON plans.
