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


class EvaluationAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def evaluate(self, question: str, answer: str) -> dict[str, Any]:
        prompt = f"""You are a technical interview evaluator. Evaluate the candidate's answer.

QUESTION:
{question[:2000]}

ANSWER:
{answer[:3000]}

Provide a JSON response with exactly this structure:
{{
  "score": "percentage score (e.g., '75%')",
  "strengths": ["list of strengths in the answer"],
  "weaknesses": ["list of weaknesses or gaps"],
  "follow_up": "suggested follow-up question to probe deeper",
  "improvement": "specific improvement suggestion"
}}

Be strict with JSON formatting. Only return the JSON object, no other text."""

        result = call_llm(prompt, self.api_key)

        if not result.get("success"):
            raise RuntimeError(result.get("error") or "LLM call failed during evaluation")

        try:
            return extract_json_from_response(result["content"])
        except ValueError as e:
            logger.error(f"Failed to parse evaluation: {e}")
            # Return fallback response
            return {
                "score": "0%",
                "strengths": [],
                "weaknesses": ["Could not evaluate - please try again"],
                "follow_up": "",
                "improvement": "Check API and try again"
            }