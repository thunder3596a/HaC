"""Motorola MB8611 driver for DOCSight."""

import hashlib
import logging
import re
from urllib.parse import urlparse

import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.drivers.base import ModemDriver

log = logging.getLogger("docsis.driver.mb8611")


class MB8611Driver(ModemDriver):

    DRIVER_KEY = "mb8611"

    def __init__(self, url: str, user: str, password: str):
        super().__init__(url, user, password)
        self._session = requests.Session()
        self._session.verify = False  # MB8611 uses a self-signed certificate
        self._session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"})
        self._real_base = url.rstrip("/")

    def login(self) -> None:
        """Authenticate via the MB8611 login form."""
        if not self._user and not self._password:
            return
        try:
            # Follow http→https redirect; store only scheme+host as real base
            r = self._session.get(f"{self._url}/", timeout=15, allow_redirects=True)
            r.raise_for_status()
            parsed = urlparse(r.url)
            self._real_base = f"{parsed.scheme}://{parsed.netloc}"

            if "logout" in r.text.lower() and "login" not in r.url.lower():
                return  # already authenticated

            # Parse the login form to find the real action URL and field names
            soup = BeautifulSoup(r.text, "html.parser")
            form = soup.find("form")
            if form:
                action = form.get("action", "/")
                post_url = action if action.startswith("http") else f"{self._real_base}/{action.lstrip('/')}"
                fields = {inp.get("name"): inp.get("value", "") for inp in form.find_all("input") if inp.get("name")}

                # Log raw HTML values BEFORE overwriting (critical: loginPassword may carry a server nonce)
                raw_pass_val = fields.get("loginPassword", "")
                log.warning("MB8611: raw HTML loginPassword -> len=%d repr=%r", len(raw_pass_val), raw_pass_val[:32])
                log.warning("MB8611: raw HTML loginText -> %r", fields.get("loginText", ""))

                # Extract all inline script content and search for doLogin definition
                inline_scripts = soup.find_all("script", src=False)
                full_inline_js = "\n".join(s.get_text() for s in inline_scripts)
                dologin_m = re.search(r'(function\s+doLogin\s*\(.*?\{.*?\})(?=\s*function|\s*$|\s*//)', full_inline_js, re.DOTALL)
                if dologin_m:
                    log.warning("MB8611: doLogin found inline: %r", dologin_m.group(0)[:3000])
                else:
                    log.warning("MB8611: doLogin NOT in inline scripts (total inline JS=%d chars)", len(full_inline_js))
                    log.warning("MB8611: full inline JS: %r", full_inline_js[:5000])

                # Try SOAPAction.js without the ?V=M2 version suffix (modem auth-gates it with suffix)
                for soap_path in ["js/SOAP/SOAPAction.js", "js/SOAPAction.js"]:
                    try:
                        soap_resp = self._session.get(f"{self._real_base}/{soap_path}", timeout=5)
                        soap_len = len(soap_resp.text)
                        if soap_resp.status_code == 200 and soap_len > 100:
                            dologin_in_soap = re.search(r'function\s+doLogin.{0,3000}', soap_resp.text, re.DOTALL)
                            log.warning("MB8611: %s [%d bytes]: doLogin=%r", soap_path, soap_len,
                                        dologin_in_soap.group(0)[:2000] if dologin_in_soap else "(not found)")
                            break
                        else:
                            log.warning("MB8611: %s status=%d len=%d", soap_path, soap_resp.status_code, soap_len)
                    except requests.RequestException as se:
                        log.warning("MB8611: could not fetch %s: %s", soap_path, se)

                sn_token = fields.get("SnToken", "")
                actual_password = hashlib.sha256((self._password + sn_token).encode()).hexdigest() if sn_token else self._password
                log.warning("MB8611: login form action=%s fields=%s sntoken_present=%s", post_url, {k: ("***" if "pass" in k.lower() else v) for k, v in fields.items()}, bool(sn_token))

                user_key = next((k for k in fields if "user" in k.lower() or k.lower() == "username"), None)
                pass_key = next((k for k in fields if "pass" in k.lower() or k.lower() == "password"), None)
                if user_key:
                    fields[user_key] = self._user
                if pass_key:
                    fields[pass_key] = actual_password
                # loginText is a visible plain-text password input (value="Password" is a placeholder);
                # set it to the actual password in case the modem reads this field instead of loginPassword
                if "loginText" in fields:
                    fields["loginText"] = actual_password
                if not user_key or not pass_key:
                    log.warning("MB8611: could not detect credential fields; found: %s", list(fields.keys()))
                    fields["loginUsername"] = self._user
                    fields["loginPassword"] = actual_password
                    fields["loginText"] = actual_password
            else:
                log.warning("MB8611: no form found on login page (url=%s), page length=%d", r.url, len(r.text))
                post_url = f"{self._real_base}/cgi-bin/moto/goform/MotoLogin"
                fields = {"loginUsername": self._user, "loginPassword": self._password}

            r2 = self._session.post(
                post_url, data=fields, timeout=15, allow_redirects=True,
                headers={"Referer": r.url},
            )
            log.warning("MB8611: submitted -> username=%r post_url=%s result=%s", fields.get("loginUsername"), post_url, r2.text[:200].replace("\n", " "))
            # Verify by fetching MotoHome regardless of redirect behaviour
            check = self._session.get(f"{self._real_base}/MotoHome.html", timeout=10)
            log.warning("MB8611: MotoHome check -> status=%s url=%s authenticated=%s", check.status_code, check.url, "logout" in check.text.lower())
            if check.status_code == 200 and "logout" in check.text.lower():
                log.info("MB8611: login confirmed")
            else:
                log.warning("MB8611: login failed — credentials may be wrong or modem requires different auth")
        except requests.RequestException as e:
            raise RuntimeError(f"MB8611: login failed: {e}")

    # Known status page paths across MB8611 firmware versions
    _STATUS_PATHS = [
        "/cmconnectionstatus.html",
        "/DocsisStatus.htm",
        "/RgConnect.asp",
        "/motoconnectionstatus.html",
        "/connection_status.html",
        "/status_docsis.asp",
        "/MotoConnection.html",
        "/MotoStatus.html",
        "/channel_status.html",
        "/docsis_status.html",
    ]

    def _find_status_url(self) -> str | None:
        """Try known paths, then scrape root page links as fallback."""
        found_paths = []
        for path in self._STATUS_PATHS:
            try:
                resp = self._session.get(f"{self._real_base}{path}", timeout=10)
                found_paths.append(f"{path}={resp.status_code}")
                if resp.status_code == 200 and "<table" in resp.text.lower():
                    log.debug("MB8611: status page found at %s", path)
                    return f"{self._real_base}{path}"
            except requests.RequestException as e:
                found_paths.append(f"{path}=ERR({e})")
                continue

        # scrape MotoHome.html (authenticated home) for status page links
        try:
            root = self._session.get(f"{self._real_base}/MotoHome.html", timeout=10)
            # extract all href attrs and any quoted .html/.htm/.asp strings from JS
            all_refs = re.findall(r'["\']([^"\']*\.(?:html?|asp))["\']', root.text, re.IGNORECASE)
            log.warning("MB8611: all page refs found on MotoHome: %s", sorted(set(all_refs)))
            keywords = ("status", "docsis", "connection", "connect", "channel")
            for ref in all_refs:
                if any(kw in ref.lower() for kw in keywords):
                    url = ref if ref.startswith("http") else f"{self._real_base}/{ref.lstrip('/')}"
                    log.info("MB8611: trying discovered ref: %s", url)
                    resp = self._session.get(url, timeout=10)
                    if resp.status_code == 200 and "<table" in resp.text.lower():
                        return url
        except requests.RequestException:
            pass

        log.error("MB8611: path probe results: %s", found_paths)
        return None

    def get_docsis_data(self) -> dict:
        status_url = self._find_status_url()
        if status_url is None:
            raise RuntimeError("MB8611: could not find status page — check DOCSight logs for 'path probe results' and 'page refs found on root' to identify the correct path")
        try:
            r = self._session.get(status_url, timeout=15)
            r.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"MB8611: failed to fetch status page: {e}")

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")

        if len(tables) < 3:
            raise RuntimeError(
                f"MB8611: expected ≥3 tables, found {len(tables)}"
            )

        downstream = self._parse_downstream(tables[1])
        upstream = self._parse_upstream(tables[2])

        return {
            "docsis": "3.1",
            "downstream": downstream,
            "upstream": upstream,
        }

    def get_device_info(self) -> dict:
        return {
            "manufacturer": "Motorola",
            "model": "MB8611",
            "sw_version": "",
        }

    def get_connection_info(self) -> dict:
        return {}

    def _parse_downstream(self, table) -> list:
        rows = table.find_all("tr")
        header_row = _find_header_row(rows)
        if header_row is None:
            return []

        headers = [c.get_text(strip=True).lower() for c in header_row.find_all(["th", "td"])]
        col = _map_ds_columns(headers)
        result = []

        for row in rows:
            if row is header_row:
                continue
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) < 4:
                continue
            if _cell(cells, col["lock_status"]).lower() != "locked":
                continue
            try:
                ch_type = _cell(cells, col["channel_type"]).upper()
                modulation = _normalize_modulation(_cell(cells, col["modulation"]))
                if ch_type == "OFDM":
                    final_type = "ofdm"
                elif modulation:
                    final_type = modulation
                else:
                    final_type = "qam"

                freq = _parse_frequency(_cell(cells, col["frequency"]))
                power = _parse_number(_cell(cells, col["power"]))
                snr = _parse_number(_cell(cells, col["snr"]))
                corr = int(_parse_number(_cell(cells, col["corrected"])))
                uncorr = int(_parse_number(_cell(cells, col["uncorrected"])))
                is_ofdm = final_type == "ofdm"

                result.append({
                    "channelID": _cell(cells, col["channel_id"], "0"),
                    "type": final_type,
                    "frequency": f"{int(freq)} MHz" if freq else "",
                    "powerLevel": power,
                    "mse": None if is_ofdm else (-snr if snr else None),
                    "mer": snr if snr else None,
                    "latency": 0,
                    "corrError": corr,
                    "nonCorrError": uncorr,
                })
            except (ValueError, TypeError, IndexError) as e:
                log.warning("MB8611: failed to parse DS row: %s", e)

        return result

    def _parse_upstream(self, table) -> list:
        rows = table.find_all("tr")
        header_row = _find_header_row(rows)
        if header_row is None:
            return []

        headers = [c.get_text(strip=True).lower() for c in header_row.find_all(["th", "td"])]
        col = _map_us_columns(headers)
        result = []

        for row in rows:
            if row is header_row:
                continue
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) < 4:
                continue
            if _cell(cells, col["lock_status"]).lower() != "locked":
                continue
            try:
                modulation = _normalize_modulation(_cell(cells, col["modulation"]))
                freq = _parse_frequency(_cell(cells, col["frequency"]))
                power = _parse_number(_cell(cells, col["power"]))

                result.append({
                    "channelID": _cell(cells, col["channel_id"], "0"),
                    "type": modulation or "qam",
                    "frequency": f"{int(freq)} MHz" if freq else "",
                    "powerLevel": power,
                    "multiplex": "",
                })
            except (ValueError, TypeError, IndexError) as e:
                log.warning("MB8611: failed to parse US row: %s", e)

        return result


def _find_header_row(rows):
    for row in rows:
        cells = row.find_all(["th", "td"])
        if cells and not any(c.get("colspan") for c in cells) and len(cells) > 3:
            return row
    return None


def _cell(cells, index, default=""):
    if index is None or index >= len(cells):
        return default
    return cells[index]


def _map_ds_columns(headers):
    col = {k: None for k in ("channel_id", "lock_status", "channel_type", "modulation",
                              "frequency", "power", "snr", "corrected", "uncorrected")}
    for i, h in enumerate(headers):
        if "channel" in h and ("id" in h or "index" in h):
            col["channel_id"] = i
        elif "lock" in h:
            col["lock_status"] = i
        elif "channel" in h and "type" in h:
            col["channel_type"] = i
        elif "modulation" in h or "profile" in h:
            col["modulation"] = i
        elif "freq" in h:
            col["frequency"] = i
        elif any(kw in h for kw in ("power", "receive", "level")):
            col["power"] = i
        elif "snr" in h or "mer" in h:
            col["snr"] = i
        elif "corrected" in h and "un" not in h:
            col["corrected"] = i
        elif "uncorrect" in h:
            col["uncorrected"] = i
    # positional fallbacks
    if col["channel_id"] is None:
        col["channel_id"] = 0
    if col["lock_status"] is None:
        col["lock_status"] = 1
    if col["frequency"] is None:
        col["frequency"] = 3
    if col["corrected"] is None:
        col["corrected"] = 6
    if col["uncorrected"] is None:
        col["uncorrected"] = 7
    return col


def _map_us_columns(headers):
    col = {k: None for k in ("channel_id", "lock_status", "modulation", "frequency", "power")}
    for i, h in enumerate(headers):
        if "channel" in h and ("id" in h or "index" in h):
            col["channel_id"] = i
        elif "lock" in h:
            col["lock_status"] = i
        elif "modulation" in h:
            col["modulation"] = i
        elif "freq" in h:
            col["frequency"] = i
        elif any(kw in h for kw in ("power", "transmit", "level")):
            col["power"] = i
    if col["lock_status"] is None:
        col["lock_status"] = 1
    if col["frequency"] is None:
        col["frequency"] = 3
    return col


def _parse_frequency(s):
    if not s:
        return 0.0
    parts = s.strip().split()
    try:
        v = float(parts[0])
    except (IndexError, ValueError):
        return 0.0
    unit = parts[1].lower() if len(parts) > 1 else ""
    if unit == "hz":
        return v / 1_000_000
    if unit == "khz":
        return v / 1_000
    if unit == "mhz":
        return v
    if v > 1_000_000:
        return v / 1_000_000
    if v > 1_000:
        return v / 1_000
    return v


def _parse_number(s):
    if not s:
        return 0.0
    try:
        return float(s.strip().split()[0])
    except (IndexError, ValueError):
        return 0.0


def _normalize_modulation(mod):
    if not mod:
        return ""
    m = mod.upper().replace("-", "")
    if "OFDMA" in m:
        return "ofdma"
    if "OFDM" in m:
        return "ofdm"
    if "ATDMA" in m:
        return "atdma"
    if "QAM" in m:
        num = m.replace("QAM", "").strip()
        return f"qam_{num}" if num else "qam"
    return mod.lower()
