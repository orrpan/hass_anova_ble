"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_MAC
from homeassistant.helpers import selector, device_registry

from homeassistant.components import bluetooth

from anova_ble import AnovaBLEPrecisionCooker
from typing import Any

from .const import DOMAIN


class AnovaBLEFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Anova Bluetooth."""

    VERSION = 1

    def __init__(self):
        self._discovery_info: bluetooth.BluetoothServiceInfoBleak | None = None
        self._discovered_address: str | None = None

    async def async_step_bluetooth(self, info: bluetooth.BluetoothServiceInfoBleak):
        address = device_registry.format_mac(info.address)
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        if res := await self._validate_anova_device(info.address):
            return self.async_abort(reason=res)

        self._discovery_info = info
        self._discovered_address = address

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Confirm discovery."""
        assert self._discovered_address is not None
        assert self._discovery_info is not None
        if user_input is not None:
            return self.async_create_entry(title="Anova Immersion Circulator", data={})

        self._set_confirm_only()
        placeholders = {"name": "Anova Immersion Circulator"}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders=placeholders
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
                    data={},
                )

        return self.async_show_form(
            step_id="user",
            last_step=True,
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
            return "not_found"
        anova = AnovaBLEPrecisionCooker(ble_device=ble_device)
        try:
            await anova.connect()
            await anova.update_state()
            await anova.disconnect()
        except Exception:
            return "unsupported"
