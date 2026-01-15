from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import random
import requests

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Models ----------------
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

# ---------------- In-Memory DB ----------------
users = {}           # username -> {"total_carbon_saved": float, "streak": int}
reminders = {}       # username -> list of {"habit": str, "frequency": str, "enabled": True}
challenges = [
    {"title": "Use public transport", "description": "Take bus/train instead of car today", "carbon_value": 2.5},
    {"title": "Plant a tree", "description": "Plant a tree in your area", "carbon_value": 5},
    {"title": "Recycle waste", "description": "Separate recyclables from trash", "carbon_value": 1.5}
]

# ---------------- Chat Endpoint ----------------
@app.post("/chat")
def chat(req: ChatRequest):
    # Call Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        return {"reply": "Groq API key not set!"}

    try:
        response = requests.post(
            "https://api.groq.ai/v1/query",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"query": req.message}
        )
        reply_text = response.json().get("result", "I couldn't understand that.")
    except Exception as e:
        reply_text = "Server error. Try again later."

    return {"reply": reply_text}

# ---------------- Carbon Tracker ----------------
@app.post("/carbon/log")
def log_carbon(req: CarbonRequest):
    u = users.get(req.username, {"total_carbon_saved": 0, "streak": 0})
    u["total_carbon_saved"] += req.carbon_saved
    u["streak"] += 1
    users[req.username] = u
    return {"message": f"Activity logged! +{req.carbon_saved} kg CO2"}

@app.get("/user/{username}")
def get_user(username: str):
    u = users.get(username, {"total_carbon_saved": 0, "streak": 0})
    return u

@app.get("/leaderboard")
def leaderboard():
    sorted_users = sorted(users.items(), key=lambda x: x[1]["total_carbon_saved"], reverse=True)
    result = [{"username": u[0], "total_carbon_saved": u[1]["total_carbon_saved"]} for u in sorted_users]
    return result

# ---------------- Daily Challenge ----------------
@app.get("/challenge/daily")
def daily_challenge():
    return random.choice(challenges)

# ---------------- Reminders ----------------
@app.get("/reminders/{username}")
def get_reminders(username: str):
    return reminders.get(username, [])

@app.post("/reminder/add")
def add_reminder(req: ReminderRequest):
    if req.username not in reminders:
        reminders[req.username] = []
    reminders[req.username].append({"habit": req.habit, "frequency": req.frequency, "enabled": True})
    return {"message": "Reminder added!"}
