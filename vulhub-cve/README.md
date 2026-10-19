# CVE-2019-10743 — Zip Slip arbitrary file write (Go archive extraction)

## 1. Vulnerability summary

| Field | Value |
|---|---|
| CVE | CVE-2019-10743 |
| Affected product | Go `archive/zip` based extraction (mholt/archiver) |
| Affected | All versions without path sanitization |
| Fix | Reject `..` / absolute paths before joining |
| CWE | CWE-22 / CWE-23 Path Traversal |
| Impact | Arbitrary file write outside the extraction directory |

## 2. Root cause

The Go standard library `archive/zip` does not sanitize entry names. If an
application joins an attacker-controlled zip entry name (e.g.
`../../tmp/evil.txt`) directly to the extraction directory, the resulting path
escapes the intended folder — the classic **Zip Slip** pattern. A malicious
archive containing `../` segments can then write files anywhere the process
has permission.

## 3. Files in this folder

| File | Purpose |
|---|---|
| `main.go` | Demo program: builds a malicious zip and extracts it; vulnerable/patched behaviour switched by the `fixed` argument |
| `Dockerfile.vuln` / `docker-compose.vuln.yml` | Vulnerable build: no path check |
| `Dockerfile.fixed` / `docker-compose.fixed.yml` | Fixed build: rejects traversal entries |

## 4. Reproduction (vulnerable)

```bash
docker compose -f docker-compose.vuln.yml up --build
```

The malicious zip contains the entry `../../tmp/evil-pwned.txt`. The vulnerable
build extracts it to `/tmp/extract` without checking the path; the file is
written to `/tmp/evil-pwned.txt`, **outside** the target directory.

## 5. Fix

Reject any entry containing `..` or an absolute path before joining:

```diff
  for _, f := range r.File {
+     if strings.Contains(f.Name, "..") || filepath.IsAbs(f.Name) {
+         fmt.Printf("[BLOCKED] traversal entry rejected: %s\n", f.Name)
+         continue
+     }
      target := filepath.Join("/tmp/extract", f.Name)
```

```bash
docker compose -f docker-compose.fixed.yml up --build
```

The patched build blocks the traversal entry and no file escapes
`/tmp/extract`.
