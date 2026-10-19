# Lab 1 — Secure REST API with CI/CD and Real CVE Vulnerability Analysis

> Course: HDU Cybersecurity Lab · Work 1
> Stack: Python 3.11+ / Flask 3 / SQLite / JWT / bcrypt
> CI: GitHub Actions — Bandit (SAST) + Safety (SCA)
> CVE studied: **CVE-2018-1000656** (Flask JSON decoder DoS)

---

## 0. How to run locally

```bash
# 1. create & activate a virtualenv
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

# 2. install deps
pip install -r requirements.txt

# 3. start the API (listens on 127.0.0.1:5000, creates app.db on first run)
python app.py
```

Seeded demo account:

| username | password |
|---|---|
| `alice` | `CorrectHorse9!` |

---

## 1. API endpoints

### 1.1 `GET /health` — public liveness probe

```bash
curl http://127.0.0.1:5000/health
# {"status":"ok"}
```

### 1.2 `POST /auth/login` — issue a JWT

Request:

```bash
curl -X POST http://127.0.0.1:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"CorrectHorse9!"}'
```

Response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

Wrong credentials → `401 {"error":"invalid credentials"}`.

### 1.3 `GET /api/data` — protected, returns the caller's items

```bash
curl http://127.0.0.1:5000/api/data \
     -H "Authorization: Bearer <access_token>"
```

Without a token → `401 {"error":"missing or malformed Authorization header"}`.

### 1.4 `POST /api/create` — protected, create a new item (custom endpoint)

```bash
curl -X POST http://127.0.0.1:5000/api/create \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"content":"hello lab"}'
```

Response `201`:

```json
{"status":"created","content":"hello lab"}
```

---

## 2. Security controls implemented (2 marks)

| Threat | Control in `app.py` |
|---|---|
| **SQL Injection** | Every query uses `?` placeholders via `sqlite3` — e.g. `WHERE username = ?` with a bound parameter. No string concatenation anywhere. |
| **XSS (stored)** | User-supplied strings pass through `html.escape(..., quote=True)` before being stored. Demo: posting `<script>alert(1)</script>` is saved as `&lt;script&gt;alert(1)&lt;/script&gt;`. |
| **Broken authentication** | Login issues a short-lived (30 min) JWT signed with HS256. A `@login_required` decorator verifies signature, expiry and required claim on every protected route. |
| **Plaintext password storage** | Passwords are hashed with **bcrypt** at work factor 12 (`bcrypt.gensalt(rounds=12)`). The DB column stores the salted hash only. |
| **User-enumeration timing attack** | On unknown usernames, a dummy bcrypt check still runs so the response time does not reveal whether the account exists. |
| **Debugger exposure** | `app.run(..., debug=False)` — the Werkzeug interactive debugger is never enabled. |

---

## 3. CI/CD security pipeline (2 marks)

Config: `.github/workflows/ci.yml`.

Triggers: every `push` and `pull_request` to `main`.

| Stage | Tool | Type | What it does |
|---|---|---|---|
| SAST | **Bandit** | Static Application Security Testing | Scans `app.py` for dangerous calls (hardcoded secrets, `eval`, unsafe SQL, weak randomness, etc.) without running the app. |
| SCA | **Safety** | Software Composition Analysis | Scans `requirements.txt` against the CVE database to flag vulnerable third-party dependencies. |

Reports are uploaded as build artifacts (`bandit-report.json`, `safety-report.json`).

> After pushing to GitHub, paste the green Actions run URL here in the report:
> `https://github.com/<your-username>/<your-repo>/actions/runs/<run-id>`

---

## 4. CVE-2018-1000656 — reproduction, root cause, fix (2 + 1 + 1 marks)

Full write-up and ready-to-run Docker files live in [`vulhub-cve/`](./vulhub-cve/).

### 4.1 Summary

| Field | Value |
|---|---|
| CVE | CVE-2018-1000656 |
| Product | Pallets Project Flask |
| Affected | `< 0.12.3` |
| Fixed in | `0.12.3` |
| CWE | CWE-20 Improper Input Validation |
| Impact | Unauthenticated remote Denial of Service (excessive memory) |

### 4.2 Reproduction

```bash
cd vulhub-cve
docker compose -f docker-compose.vuln.yml up --build -d

# PoC: deeply-nested JSON forces the old parser to balloon
python -c "print('[' * 5000 + '1' + ']' * 5000)" > payload.json
docker stats --no-stream           # memory baseline
curl -H "Content-Type: application/json" --data-binary @payload.json \
     http://127.0.0.1:8000/json
docker stats --no-stream           # memory spikes >500 MB, worker hangs / 500
```

### 4.3 Root cause

Flask < 0.12.3 used its JSON request wrapper without bounding the cost of
malformed / pathologically nested input. A remote, unauthenticated attacker
who POSTs such a body to any endpoint calling `request.get_json()` can make
the process allocate unbounded memory, exhausting the worker and causing DoS.

### 4.4 Fix

```bash
docker compose -f docker-compose.vuln.yml down
docker compose -f docker-compose.fixed.yml up --build -d
```

Single-line change in `vulhub-cve/Dockerfile.fixed`:

```diff
- RUN pip install --no-cache-dir flask==0.12.2
+ RUN pip install --no-cache-dir flask==0.12.3
```

### 4.5 Verification + regression

- **Re-run the PoC** on the fixed image → HTTP 400 returned in milliseconds,
  container memory flat. *(Screenshot for report.)*
- **Regression test** — normal business still works:
  ```bash
  curl -H "Content-Type: application/json" \
       -d '{"hello":"world"}' \
       http://127.0.0.1:8000/json
  # {"echo":{"hello":"world"}}
  ```

---

## 5. Submission checklist

- [x] Public GitHub / GitLab repo containing this folder.
- [x] This `README.md` (API docs, security controls, CI link, CVE analysis).
- [x] Green GitHub Actions run (Bandit + Safety).
- [x] `vulhub-cve/` folder with vulnerable + fixed Docker builds.
- [ ] Paste the Actions run URL above.
- [ ] Screenshots (paste into the formal lab report): login success, 401 without token, XSS-escaped output, Bandit + Safety CI results, CVE PoC memory spike, fixed PoC returning 400.

---

## 6. Answers to control questions (optional revision aid)

1. **Why bcrypt over SHA-256 for passwords?**
   bcrypt is deliberately slow and salted, with a tunable work factor; SHA-256 is fast and unsalted, making offline brute-force / rainbow-table attacks trivial.
2. **SAST vs DAST?**
   SAST audits source code while the app is not running (white-box, e.g. Bandit); DAST attacks a running instance (black-box, e.g. OWASP ZAP).
3. **How does the server verify a JWT?**
   It re-signs the header+payload with the server secret and checks that the resulting signature equals the one presented, and validates `exp` / `iat`.
4. **Risk of not auditing dependencies?**
   Transitive libraries can contain known CVEs (e.g. this very CVE) that the app never wrote itself — SCA catches them.
5. **Docker/Vulhub vs local install?**
   Isolated, reproducible, disposable environments; no pollution of the host; exact version pinning.
6. **Vulnerability vs exploit?**
   A vulnerability is the flaw; an exploit is the code/request that triggers it. Here CVE-2018-1000656 is the vulnerability; the nested-JSON curl request is the exploit.
7. **Why regression testing after a fix?**
   To confirm the patch did not break legitimate functionality (the `/json` echo must still work).
8. **Why reproduce known CVEs?**
   It builds hands-on intuition for root cause, exploitation preconditions, and patch behaviour — directly transferable to SOC triage and pentesting.
