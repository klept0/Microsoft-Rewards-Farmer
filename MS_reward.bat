@echo off

set CURRENT_DIR=%~dp0
cd /d "%CURRENT_DIR%"

REM Find any virtual environment by looking for a Python executable in subfolders
for /d %%D in ("%CURRENT_DIR%*") do (
    if exist "%%D\Scripts\python.exe" (
        set PYTHON_EXEC="%%D\Scripts\python.exe"
        echo Using virtual environment: %%D
        goto :RUN_SCRIPT
    )
)

@REM If no virtual environment is found, use global Python
set PYTHON_EXEC=python
echo Using global Python environment

:RUN_SCRIPT
REM Run the Python script with the selected environment
echo %PYTHON_EXEC% "%CURRENT_DIR%main.py" %*
%PYTHON_EXEC% "%CURRENT_DIR%main.py" %*

@REM Uncomment the line below to pause for debugging if needed
@REM pause