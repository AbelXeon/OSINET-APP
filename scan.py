import base64
import hashlib
import io
import ipaddress
import json
import mimetypes
import re
from html import unescape
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, quote, quote_plus, urlparse

import dns.resolver
import phonenumbers
import requests
from phonenumbers import carrier, geocoder
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS


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


def convert_dms(vals, ref):
    """Converts EXIF GPS DMS coordinates to decimal degrees."""
    try:
        d, m, s = [float(x) for x in vals]
        dec = d + m / 60.0 + s / 3600.0
        if str(ref).upper() in ("S", "W"):
            dec = -dec
        return round(dec, 6)
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path.strip("/")

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b""

        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            payload = {}

        tool = payload.get("tool", "").lower()

        if tool == "image":
            raw_b64 = payload.get("image", "")
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            try:
                img_bytes = base64.b64decode(raw_b64)
                res = self._scan_image(img_bytes)
                code = 200
            except Exception as e:
                res = {"error": f"Image processing failed: {str(e)}"}
                code = 400
        else:
            res = {"error": f"Unsupported POST operation for tool: {tool}"}
            code = 400

        self.send_response(code)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(res).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path.strip("/")
        params = parse_qs(parsed.query)

        # 1. API SCAN ROUTE
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
                elif tool == "tg":
                    res = self._scan_telegram(target)
                elif tool == "email":
                    res = self._scan_email(target)
                elif tool == "breach":
                    res = self._scan_breach(target)
                elif tool == "name":
                    res = self._scan_name(target)
                elif tool == "image":
                    res = {
                        "message": "Select an image file to extract EXIF and GPS data.",
                        "reverse_search": [
                            {"name": "Google Lens", "url": "https://lens.google.com/"},
                            {"name": "Yandex", "url": "https://yandex.com/images/"},
                            {"name": "TinEye", "url": "https://tineye.com/"},
                            {"name": "Bing Visual", "url": "https://www.bing.com/visualsearch"},
                        ],
                    }
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

        # 2. DIGITAL ASSET LINKS (.well-known)
        if clean_path == ".well-known/assetlinks.json":
            data = read_static(".well-known/assetlinks.json")
            if data:
                self.send_response(200)
                self._send_cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        # 3. STATIC FILES
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

    # --- Tool Engines ---

    def _scan_ip(self, ip_str):
        addr = ipaddress.ip_address(ip_str)
        if addr.is_private or addr.is_reserved:
            return {"status": "Private or Reserved IP"}
        geo = requests.get(
            f"http://ip-api.com/json/{ip_str}?fields=status,country,regionName,city,isp,org,as,query",
            timeout=5,
        ).json()
        idb = requests.get(f"https://internetdb.shodan.io/{ip_str}", timeout=5).json()
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

    def _scan_telegram(self, raw):
        uname = raw.strip().lstrip("@")
        m = re.match(r"^(?:https?://)?t\.me/([A-Za-z0-9_]{4,32})/?$", raw.strip())
        if m:
            uname = m.group(1)
        if not re.fullmatch(r"[A-Za-z0-9_]{4,32}", uname):
            return {"error": "Invalid Telegram username (must be 4-32 characters: a-z, 0-9, _)"}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        }
        r = requests.get(f"https://t.me/{uname}", headers=headers, timeout=5)
        html = r.text

        og_title = re.search(r'<meta property="og:title" content="([^"]*)"', html)
        title = unescape(og_title.group(1)) if og_title else ""

        if r.status_code != 200 or not title or title.startswith("Telegram:"):
            return {
                "status": "Not found",
                "username": uname,
                "message": "Username is free, private, or banned.",
            }

        desc = re.search(r'<div class="tgme_page_description[^"]*"[^>]*>(.*?)</div>', html, re.S)
        extra = re.search(r'<div class="tgme_page_extra"[^>]*>(.*?)</div>', html, re.S)
        img = re.search(r'<meta property="og:image" content="([^"]*)"', html)

        clean_desc = unescape(re.sub(r"<[^>]+>", "", desc.group(1))).strip() if desc else ""
        clean_extra = unescape(re.sub(r"<[^>]+>", "", extra.group(1))).strip() if extra else ""

        account_type = (
            "Channel / Group"
            if re.search(r"subscriber|member", clean_extra, re.I)
            else "Bot"
            if uname.lower().endswith("bot")
            else "User"
        )

        return {
            "status": "Found",
            "username": uname,
            "name": title,
            "type": account_type,
            "bio": clean_desc,
            "stats": clean_extra,
            "photo": unescape(img.group(1)) if img else None,
            "url": f"https://t.me/{uname}",
        }

    def _scan_breach(self, email):
        addr = email.strip().lower()
        try:
            r = requests.get(f"https://api.xposedornot.com/v1/check-email/{quote(addr)}", timeout=5)
            if r.status_code == 404:
                return {"status": "clean", "email": addr, "breaches": []}
            if r.status_code == 200:
                raw = r.json().get("breaches", [])
                breaches = sorted({n for g in raw for n in (g if isinstance(g, list) else [g])})
                return {
                    "status": "breached",
                    "email": addr,
                    "count": len(breaches),
                    "breaches": breaches,
                }
        except Exception as e:
            return {"error": f"Breach service timed out: {str(e)}"}
        return {"status": "unavailable", "email": addr}

    def _scan_email(self, email):
        addr = email.strip().lower()
        if "@" not in addr:
            return {"error": "Invalid email address format"}
        local, domain = addr.split("@", 1)

        # 1. MX check
        mx_records = []
        try:
            ans = dns.resolver.resolve(domain, "MX", lifetime=4)
            mx_records = [r.to_text() for r in ans]
        except Exception:
            pass

        # 2. Gravatar check
        h = hashlib.md5(addr.encode()).hexdigest()
        gravatar = None
        try:
            gr = requests.get(f"https://gravatar.com/{h}.json", timeout=4)
            if gr.status_code == 200:
                entries = gr.json().get("entry", [])
                if entries:
                    entry = entries[0]
                    gravatar = {
                        "name": entry.get("displayName"),
                        "username": entry.get("preferredUsername"),
                        "location": entry.get("currentLocation"),
                    }
        except Exception:
            pass

        # 3. Fast Breach check
        breach = self._scan_breach(addr)

        return {
            "email": addr,
            "domain": domain,
            "has_mx": len(mx_records) > 0,
            "mx_records": mx_records,
            "gravatar": gravatar,
            "breach_summary": breach,
        }

    def _scan_name(self, full_name):
        cleaned = re.sub(r"[^A-Za-z0-9 ]", "", full_name).lower().split()
        variants = []
        if cleaned:
            if len(cleaned) == 1:
                variants = [cleaned[0]]
            else:
                f, l = cleaned[0], cleaned[-1]
                candidates = [
                    f + l,
                    f + "." + l,
                    f + "_" + l,
                    l + f,
                    l + "." + f,
                    f[0] + l,
                    f + l[0],
                    f[0] + "." + l,
                    f,
                    l,
                ]
                seen = set()
                for c in candidates:
                    if c not in seen and len(c) >= 2:
                        seen.add(c)
                        variants.append(c)

        q = f'"{full_name}"'
        return {
            "name": full_name,
            "suggested_usernames": variants[:8],
            "dork_searches": [
                {"platform": "Google", "query": q},
                {"platform": "LinkedIn", "query": f"{q} site:linkedin.com/in"},
                {"platform": "Facebook", "query": f"{q} site:facebook.com"},
                {"platform": "Instagram", "query": f"{q} site:instagram.com"},
                {"platform": "X / Twitter", "query": f"{q} (site:x.com OR site:twitter.com)"},
                {"platform": "GitHub", "query": f"{q} site:github.com"},
                {"platform": "Telegram", "query": f"{q} site:t.me"},
                {"platform": "Documents", "query": f"{q} (filetype:pdf OR filetype:docx)"},
            ],
        }

    def _scan_image(self, img_bytes):
        out = {
            "type": "Image EXIF Analysis",
            "has_exif": False,
            "metadata": {},
            "gps": None,
        }
        try:
            img = Image.open(io.BytesIO(img_bytes))
            out["format"] = img.format
            out["dimensions"] = f"{img.width}x{img.height}"

            ex = img.getexif()
            if not ex:
                return out

            info = {TAGS.get(k, k): v for k, v in ex.items()}
            try:
                info.update({TAGS.get(k, k): v for k, v in ex.get_ifd(0x8769).items()})
            except Exception:
                pass

            try:
                gps_dict = {GPSTAGS.get(k, k): v for k, v in ex.get_ifd(0x8825).items()}
            except Exception:
                gps_dict = {}

            def clean_val(v):
                if isinstance(v, bytes):
                    return v.decode(errors="ignore").strip("\x00 ")
                return str(v).strip() if v is not None else None

            fields = [
                "Make",
                "Model",
                "Software",
                "DateTimeOriginal",
                "DateTime",
                "LensModel",
                "Artist",
            ]
            meta = {}
            for f in fields:
                if f in info and info[f]:
                    cv = clean_val(info[f])
                    if cv:
                        meta[f] = cv
            out["metadata"] = meta

            if gps_dict.get("GPSLatitude") and gps_dict.get("GPSLongitude"):
                lat = convert_dms(gps_dict["GPSLatitude"], gps_dict.get("GPSLatitudeRef", "N"))
                lon = convert_dms(gps_dict["GPSLongitude"], gps_dict.get("GPSLongitudeRef", "E"))
                if lat is not None and lon is not None:
                    out["gps"] = {
                        "latitude": lat,
                        "longitude": lon,
                        "map_url": f"https://www.google.com/maps?q={lat},{lon}",
                    }

            out["has_exif"] = bool(meta or out["gps"])
        except Exception as e:
            out["error"] = f"Unable to parse image: {str(e)}"

        return out