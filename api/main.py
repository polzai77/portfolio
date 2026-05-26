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
    allow_credentials=False,
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
Phone: +601124005710
Email: amirularif9577@gmail.com
LinkedIn: https://www.linkedin.com/in/amirul-arif-49994b155/
GitHub: https://github.com/polzai77
Portfolio: https://polzai77.github.io/portfolio/

PROFESSIONAL SUMMARY:
Experienced Infrastructure Specialist with over 5 years of expertise as a Linux Administrator.
Proficient in deploying and managing Linux-based systems, installing and configuring hardware
in data centers including servers and network switches. Skilled in software installation for
both physical and virtual machines. Passionate about continuous learning and staying up to date
with emerging technologies to enhance skills and drive innovation.

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
   - MCM (Multi Connection Manager): Centralised role-based web platform for server operations featuring:
     Windows: RDP Connections, LAPS Password Retrieval (WinRM), Windows Disk Expand & Search, File Share Browser (SMB)
     Linux: Multi-SSH Terminal (single & multi-server), Get Root Password (vCenter API with auto-login console), SCP Browser
     Misc: iDRAC Query, Redfish API Explorer, PowerCLI (vCenter), Root Access Audit, PCI Server Console
     CHGTASK: Mount Activity Checker, Implementation Step Manager
     Deployments (Mass Matter): Server Deployment Filtering, Agent Classification, ECN Email Generator, MECM Deployment Status Tracking, Historical Data
     Admin: Access Control Manager (group & user-level permissions), Usage Analytics, User Command Tracking, Kickout Session, Feedback
     Currently extending with VM Disk Add & Expand (multi-VM, SCSI-aware) — planned for OLAM conversion and ServiceNow integration
   - AskMyServer (Dell Hackathon Project): Solely designed, architected, and developed an AI-powered natural language server diagnostics platform built on MCP (Model Context Protocol) architecture. Adopted by team, senior consultant, and manager for day-to-day operations.
     Target Users: Non-technical app/server owners — enabling self-service diagnostics and vulnerability checks without CLI knowledge or SME involvement
     Backend: Dell GenAI Gateway as LLM proxy with dual-model routing — GPT-Powerful-120B for complex queries & Zabbix graph generation, LLaMA 3.3-70B for live diagnostics and bulk server queries
     MCP Tool Servers: Linux SSH (multi-server), Windows WinRM, OS Info/Inventory API, Zabbix MCP (prod & nonprod)
     Frontend: Open WebUI with tool server integration, served via nginx SSL termination
     Infrastructure: Podman + systemd deployment
     Impact: Reduced server diagnostic time to under a minute — empowering server/app owners to investigate issues and check vulnerabilities independently, directly reducing unnecessary INC creation across the full supported fleet

   Achievements:
   - Oracle DB Server CPU & RAM Resizing: Resolved kernel panic at the Linux/OS layer during system resizing. Collaborated cross-team with DBEs and SEs to reclaim 1,956 CPUs & 15.6 TB of RAM, resulting in approximately USD 312K in cost savings
   - Multi Connection Manager: Bigger audience, simplifies day-to-day work in bulk operations, applying pre-automation before implementing full automation
   - Grafana Agent Dashboard: Displaying agent status for both Windows and Linux across supported servers, server health, trending, history

2. Dell Technologies — Analyst, IT Technical Services (Linux & Windows Operation Support)
   April 2022 – March 2025 | 3 years | Hybrid
   Roles:
   - Provided in-depth support for over 30,000 Linux servers and 25,000 Windows servers, following established processes and escalating complex issues to the Engineering Team when necessary
   - Incident Management: Work with support teams to troubleshoot issues and attend Major Incident Management (MIM) when needed to ensure recovery and assist on providing root cause analysis
   - Change support: Participate in change activity given by "Change Coordinator" based on client/user needs to ensure smooth transitions with minimal impact on operations
   - Vendor support: Work with vendors and IT teams to resolve server related issues
   - Develop scripts using the in-house tool "Bi-Frost" to automate tasks, reduce manual work, and assist team members in reducing incident count
   - Support during critical activity: Major Data Center Maintenance, Power Maintenance and Black Friday holiday readiness
   Achievements:
   - GICC Bi-Frost Tools addon Features — Interactive Console Linux: Developing a web console for in-house users to connect remotely for zero touch approach
   - FY24Q2: Excellent COE Server INC Delivery Results — Combined with two other team members contributed to overall Server/Server Tool INC operation support from FY24Q1-Q2, achieving 29% incidents reduction
   - Consistently ranked among the Top 3 performers in FY24 and FY25 for resolving user incidents and task creation, demonstrating efficiency in handling a high volume of incident tickets

3. Velo Technologies Sdn. Bhd and Nebula Systems Sdn. Bhd (Outsource) — System Engineer
   May 2020 – April 2022 | 2 years | On-site
   Roles for Velo Technologies:
   - Technical Support & Maintenance: Provide IT infrastructure support for desktops, networks, security, and basic data center operations. Identify opportunities for infrastructure and process improvements.
   - User Support & Account Management: Deliver first-level user support, including IT setup and account administration.
   - IT Asset Management: Maintain IT inventory, conduct routine equipment audits, and ensure accurate tracking of desktops, laptops, network devices, and mobile assets.
   - Vendor & Supplier Coordination: Liaise with external vendors, suppliers, and contractors for repairs, services, and procurement.
   - Help Desk & Ticketing Support: Work closely with the help desk team to update ticket statuses and ensure timely issue resolution.
   - Administrative & Operational Support: Perform IT administrative duties.
   - On-Site & Standby Support: Available for on-site support and urgent troubleshooting as required.
   Roles for Nebula Systems:
   - Server & Network Administration: Installation, configuration, and maintenance of operating environments, including servers and network devices.
   - Server OS: Windows Server, Linux (Ubuntu, CentOS, Debian), VMware ESXi
   - Network OS: Cisco IOS, PFSense, OPNSense, FSOS, HP ArubaOS
   - Open-Source Solutions: Research, development, and implementation of tools such as Zabbix, LibreNMS, OpenNebula, VyOS, oVirt, and Netbox.
   - System Maintenance & Security: Regular software and hardware updates, ensuring system security and stability.
   - Monitoring & Incident Response: Proactively monitoring physical and virtual environments, troubleshooting.
   - Data Center Operations: Hands-on experience in installing and maintaining physical hardware, including servers, networking equipment, and structured cabling in both in-house and customer-owned data centers.
   - Technical Support & Documentation: Providing training, support, and maintaining detailed records of system changes and issue resolutions.
   - P2V and V2V migrations using Veeam and vCenter Converter

4. Stardocs Sdn Bhd — System Programmer & Support
   November 2019 – January 2020 | Contract | Subang
   Roles:
   - Software & Hardware Proficiency: Attain and maintain expertise in software products, related hardware, and system integration.
   - Pre & Post-Sales Support: Provide timely and high-quality support for both internal teams and external customers, ensuring smooth delivery of assignments.
   - System & Application Support: Manage in-house systems for office and outsourcing operations, including application software (Solimar Software), antivirus solutions, printers, PCs, servers, and related accessories.
   - Professional IT Services: Deliver technical support and consulting services to business partners and end-users, including billable services as required.
   - Reporting & Documentation: Submit daily activity reports outlining completed tasks, delays, and planned activities.

5. Ministry of Health Malaysia (KKM) — Administrative & IT Officer Grade N41
   January 2019 – October 2019 | Contract | Putrajaya
   Roles:
   - Technical Troubleshooting: Diagnose and resolve common IT issues, including internet connectivity problems, system crashes, and hardware/software malfunctions.
   - Hardware & Software Support: Conduct damage assessments and recommend repairs or replacements as needed.
   - Vendor Coordination: Liaise with external vendors for device replacements, hardware repairs, and procurement when required.
   - Administrative Work: Handle documentation, record-keeping, data entry, and IT-related coordination to ensure smooth operations.

6. Pacific Engineering Sdn Bhd — Intern R&D Engineer
   June 2017 – September 2017 | 4 months | Petaling Jaya
   - Developed a DIY Arduino-based controller to monitor industrial machinery as part of a supervisor-assigned project.

SKILLS:
Software:
- Linux: RHEL, OL, Debian, Ubuntu, SUSE, CentOS
- Scripting: PowerShell, Bash, Python
- Automation: Kubernetes (limited exposure), Ansible, OLAM
- Virtualisation: VMware vCenter/vSphere/ESXi, Proxmox, oVirt, OpenNebula (linked with VMware)
- Monitoring: LibreNMS, Zabbix, Grafana
- Ticketing: Zammad, ServiceNow
- Database: MariaDB, MySQL, PostgreSQL (create simple DB, provide privilege, view tasks)
- Web Development: React.js, FastAPI, Python, WebSocket, nginx
- AI/MCP: Model Context Protocol, LLM integration, GenAI, Podman

Hardware:
- Dell PowerEdge, HP ProLiant, FS Switch configuration from hardware to software installation based on requirement needs
- Configure RAID, iDRAC and iLO Card
- P2V and V2V migration using Veeam and vCenter Converter

Networking:
- Cisco IOS, PFSense, OPNSense, FSOS, HP ArubaOS, Netbox, VyOS

CERTIFICATIONS:
- Site Reliability Engineering (SRE) Foundation Certification
- Red Hat System Administration I (RH124)
- Introduction to Windows PowerShell 5.1
- Windows PowerShell: IT Management

EDUCATION:
- Bachelor's Degree in Computer & Communication Engineering — National University of Malaysia (UKM), 2014-2018
- Matriculation in Physics (Module 2) — Penang Matriculation College, 2013-2014

REFERENCES (6 total):
1. Jesse Chan — Senior Consultant, IT Infrastructure · Dell | +6019-2632171 | Jesse.Chan@dell.com (Engineering Counterpart, current)
2. Chris Ong — Senior Manager, IT Infrastructure · Dell | +6012-3358530 | Chris.Ong@dell.com (Manager, current)
3. Aqmal Zaki — Senior Advisor, IT Infrastructure · Dell | +6011-23546008 | aqmal.zaki@dell.com (Teammate, current)
4. Shahmat Dahlan — Consultant, IT Infrastructure · Dell | +6016-8826130 | shahmat.dahlan@dell.com (Co-Worker, current)
5. Ben Chin — CEO · Velo Technologies | +6012-2055522 | ben.chin@velo-technologies.com (Ex-Manager, Velo Technologies)
6. Javier Wong — CEO · Nebula Systems | +6012-2086226 | javier.wong@nebula-sys.com (Ex-Manager, Nebula Systems)

CONTACT:
- Phone: +601124005710
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
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"reply": response.text}

    except Exception as e:
        import traceback
        print(f"Gemini error: {e}")
        print(traceback.format_exc())
        return {"reply": "Sorry, I'm having trouble connecting right now. Please try again or contact Amirul directly at amirularif9577@gmail.com"}