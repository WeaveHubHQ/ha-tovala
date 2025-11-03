from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, CONF_OVEN_ID
from .api import TovalaClient

class TovalaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                client = TovalaClient(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
                await client.login()
                # Optional: fetch ovens to prefill
                me = await client.me()
                ovens = me.get("ovens", [])
                oven_id = user_input.get(CONF_OVEN_ID) or (ovens[0]["id"] if ovens else None)
                if not oven_id:
                    errors["base"] = "no_ovens_found"
                else:
                    return self.async_create_entry(title="Tovala", data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_OVEN_ID: oven_id,
                    })
            except Exception:
                errors["base"] = "auth"
        schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_OVEN_ID, description="If empty I’ll pick your first oven"): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)