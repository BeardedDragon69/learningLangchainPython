param(
    [switch]$SkipOllama,
    [string]$OllamaModel = "gpt-oss:20b-cloud"
)

$ErrorActionPreference = "Stop"

# Install Python dependencies for this project into a local virtual environment.
# Usage:
#   .\install.ps1
#   .\install.ps1 -SkipOllama
#   .\install.ps1 -OllamaModel "llama3.1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"
$ReqFile = Join-Path $ScriptDir "requirements.txt"

if (-not (Test-Path $ReqFile)) {
    Write-Error "requirements.txt not found at $ReqFile"
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3.13")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return @("python3")
    }
    throw "Python 3 is not installed or not in PATH."
}

$PythonCmd = Get-PythonCommand

# Validate the selected Python command; if py -3.13 is unavailable, fall back to py -3.
if ($PythonCmd[0] -eq "py") {
    try {
        & py -3.13 --version | Out-Null
    } catch {
        $PythonCmd = @("py", "-3")
    }
}

Write-Host "Using Python command: $($PythonCmd -join ' ')"
& $PythonCmd[0] @($PythonCmd[1..($PythonCmd.Length - 1)] | Where-Object { $_ }) --version

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir"
    & $PythonCmd[0] @($PythonCmd[1..($PythonCmd.Length - 1)] | Where-Object { $_ }) -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python not found at $VenvPython"
}

Write-Host "Upgrading pip, setuptools, and wheel"
& $VenvPython -m pip install --upgrade pip setuptools wheel

Write-Host "Installing dependencies from requirements.txt"
& $VenvPython -m pip install -r $ReqFile

if ($SkipOllama) {
    Write-Host "Skipping Ollama setup (-SkipOllama set)."
} else {
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-Host "Found Ollama. Pulling model: $OllamaModel"
        try {
            & ollama pull $OllamaModel
        } catch {
            Write-Warning "Could not pull model '$OllamaModel'. Retry manually: ollama pull $OllamaModel"
        }
    } else {
        Write-Host "Ollama not found in PATH. Install it from https://ollama.com/download"
        Write-Host "Then run: ollama pull $OllamaModel"
    }
}

Write-Host "Setup complete. Activate environment with: .\.venv\Scripts\Activate.ps1"
