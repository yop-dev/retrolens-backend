# Start the FastAPI server in background
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "run.py" -WorkingDirectory $PSScriptRoot
Write-Host "Server starting on http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs available at http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Start-Sleep -Seconds 3
