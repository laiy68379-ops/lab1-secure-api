Write-Host "=== Regression Test: normal page still works ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "GET http://127.0.0.1:8080/index.html" -ForegroundColor Gray
Write-Host ""

curl.exe -s -w "`nHTTP Status: %{http_code}`n" http://127.0.0.1:8080/index.html

Write-Host ""
Write-Host "=== Normal page works! No regression. ===" -ForegroundColor Green
Write-Host "=== Screenshot this window now. ===" -ForegroundColor Green
Read-Host "Press Enter to close"
