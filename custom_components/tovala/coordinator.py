from __future__ import annotations
from datetime import timedelta, datetime
from typing import Any
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, EVENT_TIMER_FINISHED

_LOGGER = logging.getLogger(__name__)

class TovalaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client, oven_id: str):
        super().__init__(
            hass,
            _LOGGER,  # Changed from hass.helpers.logger.getLogger(__name__)
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.oven_id = oven_id
        self._last_reported_remaining = None

    async def _async_update_data(self) -> dict:
        if not self.oven_id:
            # Return empty data if we don't have an oven yet
            _LOGGER.warning("No oven_id configured yet")
            return {}
        
        try:
            data = await self.client.oven_status(self.oven_id)
            _LOGGER.info("Oven status received: %s", data)

            # Status response format:
            # Idle: {"state":"idle", "remote_control_enabled":true}
            # Cooking: {"state":"cooking", "estimated_start_time":"...", "estimated_end_time":"...", ...}
            state = data.get("state", "unknown")

            # Calculate remaining time from estimated_end_time
            remaining = 0
            if state == "cooking" and "estimated_end_time" in data:
                try:
                    end_time_str = data["estimated_end_time"]
                    # Parse ISO format: "2025-11-07T01:43:48.000003163Z"
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    now = dt_util.utcnow()
                    delta = end_time - now
                    remaining = max(0, int(delta.total_seconds()))
                    _LOGGER.debug("Calculated remaining time: %d seconds (end_time=%s, now=%s)",
                                 remaining, end_time, now)
                except Exception as e:
                    _LOGGER.warning("Failed to parse estimated_end_time: %s - %s",
                                   data.get("estimated_end_time"), e)
                    remaining = 0

            _LOGGER.debug("Parsed state=%s, remaining=%s", state, remaining)

            # Fire event once when remaining crosses to 0
            if (self._last_reported_remaining and self._last_reported_remaining > 0) and int(remaining) == 0:
                _LOGGER.info("Timer finished for oven %s", self.oven_id)
                self.hass.bus.async_fire(EVENT_TIMER_FINISHED, {
                    "oven_id": self.oven_id,
                    "data": data
                })

            self._last_reported_remaining = int(remaining)

            # Add calculated remaining to data for sensors
            data["remaining"] = remaining
            return data

        except Exception as err:
            _LOGGER.error("Error fetching oven status: %s", err, exc_info=True)
            raise