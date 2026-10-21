# HomeBuddy Access — connection QR

A simple Home Assistant integration that generates a connection QR for the HomeBuddy
app. It detects HA's local address, accepts an optional external HTTPS address and
lets you choose **Local** or **Remote** before generating the QR.

The QR uses the app's existing long-lived-token format. **It contains your account's
access token: keep it private and scan only with your own app.** It is not a limited
guest invitation. Home Assistant exposes token names, but not their original text.

## Install with HACS

Requires **Home Assistant 2026.10.2+**, [HACS](https://www.hacs.xyz/docs/use/download/download/)
and the Home Assistant **owner account**. This is a custom integration, not an app
under Settings → Apps.

[![Open HomeBuddy Access in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FilipposPirpilidis&repository=homebudddy-access&category=integration)

1. Open **HACS → ⋮ → Custom repositories**.
2. Enter `https://github.com/FilipposPirpilidis/homebudddy-access` and select
   **Integration** as the type/category. Add the repository.
3. Find **HomeBuddy Access**, open it and select **Download**.
4. **Restart Home Assistant** (a YAML reload is not enough).
5. As the owner, open **Settings → Devices & services → Add integration** and search
   for **HomeBuddy Access**. Complete setup once.
6. Open **HomeBuddy Access** in the sidebar.

No `configuration.yaml` entry is needed. If you already installed it manually, back
up HA, add the same repository in HACS and download it. Keep the existing config
entry; restart HA without adding a duplicate integration. For old 0.x installations,
read the breaking migration notes below before upgrading.

## Update or remove

- **Update:** download the update in HACS and restart Home Assistant. Reload the panel
  after restart if it still shows the previous interface.
- **Remove:** remove the entry in Settings → Devices & services, remove the download
  in HACS and restart. Revoke unused HomeBuddy tokens separately in your HA profile
  → Security → Long-lived access tokens. Removing the integration does not revoke them.
- **Manual installation:** copy `custom_components/homebuddy_access` into HA's
  `config/custom_components/` directory, replacing the old integration folder, and
  restart. Do not merge leftover guest-client files from earlier versions.

## Get HomeBuddy

- [iOS — App Store](https://apps.apple.com/app/id6738934960)
- [Android — Google Play](https://play.google.com/store/apps/details?id=com.fpirpilidis.homebuddyandroid)

Store builds may lag behind source changes. Entity-filter import requires a compatible
mobile build; Android QR/filter behavior has not been verified in this repository.

![HomeBuddy](custom_components/homebuddy_access/brand/icon.png)

## Connect your phone

1. Check the automatically detected local address; edit it if needed (for example,
   `http://homeassistant.local:8123`).
2. Optionally enter an existing remote HTTPS origin, e.g. `https://your-home.example`.
3. Select **Local** if the phone is on the same network; select **Remote** for access
   over the internet. Remote is disabled until an external address is entered.
4. Optionally select entities under Switches, Lights, Scripts, Humidifiers, Fans and Automations.
   Leave all unchecked to show all. These filters change what the app displays; they
   do not restrict token permissions.
5. Press **Create token & generate QR**. HA creates a uniquely named HomeBuddy token
   valid for 3650 days (approximately 10 years) and opens the QR in a popup automatically.
6. Scan with HomeBuddy's Home Assistant scanner and confirm the settings. No copying,
   pasting or additional login is needed.

To reuse a saved token instead, expand **Use an existing token instead**.
The panel includes manual token-creation instructions there as a fallback.

The remote field starts blank with a placeholder; no previous remote address is
prefilled or saved. HA stores its normal token record; this integration keeps no extra token copy. Revoke it in your HA
profile to invalidate it. This does not create a tunnel or remote endpoint. Local
HTTP sends credentials unencrypted; use it only on a trusted network.

## Migration from 0.x / 1.0.0

1.0.3 generates `homebuddy-ha-access` version 1 with `useLongLivedToken=true`, matching
the HomeBuddy token importer. It replaces 1.0.0's address-only QR generation.
Guest APIs and scoped access remain removed. Old grants, session digests, signing keys
and saved connection settings are deleted on setup. HA accounts/tokens are not deleted.
Mobile apps are distributed separately from this integration.

## Development

```
uv sync --locked --group dev
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
node tests/frontend/browser-check.cjs
```

Browser tests require Playwright and Chrome. Screenshots are written to the ignored
`test-results/` directory. See [protocol](docs/protocol.md) and
[security](docs/security.md) for implementation details.

Entity-filter import requires a HomeBuddy version supporting `filterItems`.
Older builds can connect but ignore the new filterItems field. If the selection is
too large for one QR, select fewer entities and configure the rest in the app.

## Publishing and support

Maintainers: follow [the HACS release checklist](docs/hacs-release.md). The project can
be installed as a custom repository; it is not claiming default-catalog acceptance.
See [release notes](CHANGELOG.md) and [security details](docs/security.md).
Report bugs in [GitHub Issues](https://github.com/FilipposPirpilidis/homebudddy-access/issues),
including versions and sanitized logs. Never attach real tokens or QR credentials.

Licensed under the [MIT License](LICENSE).
