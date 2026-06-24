<#
Bootstraps a Python virtual environment and downloads ffmpeg for Windows.
Run from project root in PowerShell (preferably as a normal user):

    .\setup.ps1

This script will:
- Create a `venv` virtual environment if missing
- Install dependencies from `requirements.txt` into the venv
- Download an FFmpeg Windows build and extract `ffmpeg.exe` next to `main.py`
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Project root: $root"
$venv = Join-Path $root 'venv'
$python = 'python'

function Ensure-Venv {
    param($venvPath)
    if (-not (Test-Path $venvPath)) {
        Write-Host 'Creating virtual environment...'
        & $python -m venv $venvPath
    } else {
        Write-Host 'Virtual environment already exists.'
    }
}

function Venv-Python {
    param($venvPath)
    return Join-Path $venvPath 'Scripts\python.exe'
}

function Install-Requirements {
    param($venvPython)
    Write-Host 'Upgrading pip and installing requirements...'
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $root 'requirements.txt')
}

function Download-FFmpeg {
    param($dest)
    Write-Host 'Downloading FFmpeg (this may take a minute)...'
    $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    $tmp = Join-Path $env:TEMP ('ffmpeg_' + [guid]::NewGuid().ToString() + '.zip')
    Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
    $extract = Join-Path $env:TEMP ('ffmpeg_extract_' + [guid]::NewGuid().ToString())
    Expand-Archive -Path $tmp -DestinationPath $extract -Force
    $ff = Get-ChildItem -Path $extract -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1
    if ($ff) {
        Copy-Item -Path $ff.FullName -Destination $dest -Force
        Write-Host "ffmpeg.exe copied to $dest"
    } else {
        Write-Warning 'ffmpeg.exe not found in downloaded archive. Please download ffmpeg manually and place ffmpeg.exe next to main.py.'
    }
    Remove-Item -Path $tmp -Force
    Remove-Item -Path $extract -Recurse -Force
}

try {
    Push-Location $root
    Ensure-Venv -venvPath $venv
    $venvPython = Venv-Python -venvPath $venv
    if (-not (Test-Path $venvPython)) {
        throw "Python executable not found in venv: $venvPython"
    }
    Install-Requirements -venvPython $venvPython

    $ffDest = Join-Path $root 'ffmpeg.exe'
    if (-not (Test-Path $ffDest)) {
        Download-FFmpeg -dest $ffDest
    } else {
        Write-Host 'ffmpeg.exe already present.'
    }

    Write-Host 'Setup complete. Run the app with:'
    Write-Host "$($venvPython) main.py"
} catch {
    Write-Error "Setup failed: $_"
} finally {
    Pop-Location
}
