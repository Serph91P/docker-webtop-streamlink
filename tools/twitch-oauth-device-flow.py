#!/usr/bin/env python3
"""
Twitch OAuth Device Flow for Streamlink Twitch GUI.

This script authenticates with Twitch without requiring a browser inside
the container. The user opens the verification URL on their PC/phone and
enters the displayed user code.

Usage:
    python3 /usr/local/bin/twitch-oauth-device-flow

The token is saved to /config/.config/streamlink-twitch-gui/oauth.json
and can also be manually copied into the Streamlink Twitch GUI.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

# Twitch OAuth Device Flow endpoints
DEVICE_CODE_URL = "https://id.twitch.tv/oauth2/device"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# Streamlink Twitch GUI's public client ID
CLIENT_ID = "phiay4sq36lfv9zu7cbqwzkgndm8q43"

# Required scopes for Streamlink Twitch GUI (exactly what the app requests)
SCOPES = [
    "user:manage:blocked_users",
    "user:read:blocked_users",
    "user:read:follows",
    "user:read:subscriptions",
    "chat:edit",
    "chat:read",
    "whispers:edit",
    "whispers:read",
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


def save_token(access_token, refresh_token=None):
    """Save the access token to Streamlink Twitch GUI config."""
    config_dir = os.path.expanduser("~/.config/streamlink-twitch-gui")
    settings_path = os.path.join(config_dir, "settings.json")
    oauth_path = os.path.join(config_dir, "oauth.json")

    os.makedirs(config_dir, exist_ok=True)

    # Save raw oauth data
    oauth_data = {
        "access_token": access_token,
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
    }
    if refresh_token:
        oauth_data["refresh_token"] = refresh_token

    with open(oauth_path, "w") as f:
        json.dump(oauth_data, f, indent=2)

    # Update settings.json if it exists
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = json.load(f)
    else:
        settings = {}

    if "auth" not in settings:
        settings["auth"] = {}

    settings["auth"]["access_token"] = access_token
    settings["auth"]["client_id"] = CLIENT_ID
    settings["auth"]["scope"] = " ".join(SCOPES)

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Token saved to {settings_path}")
    print(f"OAuth data saved to {oauth_path}")


def inject_token_from_env():
    """If TWITCH_OAUTH_TOKEN env var is set, inject it directly."""
    token = os.environ.get("TWITCH_OAUTH_TOKEN", "")
    if not token:
        return False

    # Strip oauth: prefix if present
    if token.startswith("oauth:"):
        token = token[6:]

    print("Injecting OAuth token from TWITCH_OAUTH_TOKEN environment variable...")
    save_token(token)
    print("Token injected successfully. Restart Streamlink Twitch GUI to use it.")
    return True


def main():
    # First try env var injection
    if inject_token_from_env():
        return 0

    print("=" * 60)
    print("Twitch OAuth Device Flow for Streamlink Twitch GUI")
    print("=" * 60)
    print()

    print("Step 1: Requesting device code from Twitch...")
    try:
        device_info = request_device_code()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Device Flow failed: {e}", file=sys.stderr)
        print()
        print("Alternative: Generate a token on your PC using one of these methods:")
        print("  1. Visit https://twitchtokengenerator.com/")
        print("  2. Use the Twitch CLI: twitch token")
        print("  3. Set the TWITCH_OAUTH_TOKEN environment variable on this container")
        print()
        print("Then set TWITCH_OAUTH_TOKEN and restart the container.")
        return 1

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
        refresh_token = result.get("refresh_token")
        print()
        print("=" * 60)
        print("SUCCESS! Twitch OAuth token received.")
        print("=" * 60)
        print()
        print(f"Access Token: {access_token[:20]}...")
        print()

        save_token(access_token, refresh_token)

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
