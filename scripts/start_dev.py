"""Start both frontend and backend in development mode."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent

    # Start backend
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "sputnik.api.server"],
        cwd=project_root,
    )

    # Start frontend
    frontend_dir = project_root / "frontend"
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
    )

    try:
        print("Starting Sputnik development servers...")
        print("Backend: http://localhost:8000")
        print("Frontend: http://localhost:8080")
        print("Press Ctrl+C to stop")
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()

