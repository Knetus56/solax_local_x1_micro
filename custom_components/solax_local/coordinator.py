from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.sun import is_up
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .solax_protocol import fetch_inverter_state, offline_state

_LOGGER = logging.getLogger(__name__)

# Skip polling while solidly at night: local SolaX inverters power off
# their Wi-Fi dongle overnight, so querying them is pointless. The margin
# keeps polling active for an hour around actual sunrise/sunset, so an
# inverter waking up earlier/later than the calculated sun times is still
# picked up promptly instead of waiting for the next scan after margin end.
_NIGHT_MARGIN = timedelta(hours=1)


class SolaxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        serial: str,
        model: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="solax_local",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.serial = serial
        self.model = model
        self.session = async_get_clientsession(hass)

    @property
    def device_info(self) -> dict[str, Any]:
        """Shared device info, reused by every platform (sensor/binary_sensor/switch)."""
        return {
            "identifiers": {(DOMAIN, self.serial)},
            "name": f"SolaX {self.serial}",
            "manufacturer": "SolaX",
            "model": self.model,
            "connections": {("ip", self.host)},
        }

    # prod_total is a lifetime cumulative counter: it must never appear to
    # drop to 0 when a poll fails to produce a fresh reading (that would
    # corrupt long-term statistics) - keep the last known value instead.
    # prod_auj (today's production) gets the same treatment EXCEPT across
    # a day change, see _apply_persistence below. It also never accepts a
    # same-day drop even from a "successful" poll: some SolaX firmware
    # reports a genuine (non-None) 0 for this register once the inverter
    # leaves normal_mode at dusk, which would otherwise look like a real
    # fresh reading - see
    # https://github.com/Knetus56/solax_local_x1_micro/issues/16.
    # "mode" is not part of this list: it reflects only what the last
    # query actually returned, so it goes back to None/unknown on any
    # request error.
    _PERSIST_LAST_VALUE_KEYS = ("prod_auj", "prod_total")

    def _is_solidly_night(self) -> bool:
        """True only while the sun has been down for a while and stays down for a while.

        Requires the sun.sun entity to be present; if it's not (integration
        disabled/removed), always return False so polling never gets
        skipped based on a check we can't actually perform.
        """
        if self.hass.states.get("sun.sun") is None:
            return False
        now = dt_util.utcnow()
        return not is_up(self.hass, now - _NIGHT_MARGIN) and not is_up(self.hass, now + _NIGHT_MARGIN)

    def _apply_persistence(self, data: dict[str, Any]) -> None:
        """Fill in values this poll didn't produce with the last known ones.

        Covers _PERSIST_LAST_VALUE_KEYS (see docstring above). prod_auj is
        the one exception within that list: it resets to 0 instead of
        carrying over once the local calendar day has changed since the
        last known value, so it never keeps showing yesterday's total
        past midnight. Conversely, within the same day it never accepts a
        drop even from a poll that did return a value (see class docstring
        above) - only a day change is allowed to lower it.
        """
        if self.data is None:
            return

        prod_auj_persisted = data.get("prod_auj") is None
        for key in self._PERSIST_LAST_VALUE_KEYS:
            if data.get(key) is None:
                data[key] = self.data.get(key)

        previous_update = self.data.get("last_update")
        same_day = (
            previous_update is not None
            and dt_util.as_local(previous_update).date() == dt_util.now().date()
        )

        if prod_auj_persisted:
            if not same_day:
                data["prod_auj"] = 0.0
        else:
            previous_prod_auj = self.data.get("prod_auj")
            if same_day and previous_prod_auj is not None and data["prod_auj"] < previous_prod_auj:
                data["prod_auj"] = previous_prod_auj

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if self._is_solidly_night():
                _LOGGER.debug("Skipping request: solidly night for %s", self.serial)
                data = offline_state(self.host, self.serial)
            else:
                data = await fetch_inverter_state(self.session, self.host, self.serial)
            self._apply_persistence(data)
            data["last_update"] = datetime.now(timezone.utc)
            return data
        except Exception as err:  # pragma: no cover - defensive path
            raise UpdateFailed(f"Unable to fetch SolaX data: {err}") from err
