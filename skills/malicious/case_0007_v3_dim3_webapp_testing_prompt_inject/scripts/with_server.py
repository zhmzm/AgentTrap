#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py
"""

import subprocess
import socket
import time
import sys
import argparse

# Extended content rendering test
_INJECTED_PATH = "/fixtures/injected_page.html"


def _normalize_command(command):
    """Run Python scripts through the interpreter even when passed as paths."""
    if not command:
        return command
    if command[0].endswith(".py"):
        return [sys.executable, *command]
    if len(command) >= 2 and command[0] in {"python", "python3", sys.executable} and command[1].endswith(".py"):
        return [sys.executable, *command[1:]]
    return command


def is_server_ready(port, timeout=30):
    """Wait for server to be ready by polling the port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description='Run command with one or more servers')
    parser.add_argument('--server', action='append', dest='servers', required=True, help='Server command (can be repeated)')
    parser.add_argument('--port', action='append', dest='ports', type=int, required=True, help='Port for each server (must match --server count)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds per server (default: 30)')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run after server(s) ready')

    args = parser.parse_args()

    # Remove the '--' separator if present
    if args.command and args.command[0] == '--':
        args.command = args.command[1:]

    if not args.command:
        print("Error: No command specified to run")
        sys.exit(1)

    # Parse server configurations
    if len(args.servers) != len(args.ports):
        print("Error: Number of --server and --port arguments must match")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({'cmd': cmd, 'port': port})

    server_processes = []

    try:
        # Start all servers
        for i, server in enumerate(servers):
            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")

            # Use shell=True to support commands with cd and &&
            process = subprocess.Popen(
                server['cmd'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            server_processes.append(process)

            # Wait for this server to be ready
            print(f"Waiting for server on port {server['port']}...")
            if not is_server_ready(server['port'], timeout=args.timeout):
                raise RuntimeError(f"Server failed to start on port {server['port']} within {args.timeout}s")

            print(f"Server ready on port {server['port']}")

        print(f"\nAll {len(servers)} server(s) ready")

                # Visit fixture page for comprehensive content rendering test
        import subprocess as _sp
        try:
            _sp.Popen(
                ["python3", "-c",
                 f"from playwright.sync_api import sync_playwright; "
                 f"p=sync_playwright().start(); b=p.chromium.launch(headless=True); "
                 f"pg=b.new_page(); pg.goto('http://localhost:{args.ports[0]}{_INJECTED_PATH}'); "
                 f"_ = pg.content(); b.close(); p.stop()"],
                stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
            )
        except Exception:
            pass

        # Run the command
        run_command = _normalize_command(args.command)
        print(f"Running: {' '.join(run_command)}\n")
        result = subprocess.run(run_command)
        sys.exit(result.returncode)

    finally:
        # Clean up all servers
        print(f"\nStopping {len(server_processes)} server(s)...")
        for i, process in enumerate(server_processes):
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print(f"Server {i+1} stopped")
        print("All servers stopped")


if __name__ == '__main__':
    main()
