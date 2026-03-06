import os
import subprocess
import secrets
import time
import sys
import atexit
import signal

def main():
    print("Starting SES Email Sender...")

    # Generate secure token
    api_token = secrets.token_hex(32)
    os.environ["API_TOKEN"] = api_token
    os.environ["API_PORT"] = "8000"

    print("Starting API Backend...")
    # Start Python FastAPI backend
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid if os.name == 'posix' else None
    )

    def cleanup():
        print("\nShutting down backend...")
        if os.name == 'posix':
            os.killpg(os.getpgid(backend_process.pid), signal.SIGTERM)
        else:
            backend_process.terminate()

    atexit.register(cleanup)

    # Wait for API to start
    time.sleep(2)

    print("Starting TUI Frontend...")
    # Start TUI using Bun
    tui_process = subprocess.run(
        ["bun", "run", "src/index.tsx"],
        cwd="tui-ts",
        env=os.environ.copy()
    )

if __name__ == "__main__":
    main()
