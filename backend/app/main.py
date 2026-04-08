import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.routes import analyze, generate_questions, evaluate_answer


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.info("Starting AI Hiring Readiness Simulator")
    yield
    logging.info("Shutting down AI Hiring Readiness Simulator")


app = FastAPI(
    title="AI Hiring Readiness & Technical Interview Simulator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(generate_questions.router, prefix="/api/v1", tags=["interview"])
app.include_router(evaluate_answer.router, prefix="/api/v1", tags=["evaluation"])


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "service": "ai-hiring-simulator"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)