from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxBinarySensor(coordinator, entry.entry_id)])


class SolaxBinarySensor(CoordinatorEntity[SolaxDataUpdateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator: SolaxDataUpdateCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = "online"
        self._attr_unique_id = f"{entry_id}_online"
        self._attr_has_entity_name = True
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.get("online", False))

    @property
    def should_poll(self) -> bool:
        return False
