from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_INVERTER_TYPE, DOMAIN, INVERTER_TYPES
from .coordinator import SolaxDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get inverter model from config
    inverter_type = entry.data.get(CONF_INVERTER_TYPE, "Unknown")
    model = INVERTER_TYPES.get(inverter_type, "Unknown")
    
    async_add_entities([SolaxBinarySensor(coordinator, entry.entry_id, model)])


class SolaxBinarySensor(CoordinatorEntity[SolaxDataUpdateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, entry_id, model: str) -> None:
        super().__init__(coordinator)
        self._attr_name = "Online"
        self._attr_unique_id = f"{entry_id}_online"
        self._attr_has_entity_name = True
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
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
        return bool(self.coordinator.data.get("online", False))

    @property
    def should_poll(self) -> bool:
        return False
