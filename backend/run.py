import os
import sys
import subprocess
import uvicorn

if __name__ == "__main__":
    # Auto-detect virtualenv python to prevent running on global python
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    
    if os.path.exists(venv_python) and sys.executable.lower() != venv_python.lower():
        print(f"Auto-detected local virtualenv. Restarting script under: {venv_python}")
        sys.exit(subprocess.call([venv_python] + sys.argv))
        
    print("Starting HireGenie AI backend server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
