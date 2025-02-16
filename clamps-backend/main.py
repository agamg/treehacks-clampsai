import json
import os
import fastapi
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import uvicorn
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import random
import time
import requests
import asyncio

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# # Retrieve API key from environment
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# if not OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY not found in environment variables")

app = fastapi.FastAPI()
# oai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

from groq import Groq

oai_client = Groq(
    # This is the default and can be omitted
    api_key="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",
)


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


def returnfunc(messages):
    return messages["content"]



def query_video(query: str):
    data = {
        "query": query
    }
    response = requests.post(
        "http://localhost:5002/query",
        headers={"Content-Type": "application/json"},
        json=data
    )
    print(response.json())
    return response.json()


@app.post("/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest) -> StreamingResponse:
    logging.info(f"Received request: {request}")
    oai_request = request.dict(exclude_none=True)
    if "user_id" in oai_request:
        oai_request["user"] = oai_request.pop("user_id")
    oai_request["model"] = "llama-3.3-70b-versatile"


    #message[-1] ---> gemini ---> get
    



    


    print("querying right now", oai_request["messages"][-1]["content"])
    chat_completion_coroutine_raw = query_video(oai_request["messages"][-1]["content"])
    print("HERE IT IS", chat_completion_coroutine_raw)
    chat_completion_coroutine = chat_completion_coroutine_raw["response"]

    #expose ngrok server for gemini to receive and send back string content 


    async def event_stream():
        try:
            async for chunk in chat_completion_coroutine:
                # Convert the ChatCompletionChunk to a dictionary before JSON serialization
                chunk_dict = chunk.model_dump()
                yield f"data: {json.dumps(chunk_dict)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error("An error occurred: %s", str(e))
            yield f"data: {json.dumps({'error': 'Internal error occurred!'})}\n\n"


    
    async def event_stream1():
            # Emulate streaming response chunks
            response_text = chat_completion_coroutine
            words = response_text.split()
            
            for i, word in enumerate(words):
                chunk = {
                    "id": f"chatcmpl-{i}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "llama-3.3-70b-versatile",
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": word + " "
                        },
                        "finish_reason": None if i < len(words) - 1 else "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream1(), media_type="text/event-stream")

        
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8013)


