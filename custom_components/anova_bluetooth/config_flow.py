"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_MAC
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import selector, device_registry

from homeassistant.components import bluetooth

from anova_ble import AnovaBLEPrecisionCooker

from .const import DOMAIN, LOGGER


class AnovaBLEFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Anova Bluetooth."""

    VERSION = 1

    async def async_step_bluetooth(self, info: bluetooth.BluetoothServiceInfoBleak):
        await self.async_set_unique_id(device_registry.format_mac(info.address))
        self._abort_if_unique_id_configured()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MAC,
                        default=str(info.address),
                        description="MAC Address"
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    )
                }
            ),
        )

    async def async_step_user(
        self,
        info: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        if not bluetooth.async_scanner_count(self.hass, connectable=True):
            return self.async_abort(reason="bluetooth_not_available")

        errors = {}
        if info is not None:
            info[CONF_MAC] = device_registry.format_mac(info[CONF_MAC])

            await self.async_set_unique_id(info[CONF_MAC])
            self._abort_if_unique_id_configured()

            if (res := await self._validate_anova_device(
                address=info[CONF_MAC]
            )) is not None:
                errors["base"] = res
            else:
                return self.async_create_entry(
                    title="Anova Immersion Circulator",
                    data=info,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MAC,
                        default=(info or {}).get(CONF_MAC),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    )
                }
            ),
            errors=errors
        )

    async def _validate_anova_device(self, address: str) -> str | None:
        """Validate device is an actual Anova device."""

        ble_device = bluetooth.async_ble_device_from_address(self.hass, address.upper(), connectable=True)
        if not ble_device:
            return "No bluetooth device found with that address."
        anova = AnovaBLEPrecisionCooker(ble_device=ble_device)
        try:
            await anova.connect()
            await anova.update_state()
            await anova.disconnect()
        except Exception:
            return "Device not a supported Anova circulator."