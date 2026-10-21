"""Owner-only, token connection QR setup for HomeBuddy."""

import io
import json
from datetime import timedelta
from uuid import uuid4

import segno
from homeassistant.auth.models import TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.http import KEY_HASS
from homeassistant.helpers.storage import Store

from .core import Denied
from .network import editable_local_origin, external_origin, local_origin

DOMAIN = "homebuddy_access"
ENTITY_DOMAINS = ("switch", "light", "script", "humidifier", "fan", "automation")
PREFIX = "/api/homebuddy_access/v1"


class Bridge:
    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, 1, DOMAIN + ".connection", private=True)

    async def load(self):
        # Do not prefill addresses from either previous generation or legacy setup.
        await self.store.async_remove()
        await Store(self.hass, 1, DOMAIN + ".permanent", private=True).async_remove()

    def settings(self, user):
        tokens = sorted(
            (
                token
                for token in user.refresh_tokens.values()
                if token.token_type == TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
            ),
            key=lambda token: (token.created_at, token.id),
        )
        return {
            "local_url": local_origin(self.hass),
            "external_url": "",
            "use_local": True,
            "entities": {
                domain: [
                    {"entity_id": state.entity_id, "name": state.name}
                    for state in sorted(
                        self.hass.states.async_all(domain), key=lambda s: s.entity_id
                    )
                ]
                for domain in ENTITY_DOMAINS
            },
            "first_token_name": tokens[0].client_name if tokens else None,
        }

    def payload(self, external, use_local, token, local=None, filters=None):
        local = (local_origin(self.hass) or "") if local is None else local
        if use_local and not local:
            raise Denied("local_address_unavailable")
        if not use_local and not external:
            raise Denied("remote_address_required")
        payload = {
            "type": "homebuddy-ha-access",
            "version": 1,
            "localURL": local,
            "remoteURL": external,
            "useLocal": use_local,
            "useLongLivedToken": True,
            "longLivedToken": token,
        }

        if filters is not None:
            payload["filterItems"] = filters
        return payload


def render_qr(payload):
    encoded = json.dumps(payload, separators=(",", ":"))
    if len(encoded.encode()) > 2300:
        raise Denied("qr_too_large_select_fewer_entities")
    output = io.BytesIO()
    segno.make(encoded, micro=False, error="m").save(output, kind="svg", scale=5)
    return output.getvalue().decode()


def response(data, status=200):
    from aiohttp import web

    return web.json_response(
        data,
        status=status,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


class OwnerView(HomeAssistantView):
    url = PREFIX + "/owner"
    name = "api:homebuddy_access:owner"
    requires_auth = True

    async def get(self, request):
        return await self.handle(request)

    async def post(self, request):
        return await self.handle(request, write=True)

    async def handle(self, request, write=False):
        hass = request.app[KEY_HASS]
        user = await hass.auth.async_get_user(request["hass_user"].id)
        if not user or not user.is_owner or not user.is_active or user.system_generated:
            return response({"error": "owner_required"}, 403)
        if (
            request.headers.get("Origin", f"{request.scheme}://{request.host}")
            != f"{request.scheme}://{request.host}"
            or request.headers.get("Sec-Fetch-Site") == "cross-site"
        ):
            return response({"error": "origin_denied"}, 403)
        bridge = hass.data.get(DOMAIN)
        if bridge is None:
            return response({"error": "unavailable"}, 503)
        if not write:
            return response(bridge.settings(user))
        try:
            if request.content_type != "application/json":
                raise Denied("json_required")
            raw = bytearray()
            async for chunk in request.content.iter_chunked(4096):
                raw.extend(chunk)
                if len(raw) > 8192:
                    raise Denied("request_too_large")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise Denied("invalid_input")
            operation = data.get("operation")
            fields = {"operation", "external_url", "use_local"}
            if operation == "generate":
                fields.add("long_lived_token")
            if (
                operation not in ("generate", "create_and_generate")
                or not fields <= set(data)
                or set(data) - fields - {"local_url", "filter_items"}
                or type(data["use_local"]) is not bool
            ):
                raise Denied("invalid_input")
            external = external_origin(data["external_url"])
            local = (
                editable_local_origin(data["local_url"])
                if "local_url" in data
                else None
            )
            filters = data.get("filter_items")
            if "filter_items" in data:
                if (
                    not isinstance(filters, list)
                    or len(filters) > 100
                    or any(
                        not isinstance(item, str)
                        or len(item) > 255
                        or item.split(".")[0] not in ENTITY_DOMAINS
                        or hass.states.get(item) is None
                        for item in filters
                    )
                ):
                    raise Denied("invalid_filter_items")
                filters = sorted(set(filters))
            if operation == "create_and_generate":
                # Reject invalid connection settings before creating any credential.
                payload = bridge.payload(
                    external, data["use_local"], "", local, filters
                )
                record = await hass.auth.async_create_refresh_token(
                    user,
                    client_name="HomeBuddy " + uuid4().hex[:12],
                    token_type=TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
                    access_token_expiration=timedelta(days=3650),
                )
                completed = False
                try:
                    payload["longLivedToken"] = hass.auth.async_create_access_token(
                        record
                    )
                    svg = await hass.async_add_executor_job(render_qr, payload)
                    result = response({"qr_svg": svg, "token_name": record.client_name})
                    completed = True
                    return result
                except Denied as error:
                    return response({"error": str(error)}, 400)
                except Exception:
                    # Never expose token-related exception details to the client/logs.
                    return response({"error": "token_qr_creation_failed"}, 500)
                finally:
                    if not completed:
                        hass.auth.async_remove_refresh_token(record)
            token = data["long_lived_token"]
            if not isinstance(token, str) or not 1 <= len(token) <= 4096:
                raise Denied("long_lived_token_required")
            record = hass.auth.async_validate_access_token(token)
            if (
                record is None
                or record.user.id != user.id
                or record.token_type != TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
            ):
                raise Denied("invalid_owner_long_lived_token")
            payload = bridge.payload(external, data["use_local"], token, local, filters)
            svg = await hass.async_add_executor_job(render_qr, payload)
            return response({"qr_svg": svg, "token_name": record.client_name})
        except (Denied, ValueError, UnicodeDecodeError) as error:
            return response(
                {"error": str(error) if isinstance(error, Denied) else "invalid_json"},
                400,
            )
