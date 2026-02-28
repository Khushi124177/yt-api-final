import os
import time
import uuid
import re
import yt_dlp
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS for validator
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class RequestBody(BaseModel):
    video_url: str
    topic: str

@app.post("/ask")
async def ask(body: RequestBody):

    filename = f"{uuid.uuid4()}.m4a"

    # Download full audio only (no ffmpeg conversion)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filename,
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([body.video_url])

    # Upload to Gemini Files API
    file = genai.upload_file(filename)

    # Wait until ACTIVE
    while file.state.name != "ACTIVE":
        time.sleep(2)
        file = genai.get_file(file.name)

    model = genai.GenerativeModel("gemini-1.5-pro")

    response = model.generate_content(
        [
            file,
            f"""
            The audio file contains a full YouTube video.

            Find the FIRST time the exact spoken phrase or topic below appears:

            "{body.topic}"

            Return ONLY the timestamp in strict HH:MM:SS format.
            Do not return anything else.
            """
        ],
        generation_config={"temperature": 0}
    )

    # Extract clean HH:MM:SS
    match = re.search(r"\d{2}:\d{2}:\d{2}", response.text)
    timestamp = match.group(0) if match else "00:00:00"

    os.remove(filename)

    return {
        "timestamp": timestamp,
        "video_url": body.video_url,
        "topic": body.topic
    }
