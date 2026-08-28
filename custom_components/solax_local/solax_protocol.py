from __future__ import annotations

import base64
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=5)
_MODE_NAMES = {0: "WaitMode", 1: "CheckMode", 2: "NormalMode"}


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


def _offline_state(host: str, serial: str) -> dict[str, Any]:
    # mode/prod_auj/prod_total reflect only what a successful query
    # returned; on any request error/mismatch there is no real value to
    # show, so they stay None (the coordinator keeps the last known value
    # instead) rather than a fabricated state or a fake drop to zero for
    # the cumulative energy counters. The "online" binary_sensor is the
    # single source of truth for connectivity.
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


def _decode_payload(payload: str) -> bytes:
    return base64.b64decode(payload)


def parse_data(payload: str, host: str, serial: str) -> dict[str, Any]:
    decoded = _decode_payload(payload)
    _LOGGER.debug("parse_data: decoded length=%d", len(decoded))

    if len(decoded) < 112:
        _LOGGER.debug("parse_data: payload too short (%d bytes), marking offline", len(decoded))
        return _offline_state(host, serial)

    serial_bytes = decoded[8:22]
    serial_inverter = serial_bytes.decode("ascii", errors="ignore")
    _LOGGER.debug("parse_data: packet type=0x%02X serial_in_packet=%r expected=%r", decoded[2], serial_inverter, serial)

    if decoded[2] != 0x70 or serial_inverter != serial:
        _LOGGER.debug("parse_data: packet mismatch (type=0x%02X serial=%r), marking offline", decoded[2], serial_inverter)
        return _offline_state(host, serial)

    mode = _u16(decoded, 90)
    status = 1 if mode == 2 else 0
    # Only wait/check/normal are valid mode values; any other register
    # value has no place here and stays None (sensor shows unavailable).
    mode_name = _MODE_NAMES.get(mode)

    result = {
        "online": True,
        "status": status,
        "mode": mode_name,
        "mppt1_puissance": _u16(decoded, 86),
        "mppt2_puissance": _u16(decoded, 88),
        "mppt1_voltage": _u16(decoded, 78) / 10.0,
        "mppt2_voltage": _u16(decoded, 80) / 10.0,
        "mppt1_intensite": _u16(decoded, 82) / 10.0,
        "mppt2_intensite": _u16(decoded, 84) / 10.0,
        "inverter_voltage": _u16(decoded, 70) / 10.0,
        "inverter_intensite": _u16(decoded, 72) / 10.0,
        "inverter_puissance": _u16(decoded, 74),
        "inverter_freq": _u16(decoded, 76) / 100.0,
        "prod_auj": round(_u16(decoded, 96) / 10.0, 2),
        "prod_total": round(_u32(decoded, 92) / 10.0, 2),
        "temp": _u16(decoded, 100),
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
            if response.status == 200 and len(body) >= 150:
                return parse_data(body.replace("\n", ""), host, serial)
            _LOGGER.debug("fetch_inverter_state: response too short or bad status, marking offline")
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        _LOGGER.debug("fetch_inverter_state: request failed: %s", exc)

    return _offline_state(host, serial)


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
