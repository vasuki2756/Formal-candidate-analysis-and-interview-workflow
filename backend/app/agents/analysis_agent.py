import json
import logging
import re
from typing import Any

from app.core.llm import call_llm

logger = logging.getLogger(__name__)


def extract_json_from_response(text: str) -> dict[str, Any]:
    """Extract JSON from potentially messy LLM response"""
    text = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in code blocks
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find any {...} pattern
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValueError("Could not extract valid JSON from response")


class AnalysisAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def analyze(self, resume: str, job_description: str, company_context: str = "") -> dict[str, Any]:
        prompt = f"""You are a hiring analyst. Analyze the candidate's readiness for the position.

RESUME:
{resume[:3000]}

JOB DESCRIPTION:
{job_description[:2000]}

COMPANY CONTEXT:
{company_context[:1000]}

Provide a JSON response with exactly this structure:
{{
  "candidate_skills": ["list of skills found in resume"],
  "required_skills": ["list of skills required from JD"],
  "matched_skills": ["skills that match exactly"],
  "partial_skills": ["skills with partial match"],
  "missing_skills": ["skills completely missing"],
  "readiness_score": "percentage (e.g., '75%')",
  "top_gaps": ["top 3 skill gaps"],
  "recommendations": ["3-5 actionable recommendations"]
}}

Be strict with JSON formatting. Only return the JSON object, no other text."""

        result = call_llm(prompt, self.api_key)

        if not result.get("success"):
            raise RuntimeError(result.get("error") or "LLM call failed during analysis")

        try:
            return extract_json_from_response(result["content"])
        except ValueError as e:
            logger.error(f"Failed to parse analysis: {e}")
            # Return fallback response instead of crashing
            return {
                "candidate_skills": [],
                "required_skills": [],
                "matched_skills": [],
                "partial_skills": [],
                "missing_skills": [],
                "readiness_score": "0%",
                "top_gaps": ["Could not analyze - please try again"],
                "recommendations": ["Check API key and try again"]
            }