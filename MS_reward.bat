@echo off

set CURRENT_DIR=%~dp0
cd /d "%CURRENT_DIR%"

@REM REM Check for virtual environments in this order: .venv, .conda, then global Python
if exist "%CURRENT_DIR%.venv\Scripts\python.exe" (
    set PYTHON_EXEC="%CURRENT_DIR%.venv\Scripts\python.exe"
    echo Using .venv environment
) else if exist "%CURRENT_DIR%.conda\Scripts\python.exe" (
    set PYTHON_EXEC="%CURRENT_DIR%.conda\Scripts\python.exe"
    echo Using .conda environment
) else (
    set PYTHON_EXEC=python
    echo Using global Python environment
)

REM Run the Python script with the selected environment
echo %PYTHON_EXEC% "%CURRENT_DIR%main.py" %*
%PYTHON_EXEC% "%CURRENT_DIR%main.py" %*

@REM REM Pause to Debug if Script Fails
@REM pause