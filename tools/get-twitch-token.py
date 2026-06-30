#!/usr/bin/env python3
"""
Twitch OAuth Token Generator for Streamlink Twitch GUI
Run this on your PC (not in the container) to get a compatible token.

The token uses Streamlink Twitch GUI's exact client ID, so it will be
accepted by the application.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
import sys

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
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "scopes": " ".join(SCOPES),
    }).encode("utf-8")

    req = urllib.request.Request(DEVICE_CODE_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_for_token(device_code, interval=5, max_attempts=60):
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
                print(f"  Slowing down... (interval={interval}s)")
                continue
            else:
                print(f"Error: {error}", file=sys.stderr)
                return None

    print("Timeout. You did not authorize in time.", file=sys.stderr)
    return None


def main():
    print("=" * 60)
    print("Twitch Token Generator for Streamlink Twitch GUI")
    print("=" * 60)
    print()

    print("Requesting device code from Twitch...")
    device_info = request_device_code()

    user_code = device_info["user_code"]
    verification_uri = device_info["verification_uri"]
    device_code = device_info["device_code"]
    expires_in = device_info["expires_in"]

    print()
    print("-" * 60)
    print("STEP 1: Open this URL in your browser (PC or phone):")
    print(f"  {verification_uri}")
    print()
    print(f"STEP 2: Enter this code: {user_code}")
    print("-" * 60)
    print()
    print(f"You have {expires_in} seconds. Waiting...")
    print()

    result = poll_for_token(device_code)

    if result and "access_token" in result:
        token = result["access_token"]
        print()
        print("=" * 60)
        print("SUCCESS! Here is your token:")
        print("=" * 60)
        print()
        print(token)
        print()
        print("=" * 60)
        print()
        print("How to use it:")
        print("  1. In Streamlink Twitch GUI, click 'Login'")
        print("  2. Click 'Use Access Token' (or 'Zugangscode verwenden')")
        print("  3. Paste the token above")
        print("  4. Click OK / Apply")
        print()
        print("NOTE: If the token starts with 'oauth:', paste WITHOUT that prefix.")
        print("      Paste only the part AFTER 'oauth:' if present.")
        print()
        return 0
    else:
        print()
        print("Failed to get token. Please try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())