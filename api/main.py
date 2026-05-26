"""
Portfolio API - Visitor Tracker + Gemini CV Chat
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
import os
import requests
import base64
from google import genai

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── GEMINI SETUP ───
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ─── CV CONTEXT ───
CV_CONTEXT = """
You are an AI assistant embedded in Amirul Arif's personal portfolio website.
Your job is to answer questions about Amirul's experience, skills, and background
based on his CV below. Be concise, friendly, and professional.
If asked about something not in the CV, say you don't have that info but suggest
the visitor contact Amirul directly.

=== AMIRUL ARIF'S CV ===

Name: Mohamad Amirul 'Arif bin Tajul Hasnan
Location: Cyberjaya, Selangor, Malaysia
Email: amirularif9577@gmail.com
LinkedIn: https://www.linkedin.com/in/amirul-arif-49994b155/
GitHub: https://github.com/polzai77

PROFESSIONAL SUMMARY:
Experienced Infrastructure Specialist with over 5 years of expertise as a Linux Administrator.
Proficient in deploying and managing Linux-based systems, installing and configuring hardware
in data centers including servers and network switches. Skilled in software installation for
both physical and virtual machines. Passionate about continuous learning and emerging technologies.

EXPERIENCE:

1. Dell Technologies — Senior Analyst, OS Engineering (L3)
   March 2025 – Present | Cyberjaya, On-site
   Roles:
   - Provide next-level escalation support for Linux & Windows environments, including on-call standby for Major Incident Management (MIM)
   - Execute OS and application (process-level) CTASKs to ensure system stability and performance
   - Integrate and enhance existing internal tools to align with company standards, incorporating automation practices
   
   Official Projects:
   - Patchy-Porter: Automated kernel CVE scope-list generation and patch validation pipeline with cycle-based tracking, integrated with GitLab & OLAM for automated artifact retrieval
   - Mass Matter: Agent deployment automation pipeline featuring server filtering for both OS types, environment-based deployment targeting, ECN email generator, MECM deployment status tracking (Windows), agent classification, and Windows & Linux agent dashboards embedded into Grafana
   - CHG-A-BOT: Common CTASKs Automation (Expand Capacity / Mount Validation)
   
   Self-Initiated Projects:
   - MCM (Multi Connection Manager): Centralised role-based web platform for server operations featuring Windows RDP, LAPS Password Retrieval (WinRM), Linux Multi-SSH Terminal, Get Root Password (vCenter API), SCP Browser, iDRAC Query, Redfish API Explorer, PowerCLI, Root Access Audit, PCI Server Console, Mount Activity Checker, VM Disk Add & Expand, Access Control Manager, Usage Analytics, User Command Tracking
   - AskMyServer (Dell Hackathon): AI-powered natural language server diagnostics platform built on MCP (Model Context Protocol) architecture. Adopted by team, senior consultant, and manager. Backend uses Dell GenAI Gateway with dual-model routing (GPT-Powerful-120B and LLaMA 3.3-70B). Reduced server diagnostic time to under a minute.
   
   Achievements:
   - Oracle DB Server CPU & RAM Resizing: Resolved kernel panic, reclaimed 1,956 CPUs & 15.6 TB RAM, ~USD 312K cost savings
   - Top performer for MCM adoption and Grafana Agent Dashboard deployment

2. Dell Technologies — Analyst, IT Technical Services (Linux & Windows)
   April 2022 – March 2025 | 3 years | Hybrid
   - Supported 30,000+ Linux servers and 25,000+ Windows servers
   - Incident Management, Change Support, Major Incident Management (MIM)
   - Developed automation scripts via Bi-Frost in-house tool
   - Supported Major Data Center Maintenance, Power Maintenance, Black Friday readiness
   Achievements:
   - GICC Bi-Frost Tools: Interactive Console Linux web console for zero-touch remote access
   - FY24Q2: 29% incident reduction across COE Server team
   - Consistently Top 3 performer FY24 & FY25 for incident resolution

3. Velo Technologies & Nebula Systems — System Engineer
   May 2020 – April 2022 | 2 years | On-site
   Velo Technologies:
   - IT infrastructure support for desktops, networks, security, basic data center operations
   - User support, IT asset management, vendor coordination, help desk
   Nebula Systems:
   - Server & network administration: Windows Server, Linux (Ubuntu, CentOS, Debian), VMware ESXi
   - Network OS: Cisco IOS, PFSense, OPNSense, FSOS, HP ArubaOS
   - Open-source solutions: Zabbix, LibreNMS, OpenNebula, VyOS, oVirt, Netbox
   - Data center hands-on: servers, networking equipment, structured cabling
   - P2V and V2V migrations using Veeam and vCenter Converter

4. Stardocs Sdn Bhd — System Programmer & Support
   November 2019 – January 2020 | Contract
   - Managed in-house systems, Solimar Software, antivirus, printers, PCs, servers
   - Pre & post-sales technical support

5. Ministry of Health Malaysia — Administrative & IT Officer Grade N41
   January 2019 – October 2019 | Contract
   - IT troubleshooting, hardware/software support, vendor coordination

6. Pacific Engineering Sdn Bhd — Intern R&D Engineer
   June 2017 – September 2017
   - Developed Arduino-based controller to monitor industrial machinery

SKILLS:
Software:
- Linux: RHEL, OL, Debian, Ubuntu, SUSE, CentOS
- Scripting: PowerShell, Bash, Python
- Automation: Kubernetes (limited), Ansible, OLAM
- Virtualisation: VMware vCenter/vSphere/ESXi, Proxmox, oVirt, OpenNebula
- Monitoring: LibreNMS, Zabbix, Grafana
- Ticketing: Zammad, ServiceNow
- Database: MariaDB, MySQL, PostgreSQL
- Web Development: React.js, FastAPI, Python, WebSocket, nginx
- AI/MCP: Model Context Protocol, LLM integration, GenAI

Hardware:
- Dell PowerEdge, HP ProLiant
- RAID configuration, iDRAC, iLO
- P2V/V2V migration using Veeam

Networking:
- Cisco IOS, PFSense, OPNSense, HP ArubaOS, FSOS, Netbox

CERTIFICATIONS:
- Site Reliability Engineering (SRE) Foundation Certification
- Red Hat System Administration I (RH124)
- Introduction to Windows PowerShell 5.1
- Windows PowerShell: IT Management

EDUCATION:
- Bachelor's Degree in Computer & Communication Engineering — National University of Malaysia (UKM), 2014-2018
- Matriculation in Physics (Module 2) — Penang Matriculation College, 2013-2014

CONTACT:
- Email: amirularif9577@gmail.com
- LinkedIn: https://www.linkedin.com/in/amirul-arif-49994b155/
- GitHub: https://github.com/polzai77
- Portfolio: https://polzai77.github.io/portfolio/
"""

JD_MATCH_PROMPT = """
You are a professional HR analyst and technical recruiter. 
A visitor has pasted a Job Description and wants to know how well 
Amirul Arif's profile matches it.

Analyze the JD against Amirul's CV and provide:
1. Overall match percentage (be realistic and honest)
2. Strong matches (✅) — skills/experience that clearly match
3. Partial matches (⚠️) — some overlap but not perfect
4. Gaps (❌) — requirements not found in CV
5. A short honest recommendation

Format it clearly with emojis and sections.
Keep it concise but thorough.

=== AMIRUL'S CV ===
{cv}

=== JOB DESCRIPTION ===
{jd}
"""

# ─── GITHUB STORAGE (existing) ───
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "polzai77/portfolio")
DATA_FILE_PATH = "visitor_data.json"


def get_github_file():
    if not GITHUB_TOKEN:
        return {"total_visits": 0, "unique_visitors": [], "visits": []}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            file_content = base64.b64decode(content["content"]).decode()
            return json.loads(file_content)
        return {"total_visits": 0, "unique_visitors": [], "visits": []}
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        return {"total_visits": 0, "unique_visitors": [], "visits": []}


def save_to_github(data):
    if not GITHUB_TOKEN:
        return False
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
        payload = {"message": f"Update visitor stats - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "content": content}
        if sha:
            payload["sha"] = sha
        response = requests.put(url, headers=headers, json=payload)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error saving to GitHub: {e}")
        return False


# ─── CHAT REQUEST MODEL ───
class ChatRequest(BaseModel):
    message: str
    is_jd_match: bool = False


# ─── EXISTING ENDPOINTS ───
@app.get("/api")
async def root():
    return {
        "message": "Portfolio API",
        "status": "running",
        "endpoints": {
            "/api/track": "Track a new visit (POST)",
            "/api/stats": "Get visitor statistics (GET)",
            "/api/chat": "Chat with CV / JD match (POST)"
        }
    }


@app.post("/api/track")
async def track_visit(request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    data = get_github_file()
    visit_record = {"timestamp": datetime.now().isoformat(), "ip": client_ip, "user_agent": user_agent}
    data["visits"].append(visit_record)
    data["total_visits"] += 1
    if client_ip not in data["unique_visitors"]:
        data["unique_visitors"].append(client_ip)
    save_to_github(data)
    return {"success": True, "total_visits": data["total_visits"], "unique_visitors": len(data["unique_visitors"])}


@app.get("/api/stats")
async def get_stats():
    data = get_github_file()
    total_visits = data["total_visits"]
    unique_visitors = len(data["unique_visitors"])
    recent_visits = data["visits"][-50:] if data["visits"] else []
    today = datetime.now().date().isoformat()
    visits_today = sum(1 for v in data["visits"] if v["timestamp"].startswith(today))
    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "visits_today": visits_today,
        "visits": data["visits"],
        "recent_visits": recent_visits
    }


# ─── CHAT ENDPOINT ───
@app.post("/api/chat")
async def chat_with_cv(req: ChatRequest):
    if not gemini_client:
        return {"reply": "AI chat is not configured yet. Please contact Amirul directly at amirularif9577@gmail.com"}

    try:
        if req.is_jd_match:
            prompt = JD_MATCH_PROMPT.format(cv=CV_CONTEXT, jd=req.message)
        else:
            prompt = f"{CV_CONTEXT}\n\n=== VISITOR QUESTION ===\n{req.message}"

        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return {"reply": response.text}

    except Exception as e:
        print(f"Gemini error: {e}")
        return {"reply": "Sorry, I'm having trouble connecting right now. Please try again or contact Amirul directly at amirularif9577@gmail.com"}