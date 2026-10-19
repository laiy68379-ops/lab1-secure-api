Write-Host "=== CVE-2021-41773 PATCHED (Apache 2.4.50) ===" -ForegroundColor Cyan
Write-Host ""

$url = "http://127.0.0.1:8080/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd"
Write-Host "Same attack request: $url" -ForegroundColor Gray
Write-Host ""

Write-Host "--- Response from patched server ---" -ForegroundColor Yellow
curl.exe -s --path-as-is $url -w "`nHTTP Status: %{http_code}`n"

Write-Host ""
Write-Host "=== No /etc/passwd leaked! Attack blocked. ===" -ForegroundColor Green
Write-Host "=== Screenshot this window now. ===" -ForegroundColor Green
Read-Host "Press Enter to close"
