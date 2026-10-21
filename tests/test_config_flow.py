from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.helpers.http import KEY_AUTHENTICATED

from custom_components.homebuddy_access.api import DOMAIN


async def test_flow_owner_and_singleton(hass, hass_owner_user):
    request = {KEY_AUTHENTICATED: True, "hass_user": hass_owner_user}
    with patch(
        "custom_components.homebuddy_access.config_flow.current_request"
    ) as current:
        current.get.return_value = request
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == "form"
        with patch(
            "custom_components.homebuddy_access.async_setup_entry", return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {}
            )
            await hass.async_block_till_done()
        assert result["type"] == "create_entry"
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == "abort"
        assert result["reason"] == "already_configured"


async def test_flow_admin_and_anonymous_denied(hass, hass_admin_user):
    for request in [None, {KEY_AUTHENTICATED: True, "hass_user": hass_admin_user}]:
        with patch(
            "custom_components.homebuddy_access.config_flow.current_request"
        ) as current:
            current.get.return_value = request
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
        assert result["type"] == "abort"
        assert result["reason"] == "owner_required"
