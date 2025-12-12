# Bio LLM Brain Agent

This project implements a "Brain" agent for a multi-agent biological analysis system. It uses an LLM (via OpenRouter) to analyze complex biological questions and generate a structured execution plan.

## Project Structure

- **`brain.py`**: Core logic for the Brain Agent (includes Agent, Models, and CLI).
- **`main.py`**: FastAPI application exposing the `/decompose` endpoint.
- **`problems/`**: Directory where analysis results are saved.
- **`requirements.txt`**: Python dependencies.

## Usage

### CLI
```bash
python brain.py input.txt
```

### API Service
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
