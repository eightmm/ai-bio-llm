# Bio LLM Agent System (Brain Agent)

This project implements a "Brain" agent for a multi-agent biological analysis system. It uses an LLM (via OpenRouter) to analyze complex biological questions and generate a structured execution plan.

## Project Structure

- **`agent.py`**: Core logic for the Brain Agent.
  - Handles OpenRouter API communication.
  - Includes retry logic for rate limits.
  - Defines the system prompt for the "Chief Architect" role.
- **`models.py`**: Pydantic data models.
  - Defines the input (`BioQuestionRequest`) and rich output schema (`BrainAnalysisResponse`).
- **`main.py`**: FastAPI application.
  - Exposes the `/analyze` endpoint.
- **`solve_problem.py`**: Client script.
  - Sends a specific IL-11 Pulmonary Fibrosis problem to the API for testing.
- **`requirements.txt`**: Python dependencies.
- **`.env`**: Configuration (API Keys).

## Setup & Usage

1.  **Environment Setup**:
    ```bash
    micromamba create -n bio-agent python=3.10 -y
    micromamba activate bio-agent
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Ensure your `.env` file has the correct `OPENROUTER_API_KEY`.

3.  **Run the Server**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

4.  **Run the Analysis**:
    ```bash
    python solve_problem.py
    ```

## Output Format
The agent returns a JSON object containing:
- **Summary**: Korean summary of the problem.
- **Key Entities**: Genes, proteins, etc.
- **Execution Plan**: Step-by-step tasks for other agents.
- **Search Strategy**: Keywords and databases.
