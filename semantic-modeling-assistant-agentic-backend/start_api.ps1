# PowerShell script to start the Semantic Modeling Assistant API
# Usage: .\start_api.ps1

Write-Host "Starting Semantic Modeling Assistant API..." -ForegroundColor Green

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Set PYTHONPATH to include src directory
$env:PYTHONPATH = "$PWD\src"

# Run the API server
python run_api.py
