from __future__ import annotations

import base64
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=5)
_MODE_NAMES = {0: "wait_mode", 1: "check_mode", 2: "normal_mode"}

# Some firmware variants have been reported to return shorter response
# packets that omit trailing fields entirely, rather than always the full
# 112-byte body. 80 bytes is enough to reliably read the serial number
# (offsets 8-22) and confirm this is our inverter's response; every field
# beyond that is read defensively via _u16_or/_u32_or instead of assuming
# they're present.
_MIN_PAYLOAD_LENGTH = 80


def crc16(data: bytes, length: int) -> tuple[int, int]:
    poly = 0x8005
    reg = 0x0000
    mask = 0xFFFF

    for index in range(length):
        reg ^= (data[index] << 8) & 0xFFFF
        for _ in range(8):
            if reg & 0x8000:
                reg = ((reg << 1) ^ poly) & mask
            else:
                reg = (reg << 1) & mask

    return (reg >> 8) & 0xFF, reg & 0xFF


def offline_state(host: str, serial: str) -> dict[str, Any]:
    # mode/prod_auj/prod_total reflect only what a successful query
    # returned; on any request error/mismatch there is no real value to
    # show, so they stay None (the coordinator keeps the last known value
    # instead) rather than a fabricated state or a fake drop to zero for
    # the cumulative energy counters. The "online" binary_sensor is the
    # single source of truth for connectivity. Public: also used directly
    # by the coordinator when it deliberately skips a request (e.g. at
    # night, see coordinator.py).
    return {
        "online": False,
        "status": 0,
        "mode": None,
        "mppt1_puissance": 0,
        "mppt2_puissance": 0,
        "mppt1_voltage": 0.0,
        "mppt2_voltage": 0.0,
        "mppt1_intensite": 0.0,
        "mppt2_intensite": 0.0,
        "inverter_voltage": 0.0,
        "inverter_intensite": 0.0,
        "inverter_puissance": 0,
        "inverter_freq": 0.0,
        "prod_auj": None,
        "prod_total": None,
        "temp": 0,
        "ip": host,
        "num_inverter": serial,
    }


def build_sys_packet(inv: str, on: bool) -> str:
    buff = bytearray(76)
    buff[0] = 0x24
    buff[1] = 0x24
    buff[2] = 0x4C
    buff[4] = 0x08
    buff[5] = 0x03
    buff[6] = 0x01
    buff[7] = 0x1D
    buff[29] = 0x04
    buff[62] = 0x0A
    buff[64] = 0x02
    buff[65] = 0x07
    buff[67] = 0x01
    buff[68] = 0x61
    buff[70] = 0x02
    buff[72] = 0x01 if on else 0x00

    for index in range(14):
        buff[8 + index] = ord(inv[index]) if index < len(inv) else 0x00

    b1, b2 = crc16(buff, len(buff) - 2)
    buff[74] = b1
    buff[75] = b2

    _LOGGER.debug("build_sys_packet: serial=%s on=%s crc=(%02X,%02X)", inv, on, b1, b2)
    return base64.b64encode(bytes(buff)).decode("ascii")


def build_data_packet(inv: str) -> str:
    buff = bytearray(69)
    buff[0] = 0x24
    buff[1] = 0x24
    buff[2] = 0x45
    buff[3] = 0x00
    buff[4] = 0x08
    buff[5] = 0x04
    buff[6] = 0x01
    buff[7] = 0x1C
    buff[64] = 0x01

    for index in range(14):
        buff[8 + index] = ord(inv[index]) if index < len(inv) else 0x00

    b1, b2 = crc16(buff, len(buff) - 2)
    buff[67] = b1
    buff[68] = b2

    _LOGGER.debug("build_data_packet: serial=%s crc=(%02X,%02X)", inv, b1, b2)
    return base64.b64encode(bytes(buff)).decode("ascii")


def _u16(data: bytes, offset: int) -> int:
    return ((data[offset + 1] << 8) | data[offset]) & 0xFFFF


def _u32(data: bytes, offset: int) -> int:
    return (
        ((data[offset + 3] << 24) | (data[offset + 2] << 16) | (data[offset + 1] << 8) | data[offset])
        & 0xFFFFFFFF
    )


def _u16_or(data: bytes, offset: int, default: int | None = 0) -> int | None:
    """Like _u16, but returns `default` when the field is past the end of `data`."""
    if len(data) < offset + 2:
        return default
    return _u16(data, offset)


def _u32_or(data: bytes, offset: int, default: int | None = 0) -> int | None:
    """Like _u32, but returns `default` when the field is past the end of `data`."""
    if len(data) < offset + 4:
        return default
    return _u32(data, offset)


def _decode_payload(payload: str) -> bytes:
    return base64.b64decode(payload)


def parse_data(payload: str, host: str, serial: str) -> dict[str, Any]:
    _LOGGER.debug("parse_data: raw base64 payload=%r", payload)
    decoded = _decode_payload(payload)
    _LOGGER.debug("parse_data: decoded length=%d raw bytes=%s", len(decoded), decoded.hex())

    if len(decoded) < _MIN_PAYLOAD_LENGTH:
        _LOGGER.debug("parse_data: payload too short (%d bytes), marking offline", len(decoded))
        return offline_state(host, serial)

    serial_bytes = decoded[8:22]
    serial_inverter = serial_bytes.decode("ascii", errors="ignore")
    _LOGGER.debug("parse_data: packet type=0x%02X serial_in_packet=%r expected=%r", decoded[2], serial_inverter, serial)

    # Different firmware variants have been seen returning packet types
    # other than 0x70 for this same data layout, so only the serial - what
    # actually identifies this as our inverter's response - is checked.
    if serial_inverter != serial:
        _LOGGER.debug("parse_data: serial mismatch (got %r), marking offline", serial_inverter)
        return offline_state(host, serial)

    # mode/prod_auj/prod_total (registers 90-101) may be missing from a
    # shorter-than-usual packet. Same rule as offline_state: no real value
    # to show means None (coordinator persistence keeps the last known
    # value), not a fabricated 0 - especially for the cumulative counters,
    # see coordinator.py.
    if len(decoded) >= 92:
        mode = _u16(decoded, 90)
        status = 1 if mode == 2 else 0
        # Only wait/check/normal are valid mode values; any other register
        # value has no place here and stays None (sensor shows unavailable).
        mode_name = _MODE_NAMES.get(mode)
    else:
        status = 0
        mode_name = None

    prod_total_raw = _u32_or(decoded, 92, default=None)
    prod_auj_raw = _u16_or(decoded, 96, default=None)

    result = {
        "online": True,
        "status": status,
        "mode": mode_name,
        "mppt1_puissance": _u16_or(decoded, 86),
        "mppt2_puissance": _u16_or(decoded, 88),
        "mppt1_voltage": _u16_or(decoded, 78) / 10.0,
        "mppt2_voltage": _u16_or(decoded, 80) / 10.0,
        "mppt1_intensite": _u16_or(decoded, 82) / 10.0,
        "mppt2_intensite": _u16_or(decoded, 84) / 10.0,
        "inverter_voltage": _u16_or(decoded, 70) / 10.0,
        "inverter_intensite": _u16_or(decoded, 72) / 10.0,
        "inverter_puissance": _u16_or(decoded, 74),
        "inverter_freq": _u16_or(decoded, 76) / 100.0,
        "prod_auj": round(prod_auj_raw / 10.0, 2) if prod_auj_raw is not None else None,
        "prod_total": round(prod_total_raw / 10.0, 2) if prod_total_raw is not None else None,
        "temp": _u16_or(decoded, 100),
        "ip": host,
        "num_inverter": serial,
    }
    _LOGGER.debug("parse_data: result=%s", result)
    return result


async def fetch_inverter_state(session: aiohttp.ClientSession, host: str, serial: str) -> dict[str, Any]:
    payload = build_data_packet(serial)
    _LOGGER.debug("fetch_inverter_state: querying host=%s serial=%s", host, serial)
    try:
        async with session.post(
            f"http://{host}",
            data=payload.encode("ascii"),
            headers={"Content-Type": "application/octet-stream"},
            timeout=_REQUEST_TIMEOUT,
        ) as response:
            raw = await response.read()
            body = raw.decode("ascii", errors="ignore")
            _LOGGER.debug("fetch_inverter_state: HTTP %d body_len=%d", response.status, len(body))
            # Length is validated once, post-decode, in parse_data
            # (_MIN_PAYLOAD_LENGTH) rather than approximated here on the
            # base64 text - avoids two thresholds drifting out of sync.
            if response.status == 200:
                return parse_data(body.replace("\n", ""), host, serial)
            _LOGGER.debug("fetch_inverter_state: bad status, marking offline")
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        _LOGGER.debug("fetch_inverter_state: request failed: %s", exc)

    return offline_state(host, serial)


async def set_inverter_state(session: aiohttp.ClientSession, host: str, serial: str, on: bool) -> bool:
    payload = build_sys_packet(serial, on)
    _LOGGER.debug("set_inverter_state: host=%s serial=%s on=%s", host, serial, on)
    try:
        async with session.post(
            f"http://{host}",
            data=payload.encode("ascii"),
            headers={"Content-Type": "application/octet-stream"},
            timeout=_REQUEST_TIMEOUT,
        ) as response:
            success = response.status == 200
            _LOGGER.debug("set_inverter_state: HTTP %d success=%s", response.status, success)
            return success
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        _LOGGER.debug("set_inverter_state: request failed: %s", exc)
        return False
