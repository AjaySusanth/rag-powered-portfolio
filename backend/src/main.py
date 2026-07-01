"""
WHY THIS WAS CHOSEN:
This module initializes the FastAPI application. It registers CORS middleware to support
frontend interactions and mounts the chat router. Placing initialization in src/main.py
allows it to be imported and run easily by ASGI servers (like uvicorn).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat

app = FastAPI(
    title="RAG-Powered Developer Portfolio Backend",
    description="API for the RAG-powered developer portfolio chatbot.",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to portfolio domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Simple healthcheck endpoint."""
    return {"status": "healthy"}
