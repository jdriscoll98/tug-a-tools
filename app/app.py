from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Tuga Tools Rental")

# Serve the simple frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("app/static/index.html")

DB_PATH = "database.db"

# Database helpers

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database tables
conn = get_db()
cur = conn.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
    )""")
cur.execute(
    """CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            image TEXT
    )""")
cur.execute(
    """CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tool_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            status TEXT
    )""")
cur.execute(
    """CREATE TABLE IF NOT EXISTS damage_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            description TEXT,
            report_date TEXT
    )""")
cur.execute(
    """CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            msg_date TEXT
    )""")
conn.commit()
conn.close()

# Insert some sample tools if none exist
conn = get_db()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM tools")
count = cur.fetchone()[0]
if count == 0:
    sample_tools = [
        (1, "Hammer", "Heavy-duty hammer", "hammer.png"),
        (2, "Drill", "Cordless power drill", "drill.png"),
        (3, "Saw", "Electric jigsaw", "saw.png"),
    ]
    cur.executemany(
        "INSERT INTO tools (id, name, description, image) VALUES (?, ?, ?, ?)",
        sample_tools,
    )
    conn.commit()
conn.close()


# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Tool(BaseModel):
    id: int
    name: str
    description: str
    image: Optional[str] = None

class BookingCreate(BaseModel):
    tool_id: int
    start_date: str
    end_date: str

class Booking(BaseModel):
    id: int
    user_id: int
    tool_id: int
    start_date: str
    end_date: str
    status: str

class DamageReportCreate(BaseModel):
    booking_id: int
    description: str

class SupportMessageCreate(BaseModel):
    message: str

# Authentication helper

def get_current_user(x_token: Optional[str] = Header(None)):
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing X-Token header")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (x_token,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return row["id"]

# Routes

@app.post("/register")
def register(user: UserCreate):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    conn.close()
    return {"message": "User registered"}

@app.post("/login")
def login(user: UserLogin):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user.username, user.password))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # For simplicity token is username
    return {"token": user.username}

@app.get("/tools", response_model=List[Tool])
def list_tools():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tools")
    rows = cur.fetchall()
    conn.close()
    return [Tool(id=row["id"], name=row["name"], description=row["description"], image=row["image"]) for row in rows]

@app.post("/tools")
def add_tool(tool: Tool):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tools (id, name, description, image) VALUES (?, ?, ?, ?)",
        (tool.id, tool.name, tool.description, tool.image),
    )
    conn.commit()
    conn.close()
    return {"message": "Tool added"}

@app.post("/bookings", response_model=Booking)
def create_booking(booking: BookingCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bookings (user_id, tool_id, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, booking.tool_id, booking.start_date, booking.end_date, "booked"),
    )
    booking_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    row = cur.fetchone()
    conn.close()
    return Booking(
        id=row["id"],
        user_id=row["user_id"],
        tool_id=row["tool_id"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        status=row["status"],
    )

@app.get("/bookings", response_model=List[Booking])
def list_bookings(user_id: int = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [
        Booking(
            id=row["id"],
            user_id=row["user_id"],
            tool_id=row["tool_id"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
        )
        for row in rows
    ]

@app.post("/payments")
def process_payment(amount: float, user_id: int = Depends(get_current_user)):
    # Placeholder for payment gateway integration
    return {"message": f"Processed payment of {amount} for user {user_id}"}

@app.post("/notifications")
def send_notification(message: str, user_id: int = Depends(get_current_user)):
    # Placeholder for push notification implementation
    print(f"Notification to {user_id}: {message}")
    return {"message": "Notification sent"}

@app.post("/damage-report")
def damage_report(report: DamageReportCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO damage_reports (booking_id, description, report_date) VALUES (?, ?, ?)",
        (report.booking_id, report.description, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"message": "Damage reported"}

@app.post("/support")
def support_message(msg: SupportMessageCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO support_messages (user_id, message, msg_date) VALUES (?, ?, ?)",
        (user_id, msg.message, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"message": "Support message received"}

