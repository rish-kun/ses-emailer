#!/usr/bin/env python3
"""
SES Emailer Orchestrator
Spawns the FastAPI backend and TypeScript TUI in sync.
"""

import os
import secrets
import signal
import socket
import subprocess
import sys
import time
import urllib.request


def find_free_port(preferred: int = 8787) -> int:
    """Find a free TCP port, preferring the given one."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", preferred))
            return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def wait_for_health(url: str, timeout: int = 15) -> bool:
    """Poll the health endpoint until the API is ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=2)
            if req.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Generate one-time auth token
    token = secrets.token_hex(16)
    port = find_free_port()
    api_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["API_TOKEN"] = token

    print(f"\033[1;36m[SES Emailer]\033[0m Starting API on port {port}...")

    # Start FastAPI backend
    api_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for API to be healthy
    health_url = f"{api_url}/health"
    if not wait_for_health(health_url):
        print("\033[1;31m[Error]\033[0m API failed to start. Check logs.")
        api_proc.terminate()
        sys.exit(1)

    print(f"\033[1;32m[SES Emailer]\033[0m API ready at {api_url}")
    print(f"\033[1;36m[SES Emailer]\033[0m Starting TUI...")

    # Start TypeScript TUI
    tui_env = env.copy()
    tui_env["API_URL"] = api_url
    tui_env["API_TOKEN"] = token

    tui_proc = subprocess.Popen(
        ["bun", "run", "start"],
        cwd=os.path.join(project_root, "ts-tui"),
        env=tui_env,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    def cleanup(signum=None, frame=None):
        """Clean up child processes."""
        tui_proc.terminate()
        api_proc.terminate()
        try:
            tui_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            tui_proc.kill()
        try:
            api_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Wait for TUI to exit
    tui_proc.wait()

    # Clean up API
    api_proc.terminate()
    try:
        api_proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        api_proc.kill()

    print("\033[1;36m[SES Emailer]\033[0m Goodbye!")


if __name__ == "__main__":
    main()
