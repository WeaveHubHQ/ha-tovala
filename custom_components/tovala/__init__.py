from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS
from .api import TovalaClient
from .coordinator import TovalaCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    email = entry.data["email"]
    password = entry.data["password"]
    oven_id = entry.data["oven_id"]

    client = TovalaClient(email, password)
    await client.login()
    # If user didn't supply oven id, try to fetch first oven from profile:
    if not oven_id:
        me = await client.me()
        # Adjust to match payload: e.g. me["ovens"][0]["id"]
        oven_id = me.get("ovens", [{}])[0].get("id")
        hass.config_entries.async_update_entry(entry, data={**entry.data, "oven_id": oven_id})

    coord = TovalaCoordinator(hass, client, oven_id)
    await coord.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coord}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        stored = hass.data[DOMAIN].pop(entry.entry_id, None)
        if stored and stored.get("client"):
            await stored["client"].aclose()
    return unload_ok