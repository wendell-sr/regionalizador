@echo off
REM Wrapper CMD para o script Python de dev.
REM Uso: scripts\dev.bat [--install] [--backend] [--frontend]

python "%~dp0dev.py" %*
