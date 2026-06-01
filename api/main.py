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
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def supa_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
        "x-supabase-api-key": SUPABASE_KEY
    }

def supa_insert(ip: str, user_agent: str):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/visits",
        headers=supa_headers(),
        json={"ip": ip, "user_agent": user_agent, "timestamp": datetime.utcnow().isoformat()}
    )
    r.raise_for_status()

def supa_get_all():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/visits?select=*&order=timestamp.desc",
        headers=supa_headers()
    )
    r.raise_for_status()
    return r.json()

def supa_delete_by_ip(ip: str):
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

def call_groq(prompt: str, is_jd: bool = False) -> str:
    if not GROQ_API_KEY:
        raise Exception("Groq API key not configured")
    # Use smarter model for JD matching, fast model for regular chat
    if is_jd:
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    else:
        models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models:
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
If asked about salary or compensation, DO NOT guess or make up numbers. Instead say:
"I don't have access to real-time salary data. For accurate figures, check Glassdoor, 
JobStreet, or LinkedIn for similar roles in Malaysia."

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

1. Dell Technologies (Dell IT) — Senior Analyst, OS Engineering (L3)
   March 2025 – Present | Cyberjaya, On-site
   - L3 escalation support for Linux & Windows INC queue; on-call standby for Major Incident Management (MIM) — when on-call during a P1/escalated P3 incident, participates in the MIM call and contributes to post-incident RCA
   - Execute OS and application (process-level) CTASKs to ensure system stability and performance
   - Integrate and enhance existing internal tools to align with company standards, incorporating automation to replace legacy manual methods
   - Drive modernisation of traditional manual workflows — identifying repetitive operational tasks and converting them into automated, scalable solutions (e.g. CHG-A-BOT replacing manual CTASKs, Mass Matter replacing manual agent deployment tracking, MCM replacing individual tool access with a centralised platform)

   Official Projects:
   - Patchy-Porter: Automated kernel CVE scope-list generation (Phase 1) covering all supported Linux servers for kernel/OS CVE patching cycles. Output used internally before vendor engagement. Patch validation pipeline with cycle-based tracking, integrated with GitLab & OLAM for automated artifact retrieval. Collaborated with university team for AI-driven Phase 2.
   - Mass Matter: Agent deployment automation pipeline covering 13-15 internal agents across the supported server fleet. Features: server filtering for both OS types, environment-based deployment targeting, ECN email generator (Ansible pipeline), MECM deployment status tracking (Windows), agent classification, Windows & Linux agent dashboards in Grafana (agent version compliance, server health, TO tracking, owner data enrichment, daily refresh from internal data). Historical data tracking included.
   - CHG-A-BOT: Common CTASKs automation (Expand Capacity, Mount Validation)

   Self-Initiated Projects:
   - MCM (Multi Connection Manager): Centralised role-based web platform for server operations, used daily by 3-10 people across patching team, security team, L1 technical support, IRE team, and L3 team.
     Windows: RDP Connections, LAPS Password Retrieval (WinRM), Windows Disk Expand & Search, File Share Browser (SMB)
     Linux: Multi-SSH Terminal (single & multi-server), Get Root Password (vCenter API with auto-login console), SCP Browser
     Misc: iDRAC Query, Redfish API Explorer, PowerCLI (vCenter), Root Access Audit (identifies unrotated root passwords across fleet; OLAM-based rotation for targeted servers — typically 5-20 servers per cycle out of 20,000+), PCI Server Console
     CHGTASK: Mount Activity Checker, Implementation Step Manager, Expand Capacity for multiple servers across multiple locations, Datastore/Compute migration
     Deployments (Mass Matter): Server Deployment Filtering, Agent Classification, ECN Email Generator, MECM Deployment Status Tracking, Historical Data, Custom Dashboard and Grafana Dashboard (linked)
     Admin: Access Control Manager (group & user-level permissions), Usage Analytics, User Command Tracking, Kickout Session, Feedback
   - AskMyServer (Dell Hackathon): Solely designed, architected, and developed an AI-powered natural language server diagnostics platform on MCP (Model Context Protocol) architecture. Selected as Top 15 finalist out of 90+ teams for Round 2 (Finals). Currently adopted by manager, OS Engineering counterpart, senior consultant, and hackathon team members for day-to-day operations.
     Target Users: Non-technical app/server owners — self-service diagnostics and vulnerability checks without CLI knowledge
     Backend: Dell GenAI Gateway — dual-model routing: GPT-Powerful-120B for complex queries & Zabbix graph generation, LLaMA 3.3-70B for live diagnostics and bulk server queries
     MCP Tool Servers: Linux SSH (multi-server), Windows WinRM, OS Info/Inventory API, Zabbix MCP (prod & nonprod)
     Frontend: Open WebUI with tool server integration, served via nginx SSL termination
     Infrastructure: Podman + systemd deployment
     Impact: Reduced server diagnostic time to under a minute; adopted for production use

   Achievements:
   - Oracle DB Server CPU & RAM Resizing: Partnered with OS Engineering counterpart and collaborated with a DB Engineer to resolve a kernel panic issue triggered during resource reduction. Successfully reclaimed 1,956 CPUs & 15.6 TB RAM — ~USD 312K cost savings.
   - AskMyServer Hackathon: Selected as Top 15 finalist out of 90+ teams — advanced to Round 2 Finals. Result TBC.
   - Multi Connection Manager: Used daily by 3-10 people across multiple teams; simplifies bulk operations at scale
   - Grafana Agent Dashboard: Production dashboards showing agent deployment status, server health, trending, and history

2. Dell Technologies — Analyst, IT Technical Services (Linux & Windows)
   April 2022 – March 2025 | 3 years | Hybrid
   - Provided in-depth support for 30,000+ Linux servers and 25,000+ Windows servers
   - Incident Management: Resolved INC queue for Linux & Windows Ops; participated in MIM for recovery and RCA (ITIL Incident, Change, Problem Management practices)
   - Change support: Executed CTASKs from Change Coordinator; assisted deployment team with custom PowerShell scripts to remediate failed SCCM installations
   - Developed Multi-SSH feature backlog item via in-house tool Bi-Frost; then built own full-scale tool MCM (Multi Connection Manager) with bulk operations including multi-server capacity expansion, datastore/compute migration, ECN email automation, MECM reporting, server filtering, and custom + Grafana dashboards
   - Supported critical activities: Major Data Center Maintenance, Power Maintenance, Black Friday readiness
   Achievements:
   - GICC Bi-Frost Interactive Console Linux: Web console for zero-touch remote connections
   - FY24Q2: 29% incident reduction across COE Server team
   - Top 3 performer FY24 & FY25 for resolving user incidents and task creation

3. Velo Technologies & Nebula Systems — System Engineer
   May 2020 – April 2022 | 2 years | On-site

   Roles for Velo Technologies:
   - IT infrastructure support for desktops, networks, security, and data center operations
   - First-level user support, IT asset management, vendor coordination
   - Maintained IT inventory and accurate asset tracking

   Roles for Nebula Systems:
   - Server & Network Administration: Windows Server, Linux (Ubuntu, CentOS, Debian), VMware ESXi (installed and configured from scratch — bare metal to production), vCenter (managed vCenter environment — VM provisioning, snapshots, resource pools, migrations for customer environments), Cisco IOS, PFSense, OPNSense, FSOS, HP ArubaOS
   - Virtualisation: Created, configured, and managed VMs for customer environments using VMware ESXi and vCenter. Performed P2V and V2V migrations using Veeam and vCenter Converter.
   - Open-Source Solutions: Deployed and configured Zabbix from scratch (dashboards, alerts, proactive monitoring of physical and virtual infrastructure). LibreNMS for network device monitoring and topology discovery. OpenNebula — installed from scratch and migrated production workloads from vCenter to OpenNebula for a real client environment. oVirt — evaluated as a vCenter replacement (lab/testing only; OpenNebula was chosen instead). VyOS — tested as a cost-saving routing solution but had roadblocks; not deployed in production. Netbox for IPAM and asset tracking.
   - System Documentation: Used Netbox as single source of truth — server inventory, IPAM, rack layouts, network device configurations, structured cabling documentation. Maintained daily activity reports, system change logs, incident resolution records.
   - Data Center Operations: Installed and maintained physical servers (Dell PowerEdge, HP ProLiant), networking equipment, and structured cabling in in-house and customer-owned data centers.

4. Stardocs Sdn Bhd — System Programmer & Support
   November 2019 – January 2020 | Contract | Subang
   - Managed in-house systems, pre/post-sales technical support, IT consulting

5. Ministry of Health Malaysia (KKM) — Administrative & IT Officer Grade N41
   January 2019 – October 2019 | Contract | Putrajaya
   - IT troubleshooting, vendor coordination, documentation, record-keeping

6. Pacific Engineering Sdn Bhd — Intern R&D Engineer
   June 2017 – September 2017
   - Developed Arduino-based controller to monitor industrial machinery

SKILLS:
Software:
- Linux: RHEL, OL, Debian, Ubuntu, SUSE, CentOS — L3 escalation support for 30,000+ servers at Dell; hands-on OS deployment and maintenance at Nebula
- Scripting: PowerShell (certified; 25,000+ Windows servers at Dell — custom scripts for SCCM remediation, bulk ops), Bash (automation via Bi-Frost), Python (multithreaded bulk ops processing 1000+ servers simultaneously; FastAPI backends; widely used by patching, security, L1, IRE, and L3 teams via MCM)
- Automation: Ansible (Patchy-Porter CVE pipeline; Mass Matter agent deployment; OLAM-based root password rotation in MCM; ECN email automation pipeline), OLAM (Oracle Linux Automation Manager), CHG-A-BOT, Mass Matter, Patchy-Porter
- Virtualisation: VMware ESXi (installed from scratch at Nebula), vCenter (managed — VM provisioning, snapshots, resource pools, migrations; vCenter API integration in MCM for auto-login console), OpenNebula (installed from scratch at Nebula; migrated production client workloads from vCenter to OpenNebula), oVirt (evaluated as vCenter replacement — lab/testing only; OpenNebula chosen), Proxmox (lab), VyOS (tested as cost-saving router — not deployed in production), Kubernetes (INC-based familiarity — troubleshot Kubernetes-related incidents at Dell; familiar with Docker/Podman at production level)
- Monitoring: Zabbix (deployed and configured from scratch at Nebula Systems — dashboards, alerts, proactive monitoring of physical and virtual infrastructure; at Dell, integrated Zabbix MCP into AskMyServer for AI-driven graph generation across prod and nonprod environments), LibreNMS (network device monitoring and topology discovery at Nebula), Grafana (built production agent deployment dashboards at Dell — Mass Matter; daily refresh from internal data; used by whole ops team)
- Incident Management: L3 escalation for Linux & Windows INC queue; CTASK execution; MIM participation for critical recovery and RCA — aligns with ITIL Incident, Change, and Problem Management
- Vulnerability Management: Phase 1 of Patchy-Porter — automated CVE scope-list generation and patch validation pipeline before vendor engagement; Phase 2 with university team for AI-driven implementation
- Windows Server: INC support for 25,000+ Windows servers; SCCM remediation scripts; MECM deployment tracking via Mass Matter
- Ticketing: ServiceNow (primary ITSM at Dell — top 3 performer FY24 & FY25), Zammad (help desk at Velo/Nebula)
- Database: MariaDB, MySQL, PostgreSQL (create DB, manage privileges, basic admin for internal tools)
- Web Development: React.js (MCM frontend — SSH terminals, dashboards, admin panels), FastAPI, Python, WebSocket, nginx. React.js is the foundation of Next.js — transferable to Next.js with minimal ramp-up.
- Infrastructure as Code (IaC): Ansible (declarative configuration-as-code — same mindset as Terraform/Bicep; defines desired infrastructure state in code). OLAM pipelines. This IaC approach is transferable to Terraform/Bicep/ARM templates.
- AI/MCP: Model Context Protocol (built AskMyServer — adopted in production), LLM integration, GenAI, Podman
- SRE: SRE Foundation certified; applied SRE practices at Dell — 29% incident reduction, MIM, reliability via tooling

Hardware:
- Dell PowerEdge (install, configure, maintain — iDRAC, RAID, Redfish API Explorer in MCM)
- HP ProLiant (install, iLO configuration, maintenance in customer data centers)
- RAID configuration, iDRAC, iLO
- P2V and V2V migration using Veeam and vCenter Converter

Networking:
- Cisco IOS (switch/router config at Nebula — VLANs, routing, structured cabling)
- PFSense (firewall, NAT, routing rules)
- OPNSense (firewall, network policy)
- FSOS/FS switches (VLAN and port config at Nebula)
- HP ArubaOS (wireless AP config, SSID management)
- Netbox (IPAM, rack documentation, asset tracking — single source of truth at Nebula)
- VyOS

Documentation: Netbox (IPAM, rack layouts, asset inventory), daily activity reports, change logs, incident resolution records, structured cabling documentation

CERTIFICATIONS:
- Site Reliability Engineering (SRE) Foundation Certification
- Red Hat System Administration I (RH124)
- Introduction to Windows PowerShell 5.1
- Windows PowerShell: IT Management

EDUCATION:
- Bachelor's Degree in Computer & Communication Engineering — National University of Malaysia (UKM), 2014-2018
- Matriculation in Physics (Module 2) — Penang Matriculation College, 2013-2014

REFERENCES (6 total):
1. Jesse Chan — Senior Consultant, IT Infrastructure · Dell | +6019-2632171 | Jesse.Chan@dell.com (Engineering Counterpart)
2. Chris Ong — Senior Manager, IT Infrastructure · Dell | +6012-3358530 | Chris.Ong@dell.com (Manager)
3. Aqmal Zaki — Senior Advisor, IT Infrastructure · Dell | +6011-23546008 | aqmal.zaki@dell.com (Teammate)
4. Shahmat Dahlan — Consultant, IT Infrastructure · Dell | +6016-8826130 | shahmat.dahlan@dell.com (Co-Worker)
5. Ben Chin — CEO · Velo Technologies | +6012-2055522 | ben.chin@velo-technologies.com (Ex-Manager)
6. Javier Wong — CEO · Nebula Systems | +6012-2086226 | javier.wong@nebula-sys.com (Ex-Manager)
"""

JD_MATCH_PROMPT = """
You are a brutally honest senior technical recruiter with 15+ years of experience.
A visitor has pasted a Job Description and wants to know how well Amirul Arif's profile matches it.

CRITICAL RULES FOR SCORING:
- A skill being "listed" on a CV does NOT mean expertise. Dig into context and depth.
- If a skill appears once briefly and was not a regular part of someone's role, mark it partial or gap.
- Be realistic about experience depth — 6 months of exposure ≠ 3 years of hands-on.
- If the JD's core focus is fundamentally different from Amirul's expertise, reflect that honestly in the score.
- Don't inflate scores to be nice. A 60% match should be scored 60%, not 75%.
- DO NOT mark something as a gap (❌) if it is clearly described with real experience in the CV. Read carefully before scoring.
- Incident Management IS a core daily part of Amirul's role — L3 INC queue, MIM on-call, CTASKs. Never mark as a gap.
- Zabbix IS a real production skill — deployed from scratch, dashboards, alerts, MCP integration. Mark as strong if JD mentions monitoring.
- React.js IS transferable to Next.js — same framework, SSR layer on top. Mark as partial, not a gap.
- Ansible/OLAM demonstrates IaC mindset — transferable to Terraform/Bicep/ARM. Mark as partial, not a gap.
- GitLab IS Git/version control — mark as strong if JD mentions Git or version control.
- Do NOT use "primary" or "secondary" labels. State what experience exists and whether it's an advantage.

AMIRUL'S BACKGROUND (7+ years total experience):
- Linux/OS administration at enterprise scale — 30,000+ Linux servers at Dell (L3), hands-on at Nebula Systems
- Infrastructure automation — Python (multithreaded bulk ops, FastAPI), Bash, Ansible, OLAM — production pipelines
- Internal web platforms — MCM (used daily by 3-10 people across 5 teams) and AskMyServer (adopted in production, Top 15 hackathon finalist)
- Incident/Change Management — L3 INC queue, MIM on-call, CTASK execution, ITIL Incident/Change/Problem practices
- VMware/virtualisation — ESXi installed from scratch, vCenter managed, vCenter API integration in MCM
- PowerShell — 2 certifications, used across 25,000+ Windows servers at Dell
- Monitoring — Zabbix (deployed from scratch at Nebula, MCP integration at Dell), Grafana (production dashboards, Mass Matter)
- Web development — React.js frontend, FastAPI backend, WebSocket, nginx, full-stack internal platforms
- Networking — Cisco IOS, PFSense, OPNSense, HP ArubaOS (Nebula Systems 2020-2022)
- Windows Server — INC support, SCCM remediation scripts, MECM deployment tracking
- Git/version control — GitLab used across Dell projects (Patchy-Porter, Mass Matter)
- Modernising manual workflows into automated scalable solutions
- Certifications: SRE Foundation, Red Hat System Administration I (RH124), PowerShell x2

Analyze the JD and provide exactly this format:

📊 **Overall Match Percentage: X%**

✅ **Strong Matches:**
- [skill]: [Amirul's relevant experience and why it's an advantage]

⚠️ **Partial Matches:**
- [skill]: [what experience he has and what's missing]

❌ **Gaps:**
- [skill]: [what's missing and why it matters for this role]

📝 **Recommendation:**
[2-3 sentences: Is this a good fit? What should he highlight or what role suits him better?]

Be concise — each point max 2 lines. Total response should be readable in under 2 minutes.

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

    recent_visits = visits[:50]

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

    # Detect questions that need real-time web search
    search_keywords = [
        "salary", "pay", "compensation", "market rate", "how much",
        "current", "latest", "news", "price", "cost", "today",
        "2024", "2025", "2026", "trend", "industry average",
        "benchmark", "rate", "earning", "income", "gaji"
    ]
    needs_search = not req.is_jd_match and any(
        word in message.lower() for word in search_keywords
    )

    # Route to Gemini with Google Search for real-time questions
    if needs_search and gemini_client:
        try:
            from google.genai import types
            print(f"Routing to Gemini with Google Search: {message[:50]}")
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return {"reply": response.text, "model": "gemini-search"}
        except Exception as e:
            print(f"Gemini Search failed, falling back to Groq: {e}")

    # Use Groq for CV questions and JD matching (fast + smart)
    if GROQ_API_KEY:
        try:
            reply = call_groq(prompt, is_jd=req.is_jd_match)
            return {"reply": reply, "model": "groq"}
        except Exception as e:
            print(f"Groq failed, trying Gemini fallback: {e}")

    # Gemini fallback without search
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