# Security model

Only the active, non-system HA owner can use this panel/API. Native HA authentication
and same-origin browser checks protect it. Tokens must validate with HA and belong to
the current owner with type long_lived_access_token. Normal login tokens, revoked
credentials and other users' tokens are rejected. The integration lists the oldest
long-lived token name but cannot retrieve the original token text. The owner can explicitly create a new token and QR with one button, or paste a saved
token through the optional manual flow.

The QR contains the account's full-access credential. It is for connecting the owner's
own app, not granting limited guest access. Never publish screenshots containing a
real QR. Revoke tokens in HA when no longer needed. Local HTTP is unencrypted and
requires a trusted network. External URLs must be HTTPS origins. The integration
uses HA config.api for local detection and never fetches arbitrary external URLs.

Token text exists only in the submitted request, QR generation and the panel's live
memory. It is not logged or persisted by this integration, and no browser token
storage is used. API responses are no-store; QR generation uses bundled segno.
The app stores its imported token using its existing token settings behavior.
Old grant/session/key storage and previous connection settings are removed on setup.
The remote field always starts blank. A full restart is needed when replacing HA code.

Automatic creation uses the same HA auth manager methods as HA's long-lived-token
websocket command. It creates a uniquely named token for the authenticated owner;
no existing tokens are replaced or revoked. Tokens last 3650 days unless revoked.
The UI disables repeat clicks while generating; a lost HTTP response may still leave
a created token in HA. Check the HA profile and revoke unused tokens before retrying.
Failed QR generation removes the newly created record. No raw token is returned
outside the QR SVG, and no additional integration copy is persisted.

Optional entity filters only configure app display. They do not reduce the HA token's
permissions. The owner-only entity list exposes names/IDs only for the six supported
domains. Edited local origins are validated, and HTTP is limited to private IPs or
.local hostnames; this does not verify ownership of the chosen server. Confirm the
address before importing. QR generation rejects oversized payloads and removes any
newly created token on that failure.
