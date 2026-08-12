from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_INVERTER_TYPE, DOMAIN, INVERTER_TYPES
from .coordinator import SolaxDataUpdateCoordinator
from .solax_protocol import set_inverter_state


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get inverter model from config
    inverter_type = entry.data.get(CONF_INVERTER_TYPE, "Unknown")
    model = INVERTER_TYPES.get(inverter_type, "Unknown")
    
    async_add_entities([SolaxSwitch(coordinator, entry.entry_id, model)])


class SolaxSwitch(CoordinatorEntity[SolaxDataUpdateCoordinator], SwitchEntity):
    def __init__(self, coordinator, entry_id, model: str) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = "switch"
        self._attr_name = None
        self._attr_unique_id = f"{entry_id}_switch"
        self._attr_has_entity_name = True
        # Attach entity to inverter device by serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.serial)},
            "name": f"SolaX {coordinator.serial}",
            "manufacturer": "SolaX",
            "model": model,
            "connections": {("ip", coordinator.host)},
        }

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.get("status", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(set_inverter_state, self.coordinator.host, self.coordinator.serial, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(set_inverter_state, self.coordinator.host, self.coordinator.serial, False)
        await self.coordinator.async_request_refresh()

    @property
    def should_poll(self) -> bool:
        return False
