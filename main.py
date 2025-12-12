from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from brain import BrainAgent, ProblemDecompositionResponse
import uvicorn

app = FastAPI(title="Bio LLM Brain Agent", version="3.0")
agent = BrainAgent()

class BioQuestionRequest(BaseModel):
    question: str = Field(..., description="The raw biological problem text")

@app.post("/decompose", response_model=ProblemDecompositionResponse)
async def decompose_problem(request: BioQuestionRequest):
    try:
        result = agent.analyze_question(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
