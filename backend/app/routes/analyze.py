import logging
import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agents.analysis_agent import AnalysisAgent
from app.agents.rag_agent import RAGAgent
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, RAGStatusResponse
from app.utils.file_parser import extract_text_from_file

logger = logging.getLogger(__name__)

router = APIRouter()

_rag_instance = None


def get_rag() -> RAGAgent:
    global _rag_instance
    if _rag_instance is None:
        api_key = os.getenv("GROQ_API_KEY")
        _rag_instance = RAGAgent(api_key)
    return _rag_instance


@router.get("/rag/status", response_model=RAGStatusResponse)
async def rag_status() -> RAGStatusResponse:
    """Check RAG status and stored data"""
    rag = get_rag()
    embedding_size = 0
    if rag.embeddings and len(rag.embeddings) > 0:
        embedding_size = len(rag.embeddings[0].tolist())
    return RAGStatusResponse(
        has_data=len(rag.chunks) > 0,
        num_chunks=len(rag.chunks),
        chunks=rag.chunks[:5] if rag.chunks else [],
        sample_embedding_size=embedding_size
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        logger.info("Starting analysis")
        
        if not req.resume:
            raise HTTPException(status_code=400, detail="Resume text is required")
        
        resume_text = req.resume
        
        rag = get_rag()
        
        if req.company_data:
            rag.load_company_data(req.company_data)
            company_context = rag.get_context_string("role requirements company culture")
            logger.info(f"RAG: Loaded {len(rag.chunks)} chunks, retrieved context: {len(company_context)} chars")
        else:
            company_context = ""
        
        api_key = os.getenv("GROQ_API_KEY")
        analyzer = AnalysisAgent(api_key)
        
        result = analyzer.analyze(resume_text, req.job_description, company_context)
        
        return AnalyzeResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        message = str(e).lower()
        if "429" in message or "rate limit" in message or "rate_limit_exceeded" in message:
            raise HTTPException(
                status_code=429,
                detail="LLM rate limit reached. Please try again later or reduce request size.",
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/file", response_model=AnalyzeResponse)
async def analyze_with_file(
    job_description: str = File(..., min_length=10),
    company_data: str = File(default=""),
    resume: UploadFile = File(...)
) -> AnalyzeResponse:
    try:
        logger.info("Starting analysis with file upload")
        
        text = extract_text_from_file(resume.file, resume.filename)
        
        if not text or len(text) < 10:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        rag = get_rag()
        
        if company_data:
            rag.load_company_data(company_data)
            company_context = rag.get_context_string("role requirements company culture")
            logger.info(f"RAG: Loaded {len(rag.chunks)} chunks")
        else:
            company_context = ""
        
        api_key = os.getenv("GROQ_API_KEY")
        analyzer = AnalysisAgent(api_key)
        
        result = analyzer.analyze(text, job_description, company_context)
        
        return AnalyzeResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        message = str(e).lower()
        if "429" in message or "rate limit" in message or "rate_limit_exceeded" in message:
            raise HTTPException(
                status_code=429,
                detail="LLM rate limit reached. Please try again later or reduce request size.",
            )
        raise HTTPException(status_code=500, detail=str(e))