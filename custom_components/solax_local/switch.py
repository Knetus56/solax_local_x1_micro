from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator
from .solax_protocol import set_inverter_state


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxSwitch(coordinator, entry.entry_id)])


class SolaxSwitch(CoordinatorEntity[SolaxDataUpdateCoordinator], SwitchEntity):
    def __init__(self, coordinator: SolaxDataUpdateCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = "switch"
        self._attr_unique_id = f"{entry_id}_switch"
        self._attr_has_entity_name = True
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.get("status", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await set_inverter_state(self.coordinator.session, self.coordinator.host, self.coordinator.serial, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await set_inverter_state(self.coordinator.session, self.coordinator.host, self.coordinator.serial, False)
        await self.coordinator.async_request_refresh()

    @property
    def should_poll(self) -> bool:
        return False
