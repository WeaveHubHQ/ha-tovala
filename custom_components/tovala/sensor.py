from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import TovalaCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback):
    coord: TovalaCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    add_entities([TovalaRemainingTimeSensor(coord)])

class TovalaRemainingTimeSensor(SensorEntity):
    _attr_name = "Tovala Time Remaining"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator: TovalaCoordinator):
        self.coordinator = coordinator
        self._attr_unique_id = f"tovala_{coordinator.oven_id}_remaining"

    @property
    def native_value(self):
        return int(self.coordinator.data.get("remaining") or self.coordinator.data.get("time_remaining") or 0)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_update(self):
        await self.coordinator.async_request_refresh()