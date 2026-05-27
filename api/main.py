"""
Portfolio API - Visitor Tracker (Supabase) + Gemini CV Chat (with Groq fallback)
"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import requests
from google import genai

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── SUPABASE SETUP ───
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://snocuimyqckoxwwkspwt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # anon/service_role key from env

def supa_headers():
    # Supports both legacy (service_role JWT) and new (sb_secret_*) key formats
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
        "x-supabase-api-key": SUPABASE_KEY   # new key format fallback
    }

def supa_insert(ip: str, user_agent: str):
    """Insert a visit row into Supabase."""
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/visits",
        headers=supa_headers(),
        json={"ip": ip, "user_agent": user_agent, "timestamp": datetime.utcnow().isoformat()}
    )
    r.raise_for_status()

def supa_get_all():
    """Fetch all visits ordered by timestamp desc."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/visits?select=*&order=timestamp.desc",
        headers=supa_headers()
    )
    r.raise_for_status()
    return r.json()  # list of dicts

def supa_delete_by_ip(ip: str):
    """Delete all visits for a given IP."""
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/visits?ip=eq.{ip}",
        headers={**supa_headers(), "Prefer": "return=minimal"}
    )
    r.raise_for_status()
    return r.status_code


# ─── GEMINI SETUP ───
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ─── GROQ SETUP (fallback) ───
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def call_groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise Exception("Groq API key not configured")
    for model in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.7},
                timeout=30
            )
            data = response.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq model {model} failed: {e}")
            continue
    raise Exception("All Groq models failed")


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
Phone: +601124005710
Email: amirularif9577@gmail.com
LinkedIn: https://www.linkedin.com/in/amirul-arif-49994b155/
GitHub: https://github.com/polzai77
Portfolio: https://polzai77.github.io/portfolio/

PROFESSIONAL SUMMARY:
Experienced Infrastructure Specialist with 7+ years across Linux administration,
data center operations, and infrastructure automation. Proficient in managing
Linux-based systems at enterprise scale, driving automation initiatives that
reduce operational toil, and building AI-powered internal tools adopted in
production. Passionate about continuous learning and staying up to date with
emerging technologies to enhance skills and drive innovation.

EXPERIENCE:

1. Dell Technologies (Dell IT)— Senior Analyst, OS Engineering (L3)
   March 2025 – Present | Cyberjaya, On-site
   Roles:
   - Provide next-level escalation support for Linux & Windows environments, including on-call standby for Major Incident Management (MIM)
   - Execute OS and application (process-level) CTASKs to ensure system stability and performance
   - Integrate and enhance existing internal tools to align with company standards, incorporating automation practices to replace legacy manual methods

   Official Projects:
   - Patchy-Porter: Automated kernel CVE scope-list generation and patch validation pipeline with cycle-based tracking, integrated with GitLab & OLAM for automated artifact retrieval
   - Mass Matter: Agent deployment automation pipeline featuring server filtering for both OS types, environment-based deployment targeting, ECN email generator, MECM deployment status tracking (Windows), agent classification, and Windows & Linux agent dashboards embedded into Grafana covering agent version compliance, server health, TO tracking, and owner data enrichment. Historical data tracking included.
   - CHG-A-BOT: Common CTASKs Automation (e.g. Expand Capacity / Mount Validation)

   Self-Initiated Projects:
   - MCM (Multi Connection Manager): Centralised role-based web platform for server operations
   - AskMyServer (Dell Hackathon): AI-powered natural language server diagnostics platform on MCP architecture. Adopted by team, senior consultant, and manager for day-to-day operations.

   Achievements:
   - Oracle DB Server CPU & RAM Resizing: Reclaimed 1,956 CPUs & 15.6 TB of RAM, ~USD 312K in cost savings
   - Multi Connection Manager: Bigger audience, simplifies bulk operations
   - Grafana Agent Dashboard: Agent status across supported servers

2. Dell Technologies — Analyst, IT Technical Services (Linux & Windows)
   April 2022 – March 2025 | 3 years | Hybrid
   - Supported 30,000+ Linux servers and 25,000+ Windows servers
   - 29% incident reduction via automation
   - Top 3 performer FY24 & FY25

3. Velo Technologies & Nebula Systems — System Engineer
   May 2020 – April 2022 | On-site
   - Server & Network Administration: Windows Server, Linux, VMware ESXi, Cisco IOS, PFSense, OPNSense, FSOS, HP ArubaOS
   - Open-Source: Zabbix, LibreNMS, OpenNebula, VyOS, oVirt, Netbox
   - P2V and V2V migrations using Veeam and vCenter Converter

4. Stardocs Sdn Bhd — System Programmer & Support (Contract, Nov 2019 – Jan 2020)
5. Ministry of Health Malaysia (KKM) — Administrative & IT Officer Grade N41 (Contract, Jan 2019 – Oct 2019)
6. Pacific Engineering Sdn Bhd — Intern R&D Engineer (Jun 2017 – Sep 2017)

SKILLS:
Software: Linux (RHEL, OL, Debian, Ubuntu, SUSE, CentOS), PowerShell, Bash, Python, Ansible, OLAM, Kubernetes (limited), VMware vCenter/vSphere/ESXi, Proxmox, oVirt, Zabbix, LibreNMS, Grafana, Zammad, ServiceNow, MariaDB, MySQL, PostgreSQL, React.js, FastAPI, WebSocket, nginx, MCP, LLM integration

Hardware: Dell PowerEdge, HP ProLiant, RAID, iDRAC, iLO, P2V/V2V (Veeam, vCenter Converter)

Networking: Cisco IOS, PFSense, OPNSense, FSOS, HP ArubaOS, Netbox, VyOS

CERTIFICATIONS:
- SRE Foundation Certification
- Red Hat System Administration I (RH124)
- Introduction to Windows PowerShell 5.1
- Windows PowerShell: IT Management

EDUCATION:
- Bachelor's Degree in Computer & Communication Engineering — UKM, 2014-2018
- Matriculation in Physics — Penang Matriculation College, 2013-2014
"""

JD_MATCH_PROMPT = """
You are a brutally honest senior technical recruiter with 15+ years of experience.
A visitor has pasted a Job Description and wants to know how well Amirul Arif's profile matches it.

CRITICAL RULES FOR SCORING:
- A skill being "listed" on a CV does NOT mean expertise. Dig into context and depth.
- If a skill appears once in a short role 3+ years ago, it's NOT a strong match — mark it partial or gap.
- Primary job titles and day-to-day responsibilities matter MORE than one-off mentions.
- If the JD requires X as a PRIMARY skill but Amirul only used it occasionally, mark it partial (⚠️) not strong (✅).
- Be realistic about years of experience depth — 6 months of exposure ≠ 3 years of hands-on.
- If the JD's core focus is fundamentally different from Amirul's core expertise, reflect that in the score.
- Don't inflate scores to be nice. A 60% match should be scored 60%, not 75%.

Amirul's CORE strengths: Linux/OS administration at scale, infrastructure automation (Python, Bash, Ansible), building internal web platforms, Incident Management, VMware/virtualisation.
Amirul's SECONDARY skills: Networking (Cisco, PFSense, ArubaOS) — Nebula 2020-2022 only; Windows server — supporting role; Database — basic usage; Kubernetes — limited explicitly stated.

Analyze the JD and provide:
1. Overall match percentage (brutally honest)
2. Strong matches (✅) — genuine depth only
3. Partial matches (⚠️) — has but not at required depth
4. Gaps (❌) — missing or too shallow
5. Short honest recommendation — good fit or not? What role WOULD suit him better?

Format clearly with emojis. Be concise but thorough.

=== AMIRUL'S CV ===
{cv}

=== JOB DESCRIPTION ===
{jd}
"""


# ─── CHAT REQUEST MODEL ───
class ChatRequest(BaseModel):
    message: str
    is_jd_match: bool = False


# ─── ENDPOINTS ───

@app.get("/api")
async def root():
    return {
        "message": "Portfolio API",
        "status": "running",
        "endpoints": {
            "/api/track": "Track a new visit (POST)",
            "/api/stats": "Get visitor statistics (GET)",
            "/api/chat": "Chat with CV / JD match (POST)",
            "/api/visits/delete": "Delete visits by IP (DELETE) ?ip=x.x.x.x"
        }
    }


@app.post("/api/track")
async def track_visit(request: Request):
    ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    user_agent = request.headers.get("user-agent", "Unknown")
    try:
        supa_insert(ip, user_agent)
    except Exception as e:
        print(f"Supabase insert error: {e}")
        return {"success": False, "error": str(e)}
    return {"success": True}


@app.get("/api/stats")
async def get_stats():
    try:
        visits = supa_get_all()
    except Exception as e:
        print(f"Supabase fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    total_visits = len(visits)
    unique_ips = list({v["ip"] for v in visits})
    unique_visitors = len(unique_ips)

    today = datetime.utcnow().date().isoformat()
    visits_today = sum(1 for v in visits if v["timestamp"].startswith(today))

    recent_visits = visits[:50]  # already ordered desc from Supabase

    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "unique_ips": unique_ips,
        "visits_today": visits_today,
        "visits": visits,
        "recent_visits": recent_visits
    }


@app.delete("/api/visits/delete")
async def delete_visits_by_ip(ip: str = Query(..., description="IP address to delete")):
    """Delete all visit records for a given IP address."""
    try:
        supa_delete_by_ip(ip)
    except Exception as e:
        print(f"Supabase delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, "deleted_ip": ip, "message": f"All visits from {ip} have been removed."}


@app.post("/api/chat")
async def chat_with_cv(req: ChatRequest):
    if not GROQ_API_KEY and not gemini_client:
        return {"reply": "AI chat is not configured yet. Please contact Amirul directly at amirularif9577@gmail.com"}

    message = req.message
    if len(message) > 15000:
        message = message[:15000] + "\n\n[Content truncated for length...]"

    if req.is_jd_match:
        prompt = JD_MATCH_PROMPT.format(cv=CV_CONTEXT, jd=message)
    else:
        prompt = f"{CV_CONTEXT}\n\n=== VISITOR QUESTION ===\n{message}"

    if GROQ_API_KEY:
        try:
            reply = call_groq(prompt)
            return {"reply": reply, "model": "groq"}
        except Exception as e:
            print(f"Groq failed, trying Gemini fallback: {e}")

    if gemini_client:
        try:
            response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return {"reply": response.text, "model": "gemini"}
        except Exception as e:
            print(f"Gemini also failed: {e}")

    return {"reply": "Sorry, I'm having trouble connecting right now. Please try again or contact Amirul directly at amirularif9577@gmail.com"}


@app.get("/api/ping")
async def ping():
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
