"""Motorola MB8611 driver for DOCSight."""

import hashlib
import hmac
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

    # HNAP1 SOAP envelope template
    _HNAP_URL = "/HNAP1/"
    _HNAP_NS = "http://purenetworks.com/HNAP1/"
    _SOAP_ENVELOPE = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        '<soap:Body>{body}</soap:Body>'
        '</soap:Envelope>'
    )

    def _hnap_request(self, action: str, body_xml: str, cookie: str = "") -> str:
        """POST a HNAP1 SOAP request and return the response text."""
        url = f"{self._real_base}{self._HNAP_URL}"
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"http://purenetworks.com/HNAP1/{action}"',
        }
        if cookie:
            headers["Cookie"] = f"uid={cookie}"
        payload = self._SOAP_ENVELOPE.format(body=body_xml)
        r = self._session.post(url, data=payload, headers=headers, timeout=15)
        r.raise_for_status()
        return r.text

    @staticmethod
    def _hmac_md5(key: str, msg: str) -> str:
        return hmac.new(key.encode(), msg.encode(), hashlib.md5).hexdigest().upper()

    def login(self) -> None:
        """Authenticate via HNAP1 challenge-response (used by all MB8611 firmware)."""
        if not self._user and not self._password:
            return
        try:
            # Resolve http→https redirect to get the real base URL
            r0 = self._session.get(f"{self._url}/", timeout=15, allow_redirects=True)
            r0.raise_for_status()
            parsed = urlparse(r0.url)
            self._real_base = f"{parsed.scheme}://{parsed.netloc}"

            if "logout" in r0.text.lower() and "login" not in r0.url.lower():
                return  # already authenticated

            # Step 1 — request challenge
            step1_body = (
                f'<Login xmlns="{self._HNAP_NS}">'
                '<Action>request</Action>'
                f'<Username>{self._user}</Username>'
                '<LoginPassword></LoginPassword>'
                '<Captcha></Captcha>'
                '</Login>'
            )
            xml1 = self._hnap_request("Login", step1_body)
            log.debug("MB8611: HNAP challenge response: %s", xml1[:500])

            def _xml_val(text: str, tag: str) -> str:
                m = re.search(rf'<{tag}>(.*?)</{tag}>', text)
                return m.group(1) if m else ""

            challenge = _xml_val(xml1, "Challenge")
            public_key = _xml_val(xml1, "PublicKey")
            cookie_val = _xml_val(xml1, "Cookie")
            result1 = _xml_val(xml1, "LoginResult")

            log.debug("MB8611: HNAP challenge -> result=%r challenge_len=%d pubkey_len=%d cookie_len=%d",
                      result1, len(challenge), len(public_key), len(cookie_val))

            if not challenge or not public_key or not cookie_val:
                raise RuntimeError(
                    f"MB8611: HNAP challenge missing fields "
                    f"(challenge={bool(challenge)} pubkey={bool(public_key)} cookie={bool(cookie_val)}); "
                    f"response: {xml1[:300]}"
                )

            # Step 2 — compute HMAC-MD5 keys and login
            private_key = self._hmac_md5(public_key + self._password, challenge)
            login_password = self._hmac_md5(private_key, challenge)

            step2_body = (
                f'<Login xmlns="{self._HNAP_NS}">'
                '<Action>login</Action>'
                f'<Username>{self._user}</Username>'
                f'<LoginPassword>{login_password}</LoginPassword>'
                '<Captcha></Captcha>'
                '</Login>'
            )
            xml2 = self._hnap_request("Login", step2_body, cookie=cookie_val)
            result2 = _xml_val(xml2, "LoginResult")
            log.debug("MB8611: HNAP login result: %r", result2)

            if result2.upper() != "OK":
                raise RuntimeError(f"MB8611: HNAP login failed — LoginResult={result2!r}")

            # Persist the session cookie so subsequent requests stay authenticated
            self._session.cookies.set("uid", cookie_val, domain=parsed.netloc)
            log.info("MB8611: HNAP login succeeded")

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
