#!/usr/bin/env python3
"""
Extract Twitch OAuth token from local Streamlink Twitch GUI config.

Run this on your PC AFTER logging into Streamlink Twitch GUI.
It searches the app's config files (including LevelDB localStorage).
"""

import json
import os
import re
import sys
import platform

# Token pattern: exactly 30 alphanumeric chars
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]{30}")


def find_config_dirs():
    """Find Streamlink Twitch GUI config directories on this OS."""
    system = platform.system()
    home = os.path.expanduser("~")
    dirs = []

    if system == "Windows":
        appdata_local = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
        appdata_roaming = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        dirs.append(os.path.join(appdata_local, "streamlink-twitch-gui"))
        dirs.append(os.path.join(appdata_roaming, "streamlink-twitch-gui"))
    elif system == "Darwin":
        dirs.append(os.path.join(home, "Library", "Application Support", "streamlink-twitch-gui"))
    else:
        dirs.append(os.path.join(home, ".config", "streamlink-twitch-gui"))

    return dirs


def search_file_for_token(filepath):
    """Search a single file for token-like strings."""
    try:
        with open(filepath, "rb") as f:
            content = f.read()
    except (OSError, IOError):
        return []

    # Try decoding as UTF-8, skip errors
    try:
        text = content.decode("utf-8", errors="ignore")
    except:
        return []

    # Find all 30-char alphanumeric sequences
    matches = TOKEN_PATTERN.findall(text)

    # Filter: look for 'access_token' or 'auth' nearby (within 200 chars)
    results = []
    for match in matches:
        idx = text.find(match)
        if idx == -1:
            continue
        context = text[max(0, idx - 200):min(len(text), idx + 200)]
        if "access_token" in context or "auth" in context or "oauth" in context:
            results.append(match)

    return results


def extract_token_from_json(config_dir):
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

        token = None
        if isinstance(data, dict):
            if "access_token" in data:
                token = data["access_token"]
            elif "auth" in data and isinstance(data["auth"], dict):
                token = data["auth"].get("access_token")
            elif "session" in data and isinstance(data["session"], dict):
                token = data["session"].get("access_token")

        if token and isinstance(token, str) and len(token) >= 20:
            return token, path

    return None, None


def search_all_files(config_dir):
    """Recursively search all files for token patterns."""
    tokens_found = []

    for root, dirs, files in os.walk(config_dir):
        # Skip large files and caches
        for filename in files:
            filepath = os.path.join(root, filename)

            # Skip obvious non-interesting files
            if filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".ico", ".exe", ".dll")):
                continue

            # Skip files larger than 10MB
            try:
                size = os.path.getsize(filepath)
                if size > 10 * 1024 * 1024:
                    continue
            except OSError:
                continue

            matches = search_file_for_token(filepath)
            for match in matches:
                # Show relative path
                rel_path = os.path.relpath(filepath, config_dir)
                tokens_found.append((match, rel_path))

    return tokens_found


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

    # First try JSON files
    token, source = extract_token_from_json(config_dir)

    if token:
        print("SUCCESS! Token found in JSON:")
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
        return 0

    # Fallback: search all files including LevelDB
    print("No JSON files found. Searching LevelDB and other files...")
    print("(This may take a few seconds)")
    print()

    tokens_found = search_all_files(config_dir)

    if not tokens_found:
        print("ERROR: No OAuth token found.")
        print()
        print("Are you sure you are logged in?")
        print("Try logging in again in Streamlink Twitch GUI.")
        return 1

    # Remove duplicates, keep first occurrence
    seen = set()
    unique_tokens = []
    for token, path in tokens_found:
        if token not in seen:
            seen.add(token)
            unique_tokens.append((token, path))

    if len(unique_tokens) == 1:
        token, path = unique_tokens[0]
        print("SUCCESS! Token found:")
        print(f"  Source: {path}")
        print()
        print("=" * 60)
        print("YOUR TOKEN (copy this):")
        print("=" * 60)
        print()
        print(token)
        print()
    else:
        print(f"Found {len(unique_tokens)} potential tokens:")
        print()
        for i, (token, path) in enumerate(unique_tokens[:5], 1):
            print(f"  {i}. {token}")
            print(f"     Found in: {path}")
            print()
        print("Try them one by one in Streamlink Twitch GUI.")
        print("The correct one is usually the first.")
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
