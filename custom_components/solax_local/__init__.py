from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_HOST,
    CONF_INVERTER_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INVERTER_TYPES,
)
from .coordinator import SolaxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configuration au niveau de la plateforme."""
    hass.data.setdefault(DOMAIN, {})
    
    async def refresh_all_inverters(call: ServiceCall) -> None:
        """Service pour actualiser tous les onduleurs."""
        coordinators = hass.data.get(DOMAIN, {}).values()
        for coordinator in coordinators:
            if isinstance(coordinator, SolaxDataUpdateCoordinator):
                await coordinator.async_request_refresh()
        _LOGGER.info("Actualisation manuelle de tous les onduleurs")
    
    hass.services.async_register(DOMAIN, "refresh_all", refresh_all_inverters)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    model = INVERTER_TYPES.get(entry.data.get(CONF_INVERTER_TYPE), "Unknown")
    # host / scan_interval can be overridden after setup via the options flow.
    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = SolaxDataUpdateCoordinator(
        hass,
        host,
        entry.data[CONF_SERIAL],
        model,
        scan_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch"])
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change (e.g. host or scan_interval)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "refresh_all")
    return unload_ok
