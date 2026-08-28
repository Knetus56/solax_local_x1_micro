from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfFrequency
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator


@dataclass(frozen=True)
class SolaxSensorDescription:
    key: str
    unit: str | None
    device_class: SensorDeviceClass | None
    entity_category: EntityCategory | None = None
    state_class: SensorStateClass | None = None
    options: list[str] | None = None


SENSOR_DESCRIPTIONS: tuple[SolaxSensorDescription, ...] = (
    SolaxSensorDescription("last_update", None, SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC),
    SolaxSensorDescription("mppt1_puissance", UnitOfPower.WATT, SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("mppt1_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("mppt1_intensite", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("mppt2_puissance", UnitOfPower.WATT, SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("mppt2_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("mppt2_intensite", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("inverter_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("inverter_intensite", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("inverter_puissance", UnitOfPower.WATT, SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("inverter_freq", UnitOfFrequency.HERTZ, None, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("prod_auj", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SolaxSensorDescription("prod_total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SolaxSensorDescription(
        "mode",
        None,
        SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=["wait_mode", "check_mode", "normal_mode"],
    ),
    SolaxSensorDescription("ip", None, None, entity_category=EntityCategory.DIAGNOSTIC),
    SolaxSensorDescription("num_inverter", None, None, entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        SolaxSensor(coordinator, entry.entry_id, description) for description in SENSOR_DESCRIPTIONS
    )


class SolaxSensor(CoordinatorEntity[SolaxDataUpdateCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: SolaxDataUpdateCoordinator,
        entry_id: str,
        description: SolaxSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._key = description.key
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.unit
        self._attr_entity_category = description.entity_category
        self._attr_state_class = description.state_class
        self._attr_options = description.options
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def should_poll(self) -> bool:
        return False
