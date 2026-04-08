import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required")
        self.client = Groq(api_key=self.api_key)

    def call_llm(self, prompt: str, response_schema: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"} if response_schema else None,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")

            return {"success": True, "content": content, "error": None}

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return {"success": False, "content": None, "error": str(e)}


def call_llm(prompt: str, api_key: str | None = None) -> dict[str, Any]:
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError("API key not provided. Set GROQ_API_KEY environment variable or pass api_key parameter.")
    
    client = LLMClient(api_key=api_key)
    return client.call_llm(prompt)


def parse_json_response(response: dict[str, Any], default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not response.get("success"):
        return default or {}
    
    try:
        return json.loads(response["content"])
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return default or {}