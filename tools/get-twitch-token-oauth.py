#!/usr/bin/env python3
"""
Twitch OAuth Token Generator for Streamlink Twitch GUI
Run this on your PC. It starts a local web server, opens Twitch OAuth
in your browser, and captures the access token from the redirect.
"""

import json
import sys
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

CLIENT_ID = "phiay4sq36lfv9zu7cbqwzkgndm8q43"
REDIRECT_URI = "http://localhost:17563/callback"
PORT = 17563

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

token_result = {"token": None, "done": threading.Event()}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        # OAuth implicit grant returns token in fragment (browser-side)
        # We serve a page that extracts it via JavaScript and sends to /token
        if parsed.path == "/callback":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
<!DOCTYPE html>
<html>
<head><title>Twitch OAuth</title></head>
<body>
<h2>Processing Twitch login...</h2>
<p>If you see this, check your terminal for the token.</p>
<script>
// Extract token from URL fragment and send to server
var hash = window.location.hash;
if (hash) {
    fetch('/token' + hash.replace('#', '?'));
    document.body.innerHTML = '<h2>Token captured!</h2><p>You can close this window.</p>';
} else {
    document.body.innerHTML = '<h2>No token found</h2><p>Something went wrong.</p>';
}
</script>
</body>
</html>
""")
            return
        
        if parsed.path == "/token":
            params = parse_qs(parsed.query)
            if "access_token" in params:
                token_result["token"] = params["access_token"][0]
                token_result["done"].set()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return
        
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    print("=" * 60)
    print("Twitch OAuth Token Generator for Streamlink Twitch GUI")
    print("=" * 60)
    print()

    # Build OAuth URL
    scope_str = " ".join(SCOPES)
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=token"
        f"&scope={scope_str.replace(' ', '+')}"
    )

    # Start local server
    server = HTTPServer(("localhost", PORT), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Local server started on port {PORT}")
    print()

    # Open browser
    print("Opening Twitch login in your browser...")
    print("If it doesn't open, use this URL:")
    print(f"  {auth_url}")
    print()
    webbrowser.open(auth_url)

    # Wait for token
    print("Waiting for you to log in...")
    if not token_result["done"].wait(timeout=120):
        print()
        print("Timeout. You didn't complete the login.")
        server.shutdown()
        return 1

    server.shutdown()
    token = token_result["token"]

    print()
    print("=" * 60)
    print("SUCCESS! Here is your token:")
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
    print("NOTE: The token expires in about 60 days.")
    print("      You will need to repeat this process then.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())