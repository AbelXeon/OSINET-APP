import json
import re
import ipaddress
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import dns.resolver
import phonenumbers
from phonenumbers import geocoder, carrier
import requests

class handler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        tool = params.get("tool", [""])[0].lower()
        target = params.get("target", [""])[0].strip()

        if not tool or not target:
            self.send_response(400)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'tool' or 'target' query parameters"}).encode())
            return

        result = {}
        try:
            if tool == "ip":
                result = self._scan_ip(target)
            elif tool == "phone":
                result = self._scan_phone(target)
            elif tool == "domain":
                result = self._scan_domain(target)
            elif tool == "dork":
                result = self._build_dorks(target)
            else:
                result = {"status": "unsupported", "message": f"Tool '{tool}' not routed or handled locally."}

            self.send_response(200)
        except Exception as e:
            self.send_response(500)
            result = {"error": str(e)}

        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _scan_ip(self, ip_str):
        addr = ipaddress.ip_address(ip_str)
        if addr.is_private or addr.is_reserved:
            return {"status": "Private/Reserved IP"}
        
        geo = requests.get(f"http://ip-api.com/json/{ip_str}?fields=status,country,regionName,city,isp,org,as,query", timeout=8).json()
        idb = requests.get(f"https://internetdb.shodan.io/{ip_str}", timeout=8).json()
        return {
            "type": "IP Intelligence",
            "geolocation": geo,
            "exposure": {
                "open_ports": idb.get("ports", []),
                "hostnames": idb.get("hostnames", []),
                "vulns": idb.get("vulns", [])
            }
        }

    def _scan_phone(self, raw_number):
        n = phonenumbers.parse(raw_number, "ET")
        return {
            "valid": phonenumbers.is_valid_number(n),
            "country": geocoder.country_name_for_number(n, "en"),
            "region": geocoder.description_for_number(n, "en"),
            "carrier": carrier.name_for_number(n, "en"),
            "e164": phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
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
                {"name": "Pastebin Leaks", "dork": f'{q} site:pastebin.com'},
                {"name": "GitHub Exposure", "dork": f'{q} site:github.com'},
                {"name": "Documents", "dork": f'{q} (filetype:pdf OR filetype:docx)'}
            ]
        }