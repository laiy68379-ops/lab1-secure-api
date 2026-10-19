Write-Host "=== Lab1 API Demo ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "--- 1. POST /auth/login (correct credentials) ---" -ForegroundColor Yellow
$login = curl.exe -s -X POST http://127.0.0.1:5000/auth/login -H "Content-Type: application/json" -d '{\"username\":\"alice\",\"password\":\"CorrectHorse9!\"}' | ConvertFrom-Json
Write-Host $login
Write-Host ""

Write-Host "--- 2. GET /api/data WITHOUT token (expect 401) ---" -ForegroundColor Yellow
curl.exe -s -w "`nHTTP %{http_code}`n" http://127.0.0.1:5000/api/data
Write-Host ""

Write-Host "--- 3. GET /api/data WITH token ---" -ForegroundColor Yellow
$token = $login.access_token
curl.exe -s -w "`nHTTP %{http_code}`n" -H "Authorization: Bearer $token" http://127.0.0.1:5000/api/data
Write-Host ""

Write-Host "--- 4. POST /api/create (create item) ---" -ForegroundColor Yellow
curl.exe -s -w "`nHTTP %{http_code}`n" -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d '{\"content\":\"hello lab\"}' http://127.0.0.1:5000/api/create
Write-Host ""

Write-Host "=== Done. Screenshot this window. ===" -ForegroundColor Green
Read-Host "Press Enter to close"
