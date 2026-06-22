# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Minimal mock HTTP server that simulates the Authentik API for CI simulation runs.

Start with: python tests/mock_server.py [port]
Default port: 18999
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = 18999
DATA_DIR = Path(__file__).parent / "data" / "api"

# Path → fixture file mapping (no query-param logic needed for these)
ROUTES: dict[str, str] = {
    "/api/v3/flows/instances/": "flows-instances-GET.json",
    "/api/v3/core/groups/": "core-groups-GET.json",
    "/api/v3/stages/invitation/invitations/": "stages-invitation-invitations-GET.json",
}

EMPTY_PAGE: dict = {
    "pagination": {
        "next": 0,
        "previous": 0,
        "count": 0,
        "current": 1,
        "total_pages": 1,
        "start_index": 0,
        "end_index": 0,
    },
    "results": [],
}


class MockAuthentikHandler(BaseHTTPRequestHandler):
    """Route GET requests to fixture files; absorb all writes with a 200/204."""

    def do_GET(self) -> None:
        """Serve GET requests using fixture JSON files."""
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/v3/core/users/":
            if "username" in qs:
                # Username-uniqueness check inside create_invitation → user does not exist yet
                body = json.dumps(EMPTY_PAGE).encode()
            else:
                body = (DATA_DIR / "core-users-GET.json").read_bytes()
        elif path in ROUTES:
            body = (DATA_DIR / ROUTES[path]).read_bytes()
        else:
            body = b"{}"

        self._send(200, body)

    def do_POST(self) -> None:
        """Return a minimal 201 response (POSTs are skipped in dry mode)."""
        self._send(201, b'{"pk": "mock-pk"}')

    def do_DELETE(self) -> None:
        """Return 204 (DELETEs are skipped in dry mode)."""
        self._send(204, b"")

    def do_PATCH(self) -> None:
        """Return 200 (PATCHes are skipped in dry mode)."""
        self._send(200, b"{}")

    def _send(self, code: int, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Print a compact one-liner to stderr instead of the default two-liner."""
        sys.stderr.write(f"[mock] {self.address_string()} {format % args}\n")


def main() -> None:
    """Parse optional port argument and start the mock server."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = HTTPServer(("localhost", port), MockAuthentikHandler)
    # ponytail: flush=True so the CI step that polls readiness sees the line immediately
    print(f"Mock Authentik API listening on http://localhost:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
