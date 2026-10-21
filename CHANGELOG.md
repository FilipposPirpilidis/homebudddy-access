# Changelog

## 1.0.5

- Local/remote connection QR setup for the HomeBuddy app.
- Automatically detected, editable local URL and optional external HTTPS URL.
- Create an HA long-lived token and its QR in one step, or use a saved token.
- Optional display filters for switches, lights, scripts, humidifiers, fans and automations.
- Responsive QR popup and iOS/Android store links.
- HACS repository metadata, MIT license, validation workflows and installation guide.

### Compatibility and migration

Requires Home Assistant 2026.10.2 or later. QR entity filters require a compatible
HomeBuddy app build; Android filter import has not been tested in this repository.
This is an owner-account connection helper, not a limited guest-access system.
Tokens grant the owner's account access; entity filters affect display only.

Upgrading from 0.x removes the old guest endpoints and stored grants/session digests/
signing keys. Old connection preferences are cleared. Back up HA before upgrading.
The integration does not revoke HA tokens when removed; revoke unused HomeBuddy
tokens in your HA profile → Security → Long-lived access tokens.
