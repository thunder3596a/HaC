"""Motorola MB8611 driver for DOCSight.

The MB8611 is a standalone DOCSIS 3.1 cable modem.
It exposes channel data via HTML tables at /cmconnectionstatus.html.
No authentication is required — the page is open on the LAN.

Default URL: http://192.168.100.1
"""

import logging

import requests
from bs4 import BeautifulSoup

from app.drivers.base import ModemDriver

log = logging.getLogger("docsis.driver.mb8611")


class MB8611Driver(ModemDriver):
    """Driver for Motorola MB8611 DOCSIS 3.1 cable modem."""

    DRIVER_KEY = "mb8611"

    def __init__(self, url: str, user: str, password: str):
        super().__init__(url, user, password)
        self._session = requests.Session()

    def login(self) -> None:
        """Authenticate via the MB8611 login form."""
        if not self._user and not self._password:
            return
        try:
            r = self._session.post(
                f"{self._url}/login.asp",
                data={"loginUsername": self._user, "loginPassword": self._password},
                timeout=15,
                allow_redirects=True,
            )
            r.raise_for_status()
            if "logout" not in r.text.lower() and "connection status" not in r.text.lower():
                log.warning("MB8611: login may have failed — check credentials")
        except requests.RequestException as e:
            raise RuntimeError(f"MB8611: login failed: {e}")

    def get_docsis_data(self) -> dict:
        """Scrape DOCSIS channel tables from /cmconnectionstatus.html.

        Page layout:
          tables[0]: Startup procedure
          tables[1]: Downstream bonded channels (SC-QAM + OFDM)
          tables[2]: Upstream bonded channels (SC-QAM + OFDMA)
        """
        try:
            r = self._session.get(
                f"{self._url}/cmconnectionstatus.html",
                timeout=15,
            )
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

    # ── Parsers ──────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    col.setdefault("channel_id", 0) or col.__setitem__("channel_id", col["channel_id"] or 0)
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
