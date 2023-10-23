"""Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/integration_blueprint
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError

from homeassistant.components.bluetooth.match import ADDRESS, BluetoothCallbackMatcher

from homeassistant.components import bluetooth

from .const import DOMAIN
from .coordinator import AnovaDataUpdateCoordinator

from anova_ble import AnovaBLEPrecisionCooker

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.SWITCH,
]

# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    address = entry.data[CONF_MAC]
    hass.data.setdefault(DOMAIN, {})

    device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)

    if not device:
        raise ConfigEntryError("Device not in range")

    anova = AnovaBLEPrecisionCooker(ble_device=device)

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Update from a ble callback."""
        anova.set_ble_device(service_info.device)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            BluetoothCallbackMatcher({ADDRESS: address}),
            bluetooth.BluetoothScanningMode.PASSIVE
        )
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator = AnovaDataUpdateCoordinator(
        hass=hass,
        circulator=anova
    )
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
    await hass.config_entries.async_forward_entry_setup(entry, Platform.SWITCH)
    await hass.config_entries.async_forward_entry_setup(entry, Platform.CLIMATE)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    # if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
    await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR, Platform.SWITCH, Platform.CLIMATE])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
