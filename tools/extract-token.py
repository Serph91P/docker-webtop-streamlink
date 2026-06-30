#!/usr/bin/env python3
"""
Extract Twitch OAuth token from local Streamlink Twitch GUI config.

Run this on your PC AFTER logging into Streamlink Twitch GUI.
It reads the token from the app's config files.
"""

import json
import os
import sys
import platform


def find_config_dirs():
    """Find Streamlink Twitch GUI config directories on this OS."""
    system = platform.system()
    home = os.path.expanduser("~")
    dirs = []

    if system == "Windows":
        # Windows: could be in Roaming OR Local (portable/installed version)
        appdata_local = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
        appdata_roaming = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        dirs.append(os.path.join(appdata_local, "streamlink-twitch-gui"))
        dirs.append(os.path.join(appdata_roaming, "streamlink-twitch-gui"))
    elif system == "Darwin":
        dirs.append(os.path.join(home, "Library", "Application Support", "streamlink-twitch-gui"))
    else:
        dirs.append(os.path.join(home, ".config", "streamlink-twitch-gui"))

    return dirs


def extract_token(config_dir):
    """Try to find OAuth token in various config files."""
    paths = [
        os.path.join(config_dir, "oauth.json"),
        os.path.join(config_dir, "settings.json"),
        os.path.join(config_dir, "session.json"),
    ]

    for path in paths:
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        # Try various locations for the token
        token = None

        if isinstance(data, dict):
            # Direct token
            if "access_token" in data:
                token = data["access_token"]
            # Nested auth object
            elif "auth" in data and isinstance(data["auth"], dict):
                token = data["auth"].get("access_token")
            # Session object
            elif "session" in data and isinstance(data["session"], dict):
                token = data["session"].get("access_token")
            # user_name + access_token at root
            elif "user_name" in data and "access_token" in data:
                token = data["access_token"]

        if token and isinstance(token, str) and len(token) > 10:
            return token, path

    return None, None


def main():
    print("=" * 60)
    print("Streamlink Twitch GUI Token Extractor")
    print("=" * 60)
    print()

    config_dirs = find_config_dirs()
    print("Checking locations:")
    for d in config_dirs:
        exists = "EXISTS" if os.path.exists(d) else "not found"
        print(f"  {d} [{exists}]")
    print()

    config_dir = None
    for d in config_dirs:
        if os.path.exists(d):
            config_dir = d
            break

    if not config_dir:
        print("ERROR: Config directory not found.")
        print()
        print("Have you installed and logged into Streamlink Twitch GUI on this PC?")
        print("  1. Download from https://github.com/streamlink/streamlink-twitch-gui/releases")
        print("  2. Install and run it")
        print("  3. Log in to Twitch (this will work on your PC)")
        print("  4. Run this script again")
        return 1

    print(f"Using: {config_dir}")
    print()

    token, source = extract_token(config_dir)

    if not token:
        print("ERROR: No OAuth token found in config files.")
        print()
        print("Files checked:")
        for name in ["oauth.json", "settings.json", "session.json"]:
            path = os.path.join(config_dir, name)
            exists = "EXISTS" if os.path.exists(path) else "NOT FOUND"
            print(f"  {name}: {exists}")
        print()
        print("Are you logged in? Try logging in again in Streamlink Twitch GUI.")
        return 1

    print("SUCCESS! Token found:")
    if source:
        print(f"  Source: {os.path.basename(source)}")
    print()
    print("=" * 60)
    print("YOUR TOKEN (copy this):")
    print("=" * 60)
    print()
    print(token)
    print()
    print("=" * 60)
    print()
    print("In the container's Streamlink Twitch GUI:")
    print("  1. Click 'Login'")
    print("  2. Click 'Use Access Token' (or 'Zugangscode verwenden')")
    print("  3. Paste the token above")
    print("  4. Click OK")
    print()
    print("NOTE: The token is tied to your Twitch account.")
    print("      It will remain valid for about 60 days.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
