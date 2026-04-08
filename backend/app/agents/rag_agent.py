import json
import logging
import os
import re
import hashlib
from typing import Any

import numpy as np
import requests
from dotenv import load_dotenv

from app.core.llm import call_llm

load_dotenv()

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Preprocessing: Clean and normalize text"""
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?@\-]', '', text)
    text = text.strip()
    
    return text


def is_valid_url(text: str) -> bool:
    """Check if text is a URL"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text.strip()))


def fetch_webpage(url: str) -> str:
    """Fetch content from a company URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        text = clean_text(text)
        
        logger.info(f"Fetched {len(text)} characters from {url}")
        return text
        
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {str(e)}")
        return ""


class RAGAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.chunks: list[str] = []
        self.embeddings: list[np.ndarray] = []
        self.original_text: str = ""

    def _get_embedding(self, text: str) -> np.ndarray:
        # Local deterministic embedding keeps requests fast and avoids N LLM calls for large company pages.
        normalized = clean_text(text).lower()[:1500]
        if not normalized:
            return np.zeros(10)

        values = np.zeros(10, dtype=float)
        tokens = re.findall(r"\w+", normalized)

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(10):
                values[i] += (digest[i] / 255.0) * 2.0 - 1.0

        norm = np.linalg.norm(values)
        if norm == 0:
            return values
        return values / norm

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def load_company_data(self, company_input: str) -> None:
        """Load company data - can be URL or text"""
        self.original_text = company_input
        
        if is_valid_url(company_input):
            logger.info(f"Fetching company data from URL: {company_input}")
            company_text = fetch_webpage(company_input)
        else:
            company_text = clean_text(company_input)

        # Keep context concise so analyze requests stay responsive.
        company_text = company_text[:12000]
        
        self.chunks = self._chunk_text(company_text)[:8]
        self.embeddings = [self._get_embedding(chunk) for chunk in self.chunks]
        logger.info(f"Loaded {len(self.chunks)} chunks for RAG")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) <= chunk_size:
                current += " " + sentence
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence
        
        if current:
            chunks.append(current.strip())
        
        return chunks

    def get_relevant_context(self, query: str, top_k: int = 3) -> list[str]:
        if not self.chunks:
            return []
        
        query_emb = self._get_embedding(query)
        similarities = [
            self._cosine_similarity(query_emb, emb) 
            for emb in self.embeddings
        ]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.chunks[i] for i in top_indices]

    def get_context_string(self, query: str, top_k: int = 3) -> str:
        relevant = self.get_relevant_context(query, top_k)
        return "\n\n".join(relevant)