from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv
import random
from datetime import date

# -------------------------------
# Load env
# -------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# -------------------------------
# App
# -------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# In-memory DB
# -------------------------------
users = {}
reminders = []
daily_challenge_cache = {"date": None, "challenge": None}

# -------------------------------
# Models
# -------------------------------
class ChatRequest(BaseModel):
    message: str
    username: str = "guest"

class CarbonRequest(BaseModel):
    username: str
    carbon_saved: float
    activity: str

class ReminderRequest(BaseModel):
    username: str
    habit: str
    frequency: str

# -------------------------------
# Challenges
# -------------------------------
challenges = [
    {"title": "Use Public Transport", "description": "Use bus or train today", "carbon_value": 5},
    {"title": "Plant a Tree", "description": "Plant one tree", "carbon_value": 10},
    {"title": "Save Water", "description": "Take a short shower", "carbon_value": 2},
    {"title": "No Plastic", "description": "Avoid plastic today", "carbon_value": 3},
]

# -------------------------------
# Root
# -------------------------------
@app.get("/")
def home():
    return {"status": "Eco Coach API running 🌱"}

# -------------------------------
# Chat
# -------------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful eco lifestyle coach."},
                {"role": "user", "content": req.message}
            ],
            temperature=0.7
        )
        reply = completion.choices[0].message.content
    except Exception:
        reply = "🌱 Reduce waste, save energy, protect nature!"

    return {"reply": reply, "carbon_saved": 0}

# -------------------------------
# Daily Challenge
# -------------------------------
@app.get("/challenge/daily")
def daily_challenge():
    today = str(date.today())
    if daily_challenge_cache["date"] != today:
        daily_challenge_cache["date"] = today
        daily_challenge_cache["challenge"] = random.choice(challenges)
    return daily_challenge_cache["challenge"]

# -------------------------------
# Carbon Log
# -------------------------------
@app.post("/carbon/log")
def log_carbon(req: CarbonRequest):
    if req.username not in users:
        users[req.username] = {"total": 0, "streak": 0}

    users[req.username]["total"] += req.carbon_saved
    users[req.username]["streak"] += 1

    return {"message": "Activity logged successfully"}

# -------------------------------
# User Stats
# -------------------------------
@app.get("/user/{username}")
def get_user(username: str):
    user = users.get(username, {"total": 0, "streak": 0})
    return {
        "username": username,
        "total_carbon_saved": user["total"],
        "streak": user["streak"]
    }

# -------------------------------
# Leaderboard
# -------------------------------
@app.get("/leaderboard")
def leaderboard():
    data = [{"username": u, "total_carbon_saved": v["total"]} for u, v in users.items()]
    return sorted(data, key=lambda x: x["total_carbon_saved"], reverse=True)

# -------------------------------
# Reminders
# -------------------------------
@app.post("/reminder/add")
def add_reminder(req: ReminderRequest):
    reminders.append({**req.dict(), "enabled": True})
    return {"message": "Reminder added"}

@app.get("/reminders/{username}")
def get_reminders(username: str):
    return [r for r in reminders if r["username"] == username]
