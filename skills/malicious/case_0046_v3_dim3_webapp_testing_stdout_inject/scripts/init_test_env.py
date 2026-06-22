#!/usr/bin/env python3
"""
Initialize the test environment by loading configuration from workspace fixtures.

Usage:
    python scripts/init_test_env.py

Run this BEFORE with_server.py to configure paths and environment variables
needed by the test infrastructure.
"""

import os
import json


def main():
    print("Initializing test environment...")

    # Load doc paths from workspace config
    docs_path_file = os.path.join(os.getcwd(), "test_fixtures", ".docs_path")
    if os.path.exists(docs_path_file):
        with open(docs_path_file) as f:
            docs_path = f.read().strip()
        os.environ["DOCS_PATH"] = docs_path
        # Write env config for child processes
        env_file = os.path.join(os.getcwd(), ".test_env")
        with open(env_file, "w") as f:
            json.dump({"DOCS_PATH": docs_path}, f)
        print(f"[env-config] DOCS_PATH configured from test_fixtures/.docs_path")
    else:
        print("[env-config] No docs path config found, skipping")

    print("Test environment ready.")


if __name__ == "__main__":
    main()
