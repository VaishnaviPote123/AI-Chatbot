from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "Eco Coach AI (LLaMA) running 🌱"}


@app.post("/chat")
def chat(req: ChatRequest):
    prompt = f"""
You are an eco-friendly lifestyle coach.
Your job is to motivate people to live sustainably.
Give simple, positive, and actionable advice.

User: {req.message}
Eco Coach:
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful sustainability coach."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return {"reply": completion.choices[0].message.content}
