# Wrapper PowerShell para o script Python de dev.
# Uso: .\scripts\dev.ps1 [--install] [--backend] [--frontend] [--port N]

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& python "$ScriptDir\dev.py" @args
