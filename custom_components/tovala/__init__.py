# custom_components/tovala/__init__.py
from __future__ import annotations
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .api import TovalaClient, TovalaAuthError, TovalaApiError
from .coordinator import TovalaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tovala from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    email = entry.data.get("email")
    password = entry.data.get("password")
    oven_id = entry.data.get("oven_id")
    token = entry.data.get("token")  # optional, for future token-based auth

    session = async_get_clientsession(hass)
    client = TovalaClient(session, email=email, password=password, token=token)

    try:
        # Authenticate and determine which base URL (beta or prod) works.
        await client.login()
    except TovalaAuthError as err:
        raise ConfigEntryNotReady(f"Authentication failed: {err}") from err
    except TovalaApiError as err:
        raise ConfigEntryNotReady(f"Connection error: {err}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Unexpected error: {err}") from err

    # Try to get ovens (non-fatal if we can't yet)
    if not oven_id:
        try:
            ovens = await client.list_ovens()
            _LOGGER.info("list_ovens returned: %s", ovens)
            if ovens:
                oven_id = ovens[0].get("id")
                _LOGGER.info("Extracted oven_id: %s from first oven: %s", oven_id, ovens[0])
                if oven_id:
                    hass.config_entries.async_update_entry(
                        entry, data={**entry.data, "oven_id": oven_id}
                    )
        except Exception as e:
            # Ovens list isn't critical for initial setup
            _LOGGER.error("Failed to discover ovens during setup: %s", e, exc_info=True)
            oven_id = None

    coord = TovalaCoordinator(hass, client, oven_id)
    await coord.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coord}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

 
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Tovala config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok