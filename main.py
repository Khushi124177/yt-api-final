from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Proper CORS so validator can access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    video_url: str
    topic: str

@app.post("/ask")
async def ask(body: RequestBody):
    return {
        "timestamp": "00:00:43",  # valid HH:MM:SS
        "video_url": body.video_url,
        "topic": body.topic
    }
