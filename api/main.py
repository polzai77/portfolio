"""
Visitor Tracker API - Using GitHub as persistent storage
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os
import requests
import base64

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitHub Configuration (you'll need to set these as environment variables)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "polzai77/portfolio")  # format: username/repo
DATA_FILE_PATH = "visitor_data.json"  # Path in your repo

def get_github_file():
    """Fetch visitor data from GitHub"""
    if not GITHUB_TOKEN:
        # Fallback to empty data if no token configured
        return {
            "total_visits": 0,
            "unique_visitors": [],
            "visits": []
        }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            file_content = base64.b64decode(content["content"]).decode()
            return json.loads(file_content)
        else:
            # File doesn't exist yet
            return {
                "total_visits": 0,
                "unique_visitors": [],
                "visits": []
            }
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        return {
            "total_visits": 0,
            "unique_visitors": [],
            "visits": []
        }

def save_to_github(data):
    """Save visitor data to GitHub"""
    if not GITHUB_TOKEN:
        return False
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Get current file SHA (needed for updates)
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None
        
        # Encode data
        content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
        
        # Prepare commit
        payload = {
            "message": f"Update visitor stats - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content
        }
        
        if sha:
            payload["sha"] = sha
        
        # Push to GitHub
        response = requests.put(url, headers=headers, json=payload)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error saving to GitHub: {e}")
        return False

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
    
    # Load existing data from GitHub
    data = get_github_file()
    
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
    
    # Save to GitHub
    save_to_github(data)
    
    return {
        "success": True,
        "total_visits": data["total_visits"],
        "unique_visitors": len(data["unique_visitors"])
    }

@app.get("/api/stats")
async def get_stats():
    """Get visitor statistics"""
    data = get_github_file()
    
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