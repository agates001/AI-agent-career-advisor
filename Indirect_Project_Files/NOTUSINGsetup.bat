@echo off
echo Activating virtual environment...
REM This is a comment. 
REM Note: The command that follows turns on the virtual environment 
REM in the background which allows your terminal 
REM to run any Python or Pip commands in the .venv folder instead of your 
REM global computer system
REM to run this, type .\setup.bat
call .venv\Scripts\activate
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
echo Environment setup complete! You can now run your scripts.
pause