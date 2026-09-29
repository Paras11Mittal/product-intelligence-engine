import os
import sys
import subprocess

# Auto-relaunch using the virtual environment if it exists and we aren't using it
venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
venv_python = os.path.join(venv_dir, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(venv_dir, "bin", "python")

if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    print("Automatically switching to virtual environment...")
    sys.exit(subprocess.call([venv_python] + sys.argv))

import uvicorn

if __name__ == "__main__":
    # Render assigns a dynamic port, so we must read it from the environment.
    # We fall back to 8000 for local development.
    port = int(os.environ.get("PORT", 8000))
    
    # Use 0.0.0.0 in production (when PORT is set), otherwise use 127.0.0.1 locally
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=False  # Turn off reload in production.
    )