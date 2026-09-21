from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator
from .solax_protocol import fetch_power_ratio, set_power_ratio


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxPowerRatioNumber(coordinator, entry.entry_id)])


class SolaxPowerRatioNumber(CoordinatorEntity[SolaxDataUpdateCoordinator], RestoreNumber):
    # fetch_inverter_state's regular telemetry query doesn't expose this
    # setting, so it isn't part of the coordinator's polled data - it's only
    # known through this entity's own writes/reads. RestoreNumber refills
    # the box across a HA restart with the last value we wrote, so it isn't
    # blank while waiting for the real read below. But the restored value
    # can be stale - the inverter itself may have lost power too (HA
    # restart during an outage), come back up on its own overnight (SolaX
    # inverters power their Wi-Fi dongle off at night), or been changed
    # from the SolaX app - so it's confirmed with a real read a couple
    # seconds after: HA startup, whenever the coordinator's regular poll
    # notices the inverter transition offline -> online (i.e. it just
    # booted), and after every write this entity makes. The delay gives
    # the inverter time to finish booting/settle before it's queried.
    # It's also reset to unknown at local midnight: SolaX inverters power
    # their Wi-Fi dongle off overnight, so there's a long stretch with no
    # way to confirm the ratio is still what it was - if HA (and this
    # RestoreNumber) restarts during that window, better to show unknown
    # than to restore yesterday's now-unverified value and have it look
    # authoritative until the inverter reconnects in the morning.
    _READ_DELAY = 2
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SolaxDataUpdateCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = "power_ratio"
        self._attr_unique_id = f"{entry_id}_power_ratio"
        self._attr_has_entity_name = True
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = None
        self._was_online = bool(coordinator.data.get("online")) if coordinator.data else False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_number_data = await self.async_get_last_number_data()
        if last_number_data is not None and last_number_data.native_value is not None:
            self._attr_native_value = last_number_data.native_value
        self._schedule_read()
        self.async_on_remove(async_track_time_change(self.hass, self._async_midnight_reset, hour=0, minute=0, second=0))

    async def _async_midnight_reset(self, _now) -> None:
        self._attr_native_value = None
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        online = bool(self.coordinator.data.get("online")) if self.coordinator.data else False
        if online and not self._was_online:
            self._schedule_read()
        self._was_online = online
        super()._handle_coordinator_update()

    def _schedule_read(self) -> None:
        self.async_on_remove(async_call_later(self.hass, self._READ_DELAY, self._async_read_ratio))

    async def _async_read_ratio(self, _now) -> None:
        ratio = await fetch_power_ratio(self.coordinator.session, self.coordinator.host, self.coordinator.serial)
        if ratio is not None:
            self._attr_native_value = ratio
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        ratio = int(value)
        if await set_power_ratio(self.coordinator.session, self.coordinator.host, self.coordinator.serial, ratio):
            self._attr_native_value = ratio
            self.async_write_ha_state()
            self._schedule_read()

    @property
    def should_poll(self) -> bool:
        return False
