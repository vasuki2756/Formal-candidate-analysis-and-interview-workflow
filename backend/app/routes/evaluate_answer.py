import logging
import os

from fastapi import APIRouter, HTTPException

from app.agents.evaluation_agent import EvaluationAgent
from app.models.schemas import EvaluateAnswerRequest, EvaluateAnswerResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluate-answer", response_model=EvaluateAnswerResponse)
async def evaluate_answer(req: EvaluateAnswerRequest) -> EvaluateAnswerResponse:
    try:
        logger.info("Evaluating answer")
        
        api_key = os.getenv("GROQ_API_KEY")
        agent = EvaluationAgent(api_key)
        
        result = agent.evaluate(req.question, req.answer)
        
        return EvaluateAnswerResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        message = str(e).lower()
        if "429" in message or "rate limit" in message or "rate_limit_exceeded" in message:
            raise HTTPException(
                status_code=429,
                detail="LLM rate limit reached. Please try again later or reduce request size.",
            )
        raise HTTPException(status_code=500, detail=str(e))