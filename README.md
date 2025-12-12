# AI Bio LLM Agent

This project implements an automated multi-agent AI pipeline for analyzing complex biological problems. It decomposes large scientific questions into manageable sub-problems, performs literature search, writes academic reports, and iteratively improves them through critical review.

## Architecture

The system operates in a sequential pipeline handled by `main.py`:

1.  **Brain Agent**: Analyzes the input problem (`.txt`) and decomposes it into sub-problems (`decomposition.json`).
2.  **Sub-problem Loop**: For each sub-problem, the following agents are executed in order:
    *   **Search Agent**: Searches for relevant literature and synthesizes information.
    *   **Blue Agent**: Drafts an initial academic report based on the search results.
    *   **Red Agent**: Critiques the drafted report from a scientific red-team perspective.
    *   **BlueX Agent**: Revises the report based on the Red Team's feedback.
    *   **Red Agent (Final Review)**: Provides a final assessment of the revised report.

## Directory Structure

- `src/`: Source code for all agents (`brain`, `blue`, `red`, `search`).
- `problems/given/`: Place your input problem text files (`.txt`) here.
- `problems/results/`: Final polished reports and reviews are saved here.
- `outputs/`: Intermediate artifacts for debugging and tracing (organized by problem ID and sub-problem).

## Setup & Usage

### 1. Environment Variables
Create a `.env` file in the root directory:
```bash
OPENROUTER_API_KEY=your_api_key_here
# Optional: Override default models
# MODEL_BRAIN=openai/gpt-4o
# MODEL_SEARCH=perplexity/llama-3-sonar-large-32k-online
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
(Or use your preferred package manager like `conda` or `micromamba`)

### 3. Run the Pipeline
Place your problem text file in `problems/given/`, then run:
```bash
python main.py
```

## Agents Configuration
All model configurations and API settings are centralized in `src/config.py`. You can adjust timeouts, retry logic, and default models there.

## License
[MIT License](LICENSE)
