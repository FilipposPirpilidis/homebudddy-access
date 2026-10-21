"""Owner-only singleton connection QR setup."""

import probatio as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.http import KEY_AUTHENTICATED, current_request

from .api import DOMAIN


class HomeBuddyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        request = current_request.get()
        user = request.get("hass_user") if request is not None else None
        if user is not None:
            user = await self.hass.auth.async_get_user(user.id)
        if (
            request is None
            or not request.get(KEY_AUTHENTICATED)
            or user is None
            or not user.is_owner
            or not user.is_active
            or user.system_generated
        ):
            return self.async_abort(reason="owner_required")
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="HomeBuddy Access", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
