#!/usr/bin/env python3
"""
Twitch OAuth Device Flow for Streamlink Twitch GUI.

This script authenticates with Twitch without requiring a browser inside
the container. The user opens the verification URL on their PC/phone and
enters the displayed user code.

Usage:
    python3 twitch-oauth-device-flow.py

The token is saved to ~/.config/streamlink-twitch-gui/settings.json
and can also be manually copied into the Streamlink Twitch GUI.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse

# Twitch OAuth Device Flow endpoints
DEVICE_CODE_URL = "https://id.twitch.tv/oauth2/device"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# Streamlink Twitch GUI's public client ID
# This is the same client ID the app uses for OAuth
CLIENT_ID = "phiay4sq36lfv9zu7cbqwzkgndm8q43"

# Required scopes for Streamlink Twitch GUI
SCOPES = [
    "user:read:email",
    "user:read:follows",
    "user:edit:follows",
    "user:read:subscriptions",
    "chat:read",
    "chat:edit",
]


def request_device_code():
    """Request a device code from Twitch."""
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "scopes": " ".join(SCOPES),
    }).encode("utf-8")

    req = urllib.request.Request(DEVICE_CODE_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"Error requesting device code: {e.code} {body}", file=sys.stderr)
        sys.exit(1)


def poll_for_token(device_code, interval=5, max_attempts=60):
    """Poll Twitch for the access token after user authorization."""
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }).encode("utf-8")

    for attempt in range(max_attempts):
        time.sleep(interval)

        req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode("utf-8"))
            error = body.get("message", body.get("error", "unknown"))

            if error == "authorization_pending":
                print(f"  Waiting for authorization... ({attempt + 1}/{max_attempts})")
                continue
            elif error == "slow_down":
                interval += 5
                print(f"  Slowing down polling... (interval={interval}s)")
                continue
            else:
                print(f"Error polling token: {error}", file=sys.stderr)
                return None

    print("Timeout: User did not authorize within the time limit.", file=sys.stderr)
    return None


def save_token_to_settings(access_token):
    """Save the access token to Streamlink Twitch GUI settings."""
    config_dir = os.path.expanduser("~/.config/streamlink-twitch-gui")
    settings_path = os.path.join(config_dir, "settings.json")

    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    # Load existing settings or create new
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = json.load(f)
    else:
        settings = {}

    # Update auth settings
    if "auth" not in settings:
        settings["auth"] = {}

    settings["auth"]["access_token"] = access_token
    settings["auth"]["client_id"] = CLIENT_ID
    settings["auth"]["scope"] = " ".join(SCOPES)

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Token saved to {settings_path}")


def main():
    print("=" * 60)
    print("Twitch OAuth Device Flow for Streamlink Twitch GUI")
    print("=" * 60)
    print()

    print("Step 1: Requesting device code from Twitch...")
    device_info = request_device_code()

    user_code = device_info["user_code"]
    verification_uri = device_info["verification_uri"]
    device_code = device_info["device_code"]
    expires_in = device_info["expires_in"]

    print()
    print("-" * 60)
    print("IMPORTANT: Open this URL on your PC or phone:")
    print(f"  {verification_uri}")
    print()
    print(f"Enter this code: {user_code}")
    print("-" * 60)
    print()
    print(f"You have {expires_in} seconds to authorize.")
    print("Waiting for you to complete the authorization...")
    print()

    result = poll_for_token(device_code)

    if result and "access_token" in result:
        access_token = result["access_token"]
        print()
        print("=" * 60)
        print("SUCCESS! Twitch OAuth token received.")
        print("=" * 60)
        print()
        print(f"Access Token: {access_token[:20]}...")
        print()

        # Save to settings
        save_token_to_settings(access_token)

        print()
        print("The token has been saved to Streamlink Twitch GUI settings.")
        print("Restart the app if it's already running.")
        print()
        print("Alternatively, you can manually enter this token in the GUI:")
        print("  Login -> Use Access Token")
        print()

        return 0
    else:
        print()
        print("Failed to get token. Please try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
