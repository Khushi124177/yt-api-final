import os
import time
import uuid
import re
import yt_dlp
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

class RequestBody(BaseModel):
    video_url: str
    topic: str


@app.post("/ask")
async def ask(body: RequestBody):

    filename = f"{uuid.uuid4()}.webm"

    try:
        # 1️⃣ Download audio only
        ydl_opts = {
    "format": "bestaudio",
    "outtmpl": filename,
    "quiet": True,
}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([body.video_url])

        # 2️⃣ Upload to Gemini Files API
        file = genai.upload_file(filename)

        # 3️⃣ Wait until file is ACTIVE
        while file.state.name != "ACTIVE":
            time.sleep(2)
            file = genai.get_file(file.name)

        # 4️⃣ Ask Gemini
        model = genai.GenerativeModel("gemini-2.0-flash")

        response = model.generate_content(
            [
                file,
                f'Find when "{body.topic}" is first spoken. '
                'Return ONLY timestamp in HH:MM:SS format like 00:05:47.'
            ],
            generation_config={"temperature": 0}
        )

        # Extract only HH:MM:SS safely
        match = re.search(r"\d{2}:\d{2}:\d{2}", response.text)
        timestamp = match.group(0) if match else "00:00:00"

        return {
            "timestamp": timestamp,
            "video_url": body.video_url,
            "topic": body.topic
        }

    finally:
        # 5️⃣ Cleanup temp file
        if os.path.exists(filename):
            os.remove(filename)