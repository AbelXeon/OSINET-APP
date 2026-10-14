import ipaddress
import json
import mimetypes
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import dns.resolver
import phonenumbers
import requests
from phonenumbers import carrier, geocoder


def read_static(filename: str) -> bytes | None:
    """Finds and reads static files whether running locally or on Vercel."""
    candidates = [
        Path(__file__).resolve().parent / filename,
        Path(".") / filename,
        Path(__file__).resolve().parent / ".." / filename,
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p.read_bytes()
    return None


class handler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path.strip("/")
        params = parse_qs(parsed.query)

        # 1. API SCAN ROUTE (Triggered by EXECUTE button)
        if clean_path.startswith("api") or ("tool" in params and "target" in params):
            tool = params.get("tool", [""])[0].lower()
            target = params.get("target", [""])[0].strip()

            if not tool or not target:
                self.send_response(400)
                self._send_cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Provide tool and target"}).encode())
                return

            try:
                if tool == "ip":
                    res = self._scan_ip(target)
                elif tool == "phone":
                    res = self._scan_phone(target)
                elif tool == "domain":
                    res = self._scan_domain(target)
                elif tool == "dork":
                    res = self._build_dorks(target)
                else:
                    res = {"status": "unsupported", "tool": tool}
                code = 200
            except Exception as e:
                res = {"error": str(e)}
                code = 500

            self.send_response(code)
            self._send_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode())
            return

        # 2. STATIC FILES & DASHBOARD (Root, Manifest, SW, Icons)
        file_name = clean_path if clean_path else "index.html"
        data = read_static(file_name)

        if data is None and clean_path in ("", "index", "index.html"):
            data = read_static("index.html")

        if data is not None:
            mime, _ = mimetypes.guess_type(file_name)
            if not mime:
                if file_name.endswith(".json"):
                    mime = "application/manifest+json; charset=utf-8"
                elif file_name.endswith(".js"):
                    mime = "application/javascript; charset=utf-8"
                else:
                    mime = "text/html; charset=utf-8"

            self.send_response(200)
            self._send_cors()
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"File not found")

    def _scan_ip(self, ip_str):
        addr = ipaddress.ip_address(ip_str)
        if addr.is_private or addr.is_reserved:
            return {"status": "Private or Reserved IP"}
        geo = requests.get(
            f"http://ip-api.com/json/{ip_str}?fields=status,country,regionName,city,isp,org,as,query",
            timeout=8,
        ).json()
        idb = requests.get(f"https://internetdb.shodan.io/{ip_str}", timeout=8).json()
        return {
            "type": "IP Intelligence",
            "geolocation": geo,
            "exposure": {
                "open_ports": idb.get("ports", []),
                "hostnames": idb.get("hostnames", []),
                "vulns": idb.get("vulns", []),
            },
        }

    def _scan_phone(self, raw):
        n = phonenumbers.parse(raw, "ET")
        return {
            "valid": phonenumbers.is_valid_number(n),
            "country": geocoder.country_name_for_number(n, "en"),
            "region": geocoder.description_for_number(n, "en"),
            "carrier": carrier.name_for_number(n, "en"),
            "e164": phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(
                n, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
        }

    def _scan_domain(self, d):
        clean_d = d.removeprefix("https://").removeprefix("http://").split("/")[0]
        records = {}
        for rtype in ["A", "MX", "NS", "TXT"]:
            try:
                ans = dns.resolver.resolve(clean_d, rtype, lifetime=4)
                records[rtype] = [r.to_text() for r in ans]
            except Exception:
                records[rtype] = []
        return {"domain": clean_d, "dns": records}

    def _build_dorks(self, target):
        q = f'"{target}"'
        return {
            "target": target,
            "queries": [
                {"name": "Exact Match", "dork": q},
                {"name": "Pastebin Leaks", "dork": f"{q} site:pastebin.com"},
                {"name": "GitHub Exposure", "dork": f"{q} site:github.com"},
                {"name": "Documents", "dork": f"{q} (filetype:pdf OR filetype:docx)"},
            ],
        }