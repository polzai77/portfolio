"""
Visitor Tracker API - For Render.com
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, use your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use current directory for data file (Render.com persistent storage)
DATA_FILE = "visitor_data.json"

def load_data():
    """Load visitor data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "total_visits": 0,
        "unique_visitors": [],
        "visits": []
    }

def save_data(data):
    """Save visitor data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.get("/api")
async def root():
    """API info endpoint"""
    return {
        "message": "Visitor Tracker API",
        "status": "running",
        "endpoints": {
            "/api/track": "Track a new visit (POST)",
            "/api/stats": "Get visitor statistics (GET)"
        }
    }

@app.post("/api/track")
async def track_visit(request: Request):
    """Track a page visit"""
    # Get visitor info
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Load existing data
    data = load_data()
    
    # Record the visit
    visit_record = {
        "timestamp": datetime.now().isoformat(),
        "ip": client_ip,
        "user_agent": user_agent
    }
    
    data["visits"].append(visit_record)
    data["total_visits"] += 1
    
    # Track unique visitors by IP
    if client_ip not in data["unique_visitors"]:
        data["unique_visitors"].append(client_ip)
    
    # Save to file
    save_data(data)
    
    return {
        "success": True,
        "total_visits": data["total_visits"],
        "unique_visitors": len(data["unique_visitors"])
    }

@app.get("/api/stats")
async def get_stats():
    """Get visitor statistics"""
    data = load_data()
    
    # Calculate stats
    total_visits = data["total_visits"]
    unique_visitors = len(data["unique_visitors"])
    
    # Get recent visits (last 10)
    recent_visits = data["visits"][-10:] if data["visits"] else []
    
    # Count visits today
    today = datetime.now().date().isoformat()
    visits_today = sum(1 for v in data["visits"] if v["timestamp"].startswith(today))
    
    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "visits_today": visits_today,
        "recent_visits": recent_visits
    }