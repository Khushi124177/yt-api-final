import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class RequestBody(BaseModel):
    video_url: str
    topic: str

@app.post("/ask")
async def ask(body: RequestBody):
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = f"""
    Analyze this YouTube video:
    {body.video_url}

    Find when the topic "{body.topic}" is first spoken.

    Return ONLY timestamp in HH:MM:SS format.
    """

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0}
    )

    match = re.search(r"\d{2}:\d{2}:\d{2}", response.text)
    timestamp = match.group(0) if match else "00:00:00"

    return {
        "timestamp": timestamp,
        "video_url": body.video_url,
        "topic": body.topic
    }
