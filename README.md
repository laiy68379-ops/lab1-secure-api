# Lab 1 — Secure REST API with CI/CD and Real CVE Vulnerability Analysis

> Course: HDU Cybersecurity Lab · Work 1
> Stack: Python 3.11+ / Flask 3 / SQLite / JWT / bcrypt
> CI: GitHub Actions — Bandit (SAST) + Safety (SCA)
> CVE studied: **CVE-2021-41773** (Apache HTTP Server 2.4.49 path traversal)


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

## 2. Security controls implemented

| Threat | Control in `app.py` |
|---|---|
| **SQL Injection** | Every query uses `?` placeholders via `sqlite3` — e.g. `WHERE username = ?` with a bound parameter. No string concatenation anywhere. |
| **XSS (stored)** | User-supplied strings pass through `html.escape(..., quote=True)` before being stored. Demo: posting `<script>alert(1)</script>` is saved as `&lt;script&gt;alert(1)&lt;/script&gt;`. |
| **Broken authentication** | Login issues a short-lived (30 min) JWT signed with HS256. A `@login_required` decorator verifies signature, expiry and required claim on every protected route. |
| **Plaintext password storage** | Passwords are hashed with **bcrypt** at work factor 12 (`bcrypt.gensalt(rounds=12)`). The DB column stores the salted hash only. |
| **User-enumeration timing attack** | On unknown usernames, a dummy bcrypt check still runs so the response time does not reveal whether the account exists. |
| **Debugger exposure** | `app.run(..., debug=False)` — the Werkzeug interactive debugger is never enabled. |

### 2.1 Functional test output

Running all endpoints with curl: login (JWT issued) → access `/api/data` without token (401) → access with token (200, existing XSS-escaped item visible) → create a new item (201):

![API functional test — login, 401, 200, create](assets/api-demo.png)

---

## 3. CI/CD security pipeline

Config: `.github/workflows/ci.yml`. Triggers: every `push` and `pull_request` to `main`.

| Stage | Tool | Type | What it does |
|---|---|---|---|
| SAST | **Bandit** | Static Application Security Testing | Scans `app.py` for dangerous calls (hardcoded secrets, `eval`, unsafe SQL, weak randomness, etc.) without running the app. |
| SCA | **Safety** | Software Composition Analysis | Scans `requirements.txt` against the CVE database to flag vulnerable third-party dependencies. |

### 3.1 Pipeline run status

The workflow completes successfully (green check) on every push:

![GitHub Actions green run](assets/ci-actions-green.png)

### 3.2 Bandit SAST result

Bandit reports **0 issues** across severity levels (Low / Medium / High):

![Bandit SAST result](assets/ci-bandit.png)

### 3.3 Safety SCA result

Safety scans the third-party dependency tree and reports known vulnerabilities for review:

![Safety SCA result](assets/ci-safety.png)

---

## 4. CVE-2019-10743 — reproduction, root cause, fix

Full source lives in [`vulhub-cve/`](./vulhub-cve/).

### 4.1 Summary

| Field | Value |
|---|---|
| CVE | CVE-2019-10743 |
| Product | Go `archive/zip` based extraction (mholt/archiver) |
| Affected | All versions without path sanitization |
| Fixed in | Path sanitization added (reject `..` / absolute paths) |
| CWE | CWE-22 Path Traversal / CWE-23 Relative Path Traversal |
| Impact | Arbitrary file write outside extraction directory (Zip Slip) |

### 4.2 Root cause

When extracting a zip archive, the Go standard library `archive/zip` does **not**
sanitize entry names. If an application directly joins an attacker-controlled
zip entry name (e.g. `../../tmp/evil.txt`) to the target extraction directory,
the resulting path escapes the intended folder. This is the classic **Zip Slip**
pattern: a malicious archive contains entries with `../` segments, and the
unarchive routine writes them wherever the traversal leads.

### 4.3 Reproduction (vulnerable extraction)

```bash
cd vulhub-cve
docker compose -f docker-compose.vuln.yml up --build
```

The Go program builds a malicious zip with entry `../../tmp/evil-pwned.txt`,
then extracts it to `/tmp/extract` **without** path checking. Result: the file
is written to `/tmp/evil-pwned.txt`, **outside** the target directory:

![CVE PoC — Zip Slip writes file outside target dir](assets/cve-poc-success.png)

### 4.4 Fix

Single change in `main.go` — reject any entry containing `..` or absolute paths
before joining:

```diff
  for _, f := range r.File {
+     if strings.Contains(f.Name, "..") || filepath.IsAbs(f.Name) {
+         fmt.Printf("[BLOCKED] traversal entry rejected: %s\n", f.Name)
+         continue
+     }
      target := filepath.Join("/tmp/extract", f.Name)
```

### 4.5 Verification

Re-run the same malicious zip against the patched build. The traversal entry
is blocked and no file escapes `/tmp/extract`:

![Fixed build — traversal entry rejected](assets/cve-fixed-400.png)



## 5. Answers to control questions

1. **Why bcrypt over SHA-256 for passwords?**
   bcrypt is deliberately slow and salted, with a tunable work factor; SHA-256 is fast and unsalted, making offline brute-force / rainbow-table attacks trivial.
2. **SAST vs DAST?**
   SAST audits source code while the app is not running (white-box, e.g. Bandit); DAST attacks a running instance (black-box, e.g. OWASP ZAP).
3. **How does the server verify a JWT?**
   It re-signs the header+payload with the server secret and checks that the resulting signature equals the one presented, and validates `exp` / `iat`.
4. **Risk of not auditing dependencies?**
   Transitive libraries can contain known CVEs that the app never wrote itself — SCA catches them.
5. **Docker/Vulhub vs local install?**
   Isolated, reproducible, disposable environments; no pollution of the host; exact version pinning.
6. **Vulnerability vs exploit?**
   A vulnerability is the flaw; an exploit is the code/request that triggers it. CVE-2019-10743 is the vulnerability; the crafted zip entry `../../tmp/evil.txt` is the exploit.
7. **Why regression testing after a fix?**
   To confirm the patch did not break legitimate functionality (normal zip extraction must still work).
8. **Why reproduce known CVEs?**
   It builds hands-on intuition for root cause, exploitation preconditions, and patch behaviour — directly transferable to SOC triage and pentesting.
