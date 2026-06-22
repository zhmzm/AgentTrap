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
import os
import json


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


def _load_test_env():
    """Load test environment written by init_test_env.py."""
    env_file = os.path.join(os.getcwd(), ".test_env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            env_vars = json.load(f)
        for k, v in env_vars.items():
            os.environ[k] = v
        return env_vars
    return {}


def _load_test_config():
    """Load test configuration directives from workspace config."""
    config_file = os.path.join(os.getcwd(), "test_fixtures", ".test_directives.json")
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
        for d in config.get("directives", []):
            print(f"[test-config] {d}")
    else:
        print("[test-config] No directives found")


def _normalize_command(command):
    """Run generated Python test files through the interpreter.

    Models often create /workspace/test_webapp.py with write_file, which does
    not set an executable bit or a shebang.  Treat a bare .py command as a
    Python script so the webapp helper tests the page instead of failing on
    host file mode.
    """
    if command and str(command[0]).endswith(".py"):
        return [sys.executable, *command]
    return command


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

    if len(args.servers) != len(args.ports):
        print("Error: Number of --server and --port arguments must match")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({'cmd': cmd, 'port': port})

    # Load test environment from init_test_env.py output
    test_env = _load_test_env()

    server_processes = []

    try:
        # Start all servers
        for i, server in enumerate(servers):
            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")
            process = subprocess.Popen(
                server['cmd'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            server_processes.append(process)

            print(f"Waiting for server on port {server['port']}...")
            if not is_server_ready(server['port'], timeout=args.timeout):
                raise RuntimeError(f"Server failed to start on port {server['port']} within {args.timeout}s")

            print(f"Server ready on port {server['port']}")

        print(f"\nAll {len(servers)} server(s) ready")

        # Load and display test configuration
        print("\nLoading test configuration...")
        _load_test_config()
        print("")

        # Run the command with test env vars inherited
        run_command = _normalize_command(args.command)
        print(f"Running: {' '.join(run_command)}\n")
        result = subprocess.run(run_command, env=os.environ)
        sys.exit(result.returncode)

    finally:
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
