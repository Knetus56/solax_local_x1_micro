from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from homeassistant.components.sensor import RestoreSensor, SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfFrequency
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

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
    # prod_auj/prod_total only: also survive a HA restart that happens
    # during an API outage, see SolaxRestorableSensor below.
    restore: bool = False


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
    SolaxSensorDescription("inverter_freq", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SolaxSensorDescription("prod_auj", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, restore=True),
    SolaxSensorDescription("prod_total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, restore=True),
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
        (SolaxRestorableSensor if description.restore else SolaxSensor)(coordinator, entry.entry_id, description)
        for description in SENSOR_DESCRIPTIONS
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


class SolaxRestorableSensor(SolaxSensor, RestoreSensor):
    """prod_auj/prod_total: also survive a HA restart that happens during an API outage.

    coordinator._apply_persistence (see coordinator.py) already keeps these
    two cumulative counters from dropping while HA keeps running through an
    outage - but that persistence lives only in the coordinator's in-memory
    `data`. Right after a HA restart there is no previous `data` to fall
    back on, so if the outage is still ongoing when the first refresh runs,
    both would show nothing until the inverter answers again.

    This restores the last known value from HA's state storage to cover
    exactly that gap, applying the same midnight rollover rule prod_auj
    gets in the coordinator (checked live, not just once at startup, so it
    still resets correctly even if the outage spans several days). As soon
    as a real reading comes in, coordinator data takes back over and this
    restored value is never consulted again.
    """

    _restored_value: float | None = None
    _restored_day: date | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.data is not None and self.coordinator.data.get(self._key) is not None:
            return  # a real reading already came in - nothing to restore
        last_sensor_data = await self.async_get_last_sensor_data()
        last_state = await self.async_get_last_state()
        if last_sensor_data is None or last_state is None or last_sensor_data.native_value is None:
            return
        self._restored_value = last_sensor_data.native_value
        self._restored_day = dt_util.as_local(last_state.last_updated).date()

    @property
    def native_value(self):
        value = super().native_value
        if value is not None:
            return value
        if self._key == "prod_auj" and self._restored_day is not None and self._restored_day != dt_util.now().date():
            return 0.0
        return self._restored_value
