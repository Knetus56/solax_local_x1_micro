from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfFrequency
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
    
    # Create shared device_info with model
    device_info = {
        "identifiers": {(DOMAIN, coordinator.serial)},
        "name": f"SolaX {coordinator.serial}",
        "manufacturer": "SolaX",
        "model": model,
        "connections": {("ip", coordinator.host)},
    }
    
    entities = [
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "last_update",
            "Last update",
            None,
            SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mppt1_puissance",
            "MPPT 1 power",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mppt1_voltage",
            "MPPT 1 voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mppt1_intensite",
            "MPPT 1 current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mppt2_puissance",
            "MPPT 2 power",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mppt2_voltage",
            "MPPT 2 voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mppt2_intensite",
            "MPPT 2 current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "inverter_voltage",
            "Inverter voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "inverter_intensite",
            "Inverter current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "inverter_puissance",
            "Inverter power",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "inverter_freq",
            "Inverter frequency",
            UnitOfFrequency.HERTZ,
            SensorDeviceClass.FREQUENCY,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "temp",
            "Temperature",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "prod_auj",
            "Daily production",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "prod_total",
            "Total production",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mode",
            "Mode",
            None,
            None,
            EntityCategory.DIAGNOSTIC,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "ip",
            "IP",
            None,
            None,
            EntityCategory.DIAGNOSTIC,
            device_info=device_info,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "num_inverter",
            "Serial number",
            None,
            None,
            EntityCategory.DIAGNOSTIC,
            device_info=device_info,
        ),
    ]
    async_add_entities(entities)


class SolaxSensor(CoordinatorEntity[SolaxDataUpdateCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator,
        entry_id,
        key,
        name,
        unit,
        device_class,
        entity_category: EntityCategory | None = None,
        state_class: SensorStateClass | None = None,
        device_info: dict | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = entity_category
        self._attr_state_class = state_class
        self._attr_device_info = device_info

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def should_poll(self) -> bool:
        return False
