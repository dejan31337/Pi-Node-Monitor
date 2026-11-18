import os
import json
import hmac
import subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Load the project .env when the helper is launched directly.
# In the existing C:\\test app layout, .env is one directory above windows-helper.
if not ENV_FILE.exists():
    ENV_FILE = BASE_DIR.parent / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(
                key.strip(), value.strip().strip('"').strip("'")
            )

TOKEN = os.getenv("NODE_STATUS_TOKEN", "")
CONTAINER = os.getenv("NODE_CONTAINER", "testnet2")
PORT = 18766

SERVICES = ("horizon", "postgresql", "stellar-core", "rpc")
ACTIONS = ("start", "stop", "restart")
LOG_LINE_OPTIONS = {
    "100": 16000,
    "250": 40000,
    "500": 80000,
    "1000": 160000,
}

STATUS_COMMAND = [
    "docker", "exec", CONTAINER, "node-status",
    "--services", "--protocol", "--horizon", "--peers", "--system"
]


def run_command(command, timeout=45):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()

        if result.returncode != 0:
            return {
                "ok": False,
                "error": error or output or
                         "Command failed: " + str(result.returncode)
            }

        return {"ok": True, "output": output, "stderr": error}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Command timed out"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def supervisor_command(*args, timeout=45):
    result = run_command([
        "docker", "exec", CONTAINER, "supervisorctl", *args
    ], timeout=timeout)
    if args and args[0] == "status" and result.get("output", "").strip():
        result["ok"] = True
        result.pop("error", None)
    return result


def supervisor_logs(service, lines):
    if service not in SERVICES:
        return {"ok": False, "error": "Invalid service"}
    if lines not in LOG_LINE_OPTIONS:
        return {"ok": False, "error": "Invalid log length"}

    # supervisorctl tail -c takes a byte count, not a line count. The
    # selected values provide a practical output window; actual line count
    # depends on each service's log message length.
    byte_count = str(LOG_LINE_OPTIONS[lines])
    result = supervisor_command("tail", "-" + byte_count, service, timeout=30)
    if not result.get("ok"):
        return result

    output = result.get("output", "")
    if not output:
        return {
            "ok": True,
            "output": "",
            "message": "No log output is currently available for " + service + "."
        }
    return {
        "ok": True,
        "output": output,
        "message": "Latest Supervisor output for " + service +
                   " (output window sized for approximately " + lines + " lines)."
    }


class Handler(BaseHTTPRequestHandler):

    def send_json(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        supplied = self.headers.get("Authorization", "")
        expected = "Bearer " + TOKEN
        return bool(TOKEN) and hmac.compare_digest(supplied, expected)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json(200, {
                "ok": True, "service": "windows-helper"
            })

        if not self.authorized():
            return self.send_json(401, {
                "ok": False, "error": "Unauthorized"
            })

        if path == "/status":
            result = run_command(STATUS_COMMAND, 30)
            if result["ok"]:
                return self.send_json(200, {
                    "ok": True,
                    "status": result["output"],
                    "container": CONTAINER
                })
            return self.send_json(502, result)

        if path == "/services":
            result = supervisor_command("status")
            return self.send_json(200 if result["ok"] else 502, result)

        if path == "/peers":
            result = run_command([
                "docker", "exec", CONTAINER,
                "stellar-core", "http-command", "peers"
            ], 40)
            return self.send_json(200 if result["ok"] else 502, result)

        if path == "/logs":
            params = parse_qs(parsed.query)
            service = (params.get("service", [""])[0] or "").strip()
            lines = (params.get("lines", ["500"])[0] or "500").strip()
            result = supervisor_logs(service, lines)
            return self.send_json(200 if result["ok"] else 502, result)

        return self.send_json(404, {
            "ok": False, "error": "Not found"
        })

    def do_POST(self):
        if not self.authorized():
            return self.send_json(401, {
                "ok": False, "error": "Unauthorized"
            })

        path = urlparse(self.path).path
        parts = path.strip("/").split("/")

        if len(parts) == 3 and parts[0] == "service":
            service, action = parts[1], parts[2]

            if service not in SERVICES:
                return self.send_json(400, {
                    "ok": False, "error": "Invalid service"
                })

            if action not in ACTIONS:
                return self.send_json(400, {
                    "ok": False, "error": "Invalid action"
                })

            result = supervisor_command(action, service)
            return self.send_json(
                200 if result["ok"] else 502, result
            )

        if path in (
            "/services/start",
            "/services/stop",
            "/services/restart"
        ):
            action = path.rsplit("/", 1)[1]
            result = supervisor_command(action, "all")
            return self.send_json(
                200 if result["ok"] else 502, result
            )

        return self.send_json(404, {
            "ok": False, "error": "Not found"
        })

    def log_message(self, fmt, *args):
        print("[Windows Helper] " + (fmt % args), flush=True)


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("NODE_STATUS_TOKEN missing in .env")

    print("Pi Windows Helper starting...")
    print("Listening on 0.0.0.0:18765")

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
