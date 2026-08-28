"""Config flow for the SolaX Local X1 Micro integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_HOST,
    CONF_INVERTER_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INVERTER_TYPE_X1_MICRO_2IN1,
    INVERTER_TYPES,
)

# Serial numbers validation: alphanumeric, up to 21 chars
_SN_RE = re.compile(r"^[A-Za-z0-9]{5,21}$")

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(
            CONF_INVERTER_TYPE, default=INVERTER_TYPE_X1_MICRO_2IN1
        ): SelectSelector(
            SelectSelectorConfig(
                options=list(INVERTER_TYPES.keys()),
                mode=SelectSelectorMode.LIST,
                translation_key="inverter_type",
            )
        ),
        vol.Required(CONF_SERIAL): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class SolaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Local X1 Micro."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            serial_number: str = user_input[CONF_SERIAL].strip().upper()

            if not _SN_RE.match(serial_number):
                errors[CONF_SERIAL] = "invalid_serial"
            else:
                inverter_type: str = user_input[CONF_INVERTER_TYPE]
                inverter_model: str = INVERTER_TYPES.get(inverter_type, inverter_type)

                # Prevent duplicate entries for the same serial number
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SolaX {inverter_model} ({serial_number})",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_INVERTER_TYPE: inverter_type,
                        CONF_SERIAL: serial_number,
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SolaxOptionsFlow:
        """Create the options flow."""
        return SolaxOptionsFlow()


class SolaxOptionsFlow(config_entries.OptionsFlow):
    """Handle options for an existing SolaX Local X1 Micro entry (host / scan interval)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_host = self.config_entry.options.get(
            CONF_HOST, self.config_entry.data.get(CONF_HOST)
        )
        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        options_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_scan_interval
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)
