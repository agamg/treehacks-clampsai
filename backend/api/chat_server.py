"""FastAPI server for chat completion endpoints."""
import json
import os
import sys
import time
import logging
import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from config import Config
from groq import Groq

Config.validate()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

app = FastAPI()

# Initialize Groq client
groq_client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    user_id: Optional[str] = None


def query_video(query: str) -> dict:
    """Query the video service for context."""
    try:
        data = {"query": query}
        response = requests.post(
            f"http://localhost:{Config.VIDEO_SERVER_PORT}/query",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error querying video service: {e}")
        return {"response": ""}


@app.post("/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest) -> StreamingResponse:
    """Create a chat completion with video context."""
    logging.info(f"Received request: {request}")
    
    # Get video context
    user_message = request.messages[-1].content
    logging.info(f"Querying video service: {user_message}")
    
    try:
        video_response = query_video(user_message)
        video_context = video_response.get("response", "")
    except Exception as e:
        logging.error(f"Error querying video service: {e}")
        video_context = ""
    
    # Create streaming response
    async def event_stream():
        try:
            # Emulate streaming response chunks
            response_text = video_context or "I couldn't analyze the video at this time."
            words = response_text.split()
            
            for i, word in enumerate(words):
                chunk = {
                    "id": f"chatcmpl-{i}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": Config.GROQ_MODEL,
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": word + " "
                        },
                        "finish_reason": None if i < len(words) - 1 else "stop"
                    }]
                }}
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            yield f"data: {json.dumps({'error': 'Internal error occurred!'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.CHAT_SERVER_PORT)
