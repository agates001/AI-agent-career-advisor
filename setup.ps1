##To run this file: .\setup.ps1

# Temporarily bypass execution policies just for this terminal process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate the virtual environment natively in PowerShell
.venv\Scripts\Activate.ps1

# Upgrade pip to prevent installation warning messages
python -m pip install --upgrade pip

# Double-check and install the pinned requirements
pip install -r requirements.txt

# Execute the MAgent workflow within the correct environment
#python MAgent.py

#  Keep the window 
#Read-Host -Prompt "Workflow complete. Press Enter to exit"

