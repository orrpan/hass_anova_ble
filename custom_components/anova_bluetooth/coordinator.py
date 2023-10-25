"""DataUpdateCoordinator for integration_blueprint."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, LOGGER
import asyncio

from anova_ble import AnovaBLEPrecisionCooker

# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class AnovaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        circulator: AnovaBLEPrecisionCooker,
    ) -> None:
        """Initialize."""
        self.circulator = circulator
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with asyncio.timeout(5):
                await self.circulator.connect()
                await self.circulator.update_state()
                LOGGER.debug(f"Updated state: {self.circulator.state}")
                return
        except Exception as exception:
            # await self.circulator.disconnect()
            raise UpdateFailed(exception) from exception
