from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    resume: Optional[str] = Field(default=None, min_length=10)
    job_description: str = Field(..., min_length=10)
    company_data: str = Field(default="")  # Can be URL or text


class AnalyzeResponse(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    readiness_score: str = "0%"
    top_gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class RAGStatusResponse(BaseModel):
    has_data: bool
    num_chunks: int
    chunks: list[str] = Field(default_factory=list)
    sample_embedding_size: int = 0


class GenerateQuestionsRequest(BaseModel):
    missing_skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    role: str = Field(..., min_length=2)
    company_context: str = Field(default="")


class QuestionItem(BaseModel):
    question: str
    type: str
    skill_related: str


class GenerateQuestionsResponse(BaseModel):
    questions: list[QuestionItem] = Field(default_factory=list)


class EvaluateAnswerRequest(BaseModel):
    question: str = Field(..., min_length=10)
    answer: str = Field(..., min_length=5)


class EvaluateAnswerResponse(BaseModel):
    score: str = "0"
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    follow_up: str = ""
    improvement: str = ""