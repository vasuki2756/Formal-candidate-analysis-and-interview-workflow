import logging
import os

from fastapi import APIRouter, HTTPException

from app.agents.interview_agent import InterviewAgent
from app.models.schemas import GenerateQuestionsRequest, GenerateQuestionsResponse, QuestionItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(req: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    try:
        logger.info("Generating interview questions")
        
        api_key = os.getenv("GROQ_API_KEY")
        agent = InterviewAgent(api_key)
        
        result = agent.generate_questions(
            missing_skills=req.missing_skills,
            partial_skills=req.partial_skills,
            role=req.role,
            company_context=req.company_context
        )
        
        if not result.get("success"):
            error_message = str(result.get("error", "Failed to generate questions"))
            if "429" in error_message.lower() or "rate limit" in error_message.lower():
                raise HTTPException(
                    status_code=429,
                    detail="LLM rate limit reached. Please try again later.",
                )
            raise HTTPException(status_code=500, detail=error_message)
        
        questions = [QuestionItem(**q) for q in result["questions"]]
        return GenerateQuestionsResponse(questions=questions)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question generation failed: {str(e)}")
        if "429" in str(e).lower() or "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="LLM rate limit reached.")
        raise HTTPException(status_code=500, detail=str(e))