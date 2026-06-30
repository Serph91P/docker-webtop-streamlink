#!/usr/bin/env python3
"""
Twitch OAuth Token Generator for Streamlink Twitch GUI
Run this on your PC (not in the container) to get a compatible token.
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

# Exact scopes the GUI requires
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

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


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
                print(f"  Waiting... ({attempt + 1}/{max_attempts})")
                continue
            elif error == "slow_down":
                interval += 5
                continue
            else:
                print(f"Error: {error}", file=sys.stderr)
                return None

    print("Timeout.", file=sys.stderr)
    return None


def main():
    print("=" * 60)
    print("Twitch Token Generator for Streamlink Twitch GUI")
    print("=" * 60)
    print()

    device_info = request_device_code()

    user_code = device_info["user_code"]
    verification_uri = device_info["verification_uri"]
    device_code = device_info["device_code"]

    print("-" * 60)
    print("STEP 1: Open this URL in your browser:")
    print(f"  {verification_uri}")
    print()
    print(f"STEP 2: Enter this code: {user_code}")
    print("-" * 60)
    print()
    print("Waiting for authorization...")
    print()

    result = poll_for_token(device_code)

    if result and "access_token" in result:
        token = result["access_token"]
        print()
        print("=" * 60)
        print("SUCCESS! Copy this token:")
        print("=" * 60)
        print()
        print(token)
        print()
        print("=" * 60)
        print()
        print("In Streamlink Twitch GUI:")
        print("  Login -> 'Zugangscode verwenden'")
        print("  Paste the token above")
        print()
        return 0
    else:
        print("Failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())