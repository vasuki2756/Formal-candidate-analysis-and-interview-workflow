import json
import logging
import re
from typing import Any

from app.core.llm import call_llm

logger = logging.getLogger(__name__)


def extract_json_from_response(text: str, expect_list: bool = False) -> Any:
    """Extract JSON from potentially messy LLM response"""
    text = text.strip()
    
    # Try direct parse first
    try:
        data = json.loads(text)
        if expect_list and isinstance(data, list):
            return data
        return data
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in code blocks
    if expect_list:
        # Look for array in code blocks
        json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text, re.IGNORECASE)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
    else:
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
    
    # Try to find array pattern
    if expect_list:
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
    
    raise ValueError("Could not extract valid JSON from response")


class InterviewAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def generate_questions(
        self,
        missing_skills: list[str],
        partial_skills: list[str],
        role: str,
        company_context: str = ""
    ) -> dict[str, Any]:
        skills_to_cover = missing_skills + partial_skills
        
        prompt = f"""Generate exactly 5 interview questions for the role of {role}.

SKILLS TO TEST: {', '.join(skills_to_cover[:10])}

COMPANY CONTEXT:
{company_context[:500]}

Requirements:
- 2 conceptual questions (testing understanding of concepts)
- 2 problem-solving questions (testing practical skills)
- 1 company-specific question (testing fit with company)

Return ONLY a JSON array of 5 objects, each with:
{{
  "question": "the question text",
  "type": "conceptual" | "problem_solving" | "company_specific",
  "skill_related": "the skill this tests"
}}

Return ONLY the JSON array, no other text. Do not include any explanations."""

        result = call_llm(prompt, self.api_key)

        if not result.get("success"):
            return {
                "success": False,
                "questions": [],
                "error": result.get("error") or "Failed to generate questions",
            }

        try:
            questions = extract_json_from_response(result["content"], expect_list=True)
            if isinstance(questions, list) and len(questions) == 5:
                return {"success": True, "questions": questions}
            elif isinstance(questions, list):
                # Return up to 5 questions
                return {"success": True, "questions": questions[:5]}
            return {
                "success": False,
                "questions": [],
                "error": "Model response did not contain a valid array of questions",
            }
        except Exception as e:
            logger.error(f"Failed to parse questions: {e}")
            return {
                "success": False,
                "questions": [],
                "error": "Model returned invalid JSON for questions",
            }