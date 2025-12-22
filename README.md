# AI Bio LLM (Multi-Agent Pipeline)

This project is a multi-agent pipeline orchestrated by `main.py` to solve complex biology/bioinformatics problems.  
For each input problem, it runs a fixed sequence of agents and stores artifacts in **numbered step directories** under the problem folder (e.g., `problems/problem_1/`).

For a Korean translation, see [docs/README.ko.md](docs/README.ko.md).

---

## How it runs

### Input file discovery
`main.py` searches for problem files matching:
- `problems/**/problem_*.txt`
  - Example: `problems/problem_1/problem_1.txt`

### Run the pipeline

```bash
python main.py
```

### Run only specific problems

```bash
python main.py --only 1
python main.py --only problem_2
python main.py --only problems/problem_3/problem_3.txt
```

### Verbose mode
By default, most agent stdout is suppressed and only step progress + saved paths are shown. To print full agent logs:

```bash
python main.py --verbose
```

---

## Pipeline steps (execution order)

For each `problem_*.txt`, `main.py` runs the following steps:

### 01) Brain (`01_brain/`)
- **Agent**: `BrainAgent`
- **Output**: `01_brain/brain_decomposition.json`
- **Purpose**: Produce structured context from the raw problem text for downstream agents

### 02) Search (`02_search/`)
- **Agent**: `SearchAgent`
- **Input**: `01_brain/brain_decomposition.json`
- **Standard artifacts**:
  - `02_search/system_prompt.md`
  - `02_search/user_prompt.txt`
  - `02_search/output.txt`
- **Purpose**: Produce knowledge/literature synthesis (may include references)

### 03) Data Analysis (`03_data_analysis/`)
- **Agent**: `DataAnalystAgent`
- **Input**: `01_brain/brain_decomposition.json`
- **Outputs (always)**:
  - `03_data_analysis/data_analysis_results.txt` *(always written for downstream use, even on skip/failure)*
  - Optional: `03_data_analysis/data_analysis.md` or `03_data_analysis/data_analysis.json`
- **Purpose**: Resolve and summarize local data files (CSV/TSV/etc.) under the problem directory
- **Data Resolution Strategy**:
  - **Stage 1**: LLM-based extraction from problem text (primary method)
  - **Stage 2**: Regex-based pattern matching (fallback method)
  - Combines both methods to maximize file discovery

### 04) Blue Draft (`04_blue_draft/`)
- **Agent**: `BlueAgent`
- **Inputs**: Search output + data analysis summary
- **Standard artifacts**:
  - `04_blue_draft/system_prompt.md`
  - `04_blue_draft/user_prompt.txt`
  - `04_blue_draft/output.txt`
- **Purpose**: Produce an initial answer that matches the problem’s required format/numbering

### 05) Red Critique (`05_red_critique/`)
- **Agent**: `RedAgent`
- **Input**: Blue draft
- **Standard artifacts**:
  - `05_red_critique/system_prompt.md`
  - `05_red_critique/user_prompt.txt`
  - `05_red_critique/output.txt`
- **Purpose**: Provide a critical review of the draft (gaps, risks, missing requirements)

### 06) BlueX Revision (`06_bluex_revision/`)
- **Agent**: `BlueXAgent`
- **Inputs**: Blue draft + red critique + data analysis summary
- **Standard artifacts**:
  - `06_bluex_revision/system_prompt.md`
  - `06_bluex_revision/user_prompt.txt`
  - `06_bluex_revision/output.txt`
- **Purpose**: Revise the answer using red critique feedback

### 07) Red Review (`07_red_review/`)
- **Agent**: `RedAgent`
- **Input**: BlueX output
- **Standard artifacts**:
  - `07_red_review/system_prompt.md`
  - `07_red_review/user_prompt.txt`
  - `07_red_review/output.txt`
- **Purpose**: Final review including **Reliability Score (0–100)** and critiques/limitations/risks

### 08) Answer (`08_answer/`)
- **Agent**: `AnswerAgent`
- **Inputs**:
  - Problem text (from Brain JSON)
  - Search output (may contain references)
  - BlueX answer
  - Final red review (reliability score + critiques)
- **Standard artifacts**:
  - `08_answer/system_prompt.md`
  - `08_answer/user_prompt.txt`
  - `08_answer/output.txt`
- **Purpose**: Compose the final deliverable:
  - preserve the problem’s required format
  - append the red review section
  - add in-text citations + a **References** section if Search output contains references

---

## Final output file
`main.py` writes a final answer file into the problem directory:
- `answer_*.txt` (e.g., `problem_1.txt` → `answer_1.txt`)

The contents are copied from `08_answer/output.txt`.

---

## Environment variables (.env)
Create `.env` in the project root:

```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional model overrides
MODEL_BRAIN=google/gemini-2.5-flash
MODEL_SEARCH=google/gemini-2.5-flash
MODEL_BLUE=google/gemini-2.5-flash
MODEL_BLUEX=google/gemini-2.5-flash
MODEL_RED=google/gemini-2.5-flash
```

---

## Install (micromamba/conda + pip)

```bash
pip install -r requirements.txt
```

---

## Notes
- Each step stores `system_prompt.md`, `user_prompt.txt`, and `output.txt` so you can trace exactly what was prompted and what was generated.

---

## Latest run timings (sample)
Below are the timings from a recent run of `micromamba run -n bio-agent python main.py` (parallel execution).  
Times will vary depending on model choice, rate limits, network, and data availability.

| Problem | Total (s) | Brain | Search | Data | Blue | Red critique | BlueX | Red review | Answer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `problem_1.txt` | 371.1 | 7.6 | 159.7 | 64.4 | 24.3 | 29.9 | 25.1 | 39.3 | 20.7 |
| `problem_2.txt` | 446.2 | 18.8 | 262.5 | 0.0 | 27.0 | 39.2 | 30.8 | 39.5 | 28.3 |
| `problem_3.txt` | 343.9 | 8.0 | 195.9 | 0.0 | 21.0 | 40.7 | 22.0 | 32.0 | 24.2 |
| `problem_4.txt` | 327.6 | 11.6 | 195.4 | 0.0 | 22.3 | 28.7 | 25.8 | 28.1 | 15.6 |
| `problem_5.txt` | 282.2 | 7.4 | 154.8 | 0.0 | 17.8 | 33.9 | 17.8 | 25.9 | 24.5 |

---

## License
[MIT License](LICENSE)
