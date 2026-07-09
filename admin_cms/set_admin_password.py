#!/usr/bin/env python3
"""Bootstrap or reset the Admin CMS password.

Usage:
    python3 admin_cms/set_admin_password.py [<new-password>]

Without an argument, prompts interactively (hidden input).
Writes admin_cms/admin_config.json with a fresh bcrypt hash and a random
secret_key (generated if not already present). Idempotent: existing
secret_key is preserved so live sessions don't get invalidated.
"""

import getpass
import json
import os
import secrets
import sys

import bcrypt

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_config.json")


def load():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_PATH, 0o600)


def main():
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("New admin password: ")
        confirm = getpass.getpass("Confirm: ")
        if password != confirm:
            print("ERROR: passwords do not match", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print("ERROR: password must be at least 8 characters", file=sys.stderr)
        sys.exit(1)

    config = load()
    if "secret_key" not in config:
        config["secret_key"] = secrets.token_hex(32)
    config["password_hash"] = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    config["failed_attempts"] = 0
    config["lockout_until"] = 0
    save(config)

    print(f"OK: password set. Config at {CONFIG_PATH} (chmod 600)")


if __name__ == "__main__":
    main()
