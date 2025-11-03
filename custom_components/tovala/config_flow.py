# custom_components/tovala/config_flow.py
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .api import TovalaClient, TovalaAuthError

class TovalaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tovala."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = TovalaClient(
                session,
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
            )
            try:
                # Just verify auth for now; oven selection will be added later
                await client.login()
                return self.async_create_entry(
                    title="Tovala",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
            except TovalaAuthError:
                errors["base"] = "auth"
            except Exception:
                # Any other error: treat as connectivity/unknown for now
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)