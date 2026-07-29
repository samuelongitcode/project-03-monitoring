#!/usr/bin/env python3
"""
Same http.server base as the other demo apps, extended with:
  - /metrics : hand-written Prometheus exposition format (no client
    library needed — this is genuinely what that format looks like)
  - /api/fail : deliberately returns 500 and increments an error counter,
    so you have something real to trigger an alert with
"""
import json
import socketserver
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

PORT = 8000

# Simple in-memory counters, protected by a lock since http.server can be
# hit concurrently. This is the entire "instrumentation" — no library
# needed to understand what Prometheus is actually scraping.
_lock = threading.Lock()
_counters = {"requests_total": 0, "errors_total": 0}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        with _lock:
            _counters["requests_total"] += 1

        if self.path == "/metrics":
            # This IS the Prometheus exposition format — a scraper just
            # GETs this endpoint on a schedule and parses these lines.
            with _lock:
                requests_total = _counters["requests_total"]
                errors_total = _counters["errors_total"]
            body = (
                "# HELP app_requests_total Total requests received\n"
                "# TYPE app_requests_total counter\n"
                f"app_requests_total {requests_total}\n"
                "# HELP app_errors_total Total requests that returned an error\n"
                "# TYPE app_errors_total counter\n"
                f"app_errors_total {errors_total}\n"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if self.path == "/api/fail":
            # A deliberately broken endpoint — this exists ONLY so you
            # have something real to hammer in Phase 3's "trigger the
            # alert on purpose" step.
            with _lock:
                _counters["errors_total"] += 1
            self._send_json({"error": "simulated failure"}, status=500)
            return

        if self.path == "/":
            self._send_json({
                "message": "monitoring demo app",
                "time_utc": datetime.now(timezone.utc).isoformat(),
            })
            return

        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}")


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"monitoring demo app listening on 0.0.0.0:{PORT}")
        httpd.serve_forever()
