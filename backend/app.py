from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os, random
from groq import Groq  # Make sure you installed groq: pip install groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join("frontend", "index.html"))

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
users = {}  # username -> {"total_carbon_saved": float, "streak": int}
reminders = {}  # username -> list of {"habit": str, "frequency": str, "enabled": True}
challenges = [
    {"title": "Use public transport", "description": "Take bus/train instead of car today", "carbon_value": 2.5},
    {"title": "Plant a tree", "description": "Plant a tree in your area", "carbon_value": 5},
    {"title": "Recycle waste", "description": "Separate recyclables from trash", "carbon_value": 1.5}
]

# ---------------- Chat Endpoint ----------------
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an eco-friendly sustainability coach."},
                {"role": "user", "content": req.message}
            ],
            temperature=0.7
        )
        reply_text = completion.choices[0].message.content
    except Exception as e:
        print("Groq error:", e)
        reply_text = "🌱 Sorry, I couldn't process that. Try again!"
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
    return users.get(username, {"total_carbon_saved": 0, "streak": 0})

@app.get("/leaderboard")
def leaderboard():
    sorted_users = sorted(users.items(), key=lambda x: x[1]["total_carbon_saved"], reverse=True)
    return [{"username": u[0], "total_carbon_saved": u[1]["total_carbon_saved"]} for u in sorted_users]

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
