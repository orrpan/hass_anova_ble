"""Sensor platform for integration_blueprint."""
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import AnovaDataUpdateCoordinator
from .entity import AnovaBluetoothEntity

from anova_ble import AnovaStatus

ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="timer_active",
        name="Timer Active",
        icon="mdi:clock",
    ),
)

async def async_setup_entry(hass, entry: ConfigEntry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        AnovaBluetoothSwitch(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class AnovaBluetoothSwitch(AnovaBluetoothEntity, SwitchEntity):
    """integration_blueprint Sensor class."""

    def __init__(
        self,
        coordinator: AnovaDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.coordinator = coordinator

    async def async_turn_on(self):
        await self.coordinator.circulator.start_timer()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        await self.coordinator.circulator.stop_timer()
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self) -> bool:
        """Return the native value of the sensor."""
        if state := self.coordinator.circulator.state:
            return state.timer[1] == AnovaStatus.Running
        else:
            return None
