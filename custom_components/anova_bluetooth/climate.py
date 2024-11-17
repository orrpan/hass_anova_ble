"""Sensor platform for integration_blueprint."""
from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription, ClimateEntityFeature
from homeassistant.components.climate.const import HVAC_MODE_HEAT, HVAC_MODE_OFF
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN
from .coordinator import AnovaDataUpdateCoordinator
from .entity import AnovaBluetoothEntity

from anova_ble import AnovaStatus

async def async_setup_entry(hass, entry: ConfigEntry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([
        AnovaBluetoothClimate(
            coordinator=coordinator,
            entity_description=ClimateEntityDescription(
                key="water_bath",
                name="Sous Vide"
            )
        )
    ])


class AnovaBluetoothClimate(AnovaBluetoothEntity, ClimateEntity):
    """integration_blueprint Climate class."""

    def __init__(
        self,
        coordinator: AnovaDataUpdateCoordinator,
        entity_description: ClimateEntityDescription,
    ) -> None:
        """Initialize the climate class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.coordinator = coordinator

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        self._attr_max_temp = 211.8
        self._attr_min_temp = 41
        self._attr_precision = 0.1

    @property
    def target_temperature(self):
        if state := self.coordinator.circulator.state:
            return state.target_temp
        return None

    @property
    def current_temperature(self):
        if state := self.coordinator.circulator.state:
            return state.current_temp
        return None

    @property
    def hvac_mode(self):
        if state := self.coordinator.circulator.state:
            if state.status == AnovaStatus.Running:
                return HVAC_MODE_HEAT
            else:
                return HVAC_MODE_OFF
        else:
            return None

    async def async_set_temperature(self, **kwargs):
        await self.coordinator.circulator.set_temp(kwargs["temperature"])
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_HEAT:
            await self.coordinator.circulator.start()
        if hvac_mode == HVAC_MODE_OFF:
            await self.coordinator.circulator.stop()

        await self.coordinator.async_request_refresh()
