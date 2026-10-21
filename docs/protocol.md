# HomeBuddy connection QR protocol

## QR payload

```json
{
  "type": "homebuddy-ha-access",
  "version": 1,
  "localURL": "http://192.168.1.20:8123",
  "remoteURL": "",
  "useLocal": true,
  "useLongLivedToken": true,
  "longLivedToken": "<access-token>",
  "filterItems": ["light.kitchen", "automation.evening"]
}
```

The selected connection URL must exist. Remote URLs must be HTTPS origins. Local
URLs allow HTTPS, or HTTP with private IP addresses and `.local` hostnames. URLs
must not contain credentials, a query, a fragment or a non-root path.

The QR is reusable and contains an account credential. The app confirms the settings
before importing the token. `filterItems` is an optional display allow-list, not an
authorization boundary. An empty list means show all; an omitted field leaves the
app's existing filters unchanged. Supported domains: switch, light, script,
humidifier, fan and automation. Filter support requires a compatible mobile version.

The UTF-8 JSON payload is limited to 2300 bytes to fit one QR code.

## Owner API

All operations use `/api/homebuddy_access/v1/owner` and require the active Home
Assistant owner. Browser requests are subject to same-origin checks. Responses use
`Cache-Control: no-store`. Requests are limited to 8 KiB.

### GET

Returns `local_url`, an empty `external_url`, `use_local=true`, `first_token_name`
and `entities` grouped by supported domain. Each entity has `entity_id` and `name`.
Token metadata never includes the original token text.

### POST

Both operations require `external_url` (string) and `use_local` (boolean). Optional
`local_url` overrides detection. Optional `filter_items` accepts up to 100 current
entities from the supported domains; duplicates are removed and IDs are sorted.

- `operation="generate"` also requires `long_lived_token`. The token must validate
  with HA, belong to the current owner and be a long-lived access token.
- `operation="create_and_generate"` creates a uniquely named HomeBuddy token through
  HA's auth manager with a lifespan of 3650 days.

Success returns `qr_svg` and `token_name`. QR generation runs locally. The raw token
is not returned as a separate field or persisted by the integration. HA manages its
normal token record, which survives restart and can be revoked from the owner profile.

Invalid connection settings are rejected before token creation. If signing or QR
rendering fails, the new token is removed. An oversized payload returns
`qr_too_large_select_fewer_entities`. Requests are not retried automatically: a lost
HTTP response can leave a created token in HA, which can be revoked manually.
