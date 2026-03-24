from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import json
import asyncio

# --- 💾 Database Setup ---
def init_db():
    with sqlite3.connect('workers.db') as conn:
        # टेबल स्ट्रक्चरमध्ये सुसूत्रता आणली आहे
        conn.execute('''CREATE TABLE IF NOT EXISTS locations 
                     (worker_id TEXT, latitude REAL, longitude REAL, timestamp TEXT, task TEXT)''')
        conn.commit()

init_db()

app = FastAPI(title="GPS Worker Tracking")

# --- 🛡️ CORS Middleware (हे वर असणे आवश्यक आहे) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🚀 Root Health Check ---
@app.get("/")
async def home():
    return {"message": "Server is running 🚀"}

# --- 📡 WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self): # __init__ सुधारले आहे
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                continue 

manager = ConnectionManager()

# --- 💾 State Management ---
workers: Dict[str, Dict[str, Any]] = {}

class GPSUpdate(BaseModel):
    worker_id: str
    latitude: float
    longitude: float
    task: str = ""

# --- 🛠️ Helper Database Functions ---
def _save_location_sync(worker_id: str, lat: float, lon: float, task: str, timestamp: str):
    with sqlite3.connect('workers.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO locations VALUES (?, ?, ?, ?, ?)", 
                  (worker_id, lat, lon, timestamp, task))
        conn.commit()

def _get_work_time_sync(worker_id: str) -> float:
    today = datetime.now().date().isoformat()
    with sqlite3.connect('workers.db') as conn:
        c = conn.cursor()
        c.execute(
            "SELECT timestamp FROM locations WHERE worker_id = ? AND timestamp >= ? ORDER BY timestamp ASC",
            (worker_id, today)
        )
        rows = c.fetchall()

    if len(rows) < 2:
        return 0.0

    start = datetime.fromisoformat(rows[0][0])
    end = datetime.fromisoformat(rows[-1][0])
    return round((end - start).total_seconds() / 3600, 2)

# --- 📍 API Endpoints ---

@app.post("/update-location")
async def update_location(update: GPSUpdate):
    now = datetime.now()
    timestamp_iso = now.isoformat()

    # वर्कर अ‍ॅक्टिव्ह आहे का ते तपासा (५ मिनिटांच्या आतील अपडेट)
    status = "active"
    if update.worker_id in workers:
        last_time = datetime.fromisoformat(workers[update.worker_id]['last_update'])
        if (now - last_time) > timedelta(minutes=5):
            status = "passive"

    workers[update.worker_id] = {
        "lat": update.latitude,
        "lon": update.longitude,
        "last_update": timestamp_iso,
        "task": update.task,
        "status": status
    }

    # डेटाबेसमध्ये बॅकग्राउंडला सेव्ह करा
    await asyncio.to_thread(
        _save_location_sync,
        update.worker_id,
        update.latitude,
        update.longitude,
        update.task,
        timestamp_iso
    )

    # सर्व कनेक्टेड ॲडमिनला अपडेट पाठवा
    await manager.broadcast({"workers": workers, "timestamp": timestamp_iso})

    return {"status": "updated", "worker_status": status}

@app.get("/workers")
async def get_workers():
    now = datetime.now()
    result_workers = workers.copy()
    
    active_count = 0
    passive_count = 0

    for w_id, data in result_workers.items():
        last_update = datetime.fromisoformat(data['last_update'])
        if (now - last_update) < timedelta(minutes=5):
            active_count += 1
        else:
            passive_count += 1
            result_workers[w_id]["status"] = "passive"

        # कामाचे तास मोजा
        result_workers[w_id]["work_hours"] = await asyncio.to_thread(_get_work_time_sync, w_id)

    return {
        "all_workers": result_workers,
        "active_count": active_count,
        "passive_count": passive_count
    }

@app.get("/get-history/{worker_id}")
async def get_worker_history(worker_id: str):
    def _fetch():
        with sqlite3.connect('workers.db') as conn:
            c = conn.cursor()
            c.execute(
                "SELECT latitude, longitude, timestamp, task FROM locations WHERE worker_id = ? ORDER BY timestamp DESC LIMIT 50",
                (worker_id,)
            )
            return [{"lat": r[0], "lon": r[1], "time": r[2], "task": r[3]} for r in c.fetchall()]

    history = await asyncio.to_thread(_fetch)
    return history

# --- 🔌 WebSockets Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)