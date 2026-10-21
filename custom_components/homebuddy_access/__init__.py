"""HomeBuddy connection QR integration."""

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig

from .api import DOMAIN, Bridge, OwnerView


async def async_setup(hass, config):
    hass.http.register_view(OwnerView())
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/homebuddy-access-assets", str(Path(__file__).parent / "www"), False
            )
        ]
    )
    return True


async def async_setup_entry(hass, entry):
    bridge = Bridge(hass)
    await bridge.load()
    hass.data[DOMAIN] = bridge
    entry.runtime_data = bridge
    frontend.async_register_built_in_panel(
        hass,
        "custom",
        sidebar_title="HomeBuddy Access",
        sidebar_icon="mdi:qrcode",
        frontend_url_path="homebuddy-access",
        config={
            "_panel_custom": {
                "name": "homebuddy-access-panel",
                "module_url": "/homebuddy-access-assets/owner.js?v=1.0.5",
                "embed_iframe": False,
                "trust_external": False,
            }
        },
        require_admin=True,
    )
    return True


async def async_unload_entry(hass, entry):
    hass.data.pop(DOMAIN, None)
    frontend.async_remove_panel(hass, "homebuddy-access")
    return True


async def async_remove_entry(hass, entry):
    from homeassistant.helpers.storage import Store

    await Store(hass, 1, DOMAIN + ".permanent").async_remove()
    await Store(hass, 1, DOMAIN + ".connection").async_remove()
