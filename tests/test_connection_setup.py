from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant.helpers.storage import Store
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homebuddy_access.api import DOMAIN, PREFIX, render_qr


@pytest.fixture
async def setup(hass, hass_owner_user, hass_client_no_auth):
    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    refresh = await hass.auth.async_create_refresh_token(
        hass_owner_user, client_id="https://homebuddy.test"
    )
    token = hass.auth.async_create_access_token(refresh)
    long_refresh = await hass.auth.async_create_refresh_token(
        hass_owner_user,
        client_name="HomeBuddy",
        token_type="long_lived_access_token",
        access_token_expiration=timedelta(days=3650),
    )
    long_token = hass.auth.async_create_access_token(long_refresh)
    client = await hass_client_no_auth()
    with patch(
        "custom_components.homebuddy_access.api.local_origin",
        return_value="http://192.168.1.20:8123",
    ):
        yield SimpleNamespace(
            long_token=long_token,
            long_refresh=long_refresh,
            client=client,
            headers={"Authorization": f"Bearer {token}"},
            entry=entry,
        )


async def generate(setup, **overrides):
    return await setup.client.post(
        PREFIX + "/owner",
        headers=setup.headers,
        json={
            "operation": "generate",
            "long_lived_token": setup.long_token,
            "external_url": "",
            "use_local": True,
            **overrides,
        },
    )


async def test_local_remote_payloads_and_reload(setup, hass):
    with patch(
        "custom_components.homebuddy_access.api.render_qr", wraps=render_qr
    ) as qr:
        result = await generate(setup)
        assert result.status == 200
        data = await result.json()
        assert qr.call_args.args[0] == {
            "type": "homebuddy-ha-access",
            "version": 1,
            "remoteURL": "",
            "localURL": "http://192.168.1.20:8123",
            "useLocal": True,
            "useLongLivedToken": True,
            "longLivedToken": setup.long_token,
        }
        assert "<svg" in data["qr_svg"]
        assert data["token_name"] == "HomeBuddy"
        assert "payload" not in data
        result = await generate(
            setup, external_url="https://ha.example/", use_local=False
        )
        assert result.status == 200
        assert qr.call_args.args[0]["remoteURL"] == "https://ha.example"
    assert await hass.config_entries.async_reload(setup.entry.entry_id)
    settings = await (
        await setup.client.get(PREFIX + "/owner", headers=setup.headers)
    ).json()
    assert settings["external_url"] == ""
    assert settings["use_local"] is True
    assert settings["first_token_name"] == "HomeBuddy"
    assert setup.long_token not in str(settings)


@pytest.mark.parametrize(
    "values",
    [
        {"use_local": False},
        {"use_local": "true"},
        {"external_url": "http://public.example"},
        {"external_url": "https://user:secret@ha.example"},
        {"external_url": "https://ha.example/path"},
        {"external_url": "https://ha.example?token=x"},
        {"operation": "enable"},
        {"long_lived_token": ""},
        {"long_lived_token": "invalid"},
        {"long_lived_token": None},
    ],
)
async def test_invalid_settings(setup, values):
    assert (await generate(setup, **values)).status == 400


async def test_missing_local_remote_still_works(setup):
    with patch(
        "custom_components.homebuddy_access.api.local_origin", return_value=None
    ):
        assert (await generate(setup)).status == 400
        assert (
            await generate(setup, use_local=False, external_url="https://ha.example")
        ).status == 200


async def test_retired_guest_routes_and_csrf(setup):
    for operation in [
        "exchange",
        "execute",
        "web_exchange",
        "web_link",
        "web_claim_link",
    ]:
        assert (
            await setup.client.post(PREFIX + "/guest/" + operation, json={})
        ).status == 404
    assert (await setup.client.get(PREFIX + "/probe?nonce=" + "a" * 64)).status == 404
    assert (await setup.client.get(PREFIX + "/owner")).status == 401
    assert (
        await setup.client.post(
            PREFIX + "/owner",
            headers={**setup.headers, "Origin": "https://evil.example"},
            json={},
        )
    ).status == 403


async def test_legacy_storage_removed(hass):
    legacy = Store(hass, 1, DOMAIN + ".permanent", private=True)
    await legacy.async_save(
        {
            "external_url": "https://ha.example",
            "enabled": True,
            "grants": [{"id": "old"}],
            "sessions": {"digest": "old"},
            "identity": "old-private-key",
        }
    )
    from custom_components.homebuddy_access.api import Bridge

    bridge = Bridge(hass)
    await bridge.load()
    assert await legacy.async_load() is None
    assert await bridge.store.async_load() is None


async def test_owner_api_rejects_admin_and_large_body(setup, hass, hass_admin_user):
    refresh = await hass.auth.async_create_refresh_token(
        hass_admin_user, client_id="https://homebuddy.test"
    )
    token = hass.auth.async_create_access_token(refresh)
    assert (
        await setup.client.get(
            PREFIX + "/owner", headers={"Authorization": f"Bearer {token}"}
        )
    ).status == 403
    assert (
        await setup.client.post(
            PREFIX + "/owner",
            headers={**setup.headers, "Content-Type": "application/json"},
            data='{"x":"' + "a" * 9000 + '"}',
        )
    ).status == 400


async def test_token_revocation_and_normal_token_rejected(setup, hass):
    normal = setup.headers["Authorization"].removeprefix("Bearer ")
    assert (await generate(setup, long_lived_token=normal)).status == 400
    hass.auth.async_remove_refresh_token(setup.long_refresh)
    assert (await generate(setup)).status == 400
    settings = await (
        await setup.client.get(PREFIX + "/owner", headers=setup.headers)
    ).json()
    assert settings["first_token_name"] is None


async def test_other_user_token_rejected(setup, hass, hass_admin_user):
    record = await hass.auth.async_create_refresh_token(
        hass_admin_user, client_name="Other", token_type="long_lived_access_token"
    )
    token = hass.auth.async_create_access_token(record)
    assert (await generate(setup, long_lived_token=token)).status == 400


async def create_token_qr(setup, **overrides):
    return await setup.client.post(
        PREFIX + "/owner",
        headers=setup.headers,
        json={
            "operation": "create_and_generate",
            "external_url": "",
            "use_local": True,
            **overrides,
        },
    )


async def test_create_token_qr_and_revoke(setup, hass, hass_owner_user):
    before = set(hass_owner_user.refresh_tokens)
    with patch(
        "custom_components.homebuddy_access.api.render_qr", wraps=render_qr
    ) as qr:
        result = await create_token_qr(setup)
        assert result.status == 200
        assert result.headers["Cache-Control"] == "no-store"
        body = await result.json()
        payload = qr.call_args.args[0]
    token = payload["longLivedToken"]
    record = hass.auth.async_validate_access_token(token)
    assert record.user is hass_owner_user
    assert record.token_type == "long_lived_access_token"
    assert record.access_token_expiration == timedelta(days=3650)
    assert body["token_name"] == record.client_name
    assert record.client_name.startswith("HomeBuddy ")
    assert set(hass_owner_user.refresh_tokens) - before == {record.id}
    assert "<svg" in body["qr_svg"]
    assert token not in str(body)
    assert payload["useLongLivedToken"] is True
    assert payload["type"] == "homebuddy-ha-access"
    assert await hass.config_entries.async_reload(setup.entry.entry_id)
    assert hass.auth.async_validate_access_token(token) is not None
    hass.auth.async_remove_refresh_token(record)
    assert hass.auth.async_validate_access_token(token) is None


async def test_create_token_invalid_settings_and_failure_cleanup(
    setup, hass_owner_user
):
    before = set(hass_owner_user.refresh_tokens)
    assert (await create_token_qr(setup, use_local=False)).status == 400
    assert (
        await create_token_qr(setup, external_url="http://public.example")
    ).status == 400
    assert (await create_token_qr(setup, long_lived_token="unexpected")).status == 400
    assert set(hass_owner_user.refresh_tokens) == before
    with patch(
        "custom_components.homebuddy_access.api.render_qr",
        side_effect=RuntimeError("private detail"),
    ):
        result = await create_token_qr(setup)
        assert result.status == 500
        assert (await result.json())["error"] == "token_qr_creation_failed"
    assert set(hass_owner_user.refresh_tokens) == before
    assert (
        await create_token_qr(setup, use_local=False, external_url="https://ha.example")
    ).status == 200


async def test_create_token_requires_owner_and_same_origin(
    setup, hass, hass_admin_user, hass_owner_user
):
    data = {"operation": "create_and_generate", "external_url": "", "use_local": True}
    before = set(hass_owner_user.refresh_tokens)
    assert (await setup.client.post(PREFIX + "/owner", json=data)).status == 401
    assert (
        await setup.client.post(
            PREFIX + "/owner",
            json=data,
            headers={**setup.headers, "Origin": "https://evil.example"},
        )
    ).status == 403
    refresh = await hass.auth.async_create_refresh_token(
        hass_admin_user, client_id="https://homebuddy.test"
    )
    admin_token = hass.auth.async_create_access_token(refresh)
    assert (
        await setup.client.post(
            PREFIX + "/owner",
            json=data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).status == 403
    assert set(hass_owner_user.refresh_tokens) == before


async def test_editable_local_and_grouped_filters(setup, hass):
    for domain in (
        "switch",
        "light",
        "script",
        "humidifier",
        "fan",
        "automation",
        "sensor",
    ):
        hass.states.async_set(
            f"{domain}.test", "off", {"friendly_name": "My " + domain}
        )
    settings = await (
        await setup.client.get(PREFIX + "/owner", headers=setup.headers)
    ).json()
    assert set(settings["entities"]) == {
        "switch",
        "light",
        "script",
        "humidifier",
        "fan",
        "automation",
    }
    assert settings["entities"]["fan"][0] == {"entity_id": "fan.test", "name": "My fan"}
    with patch(
        "custom_components.homebuddy_access.api.render_qr", wraps=render_qr
    ) as qr:
        result = await generate(
            setup,
            local_url="http://homeassistant.local:8123/",
            filter_items=["automation.test", "fan.test", "light.test"],
        )
        assert result.status == 200
        payload = qr.call_args.args[0]
        assert payload["localURL"] == "http://homeassistant.local:8123"
        assert payload["filterItems"] == ["automation.test", "fan.test", "light.test"]
        assert (
            await create_token_qr(
                setup, local_url="http://192.168.1.21:8123", filter_items=[]
            )
        ).status == 200
        assert qr.call_args.args[0]["filterItems"] == []


@pytest.mark.parametrize(
    "values",
    [
        {"local_url": "http://public.example"},
        {"local_url": "http://8.8.8.8"},
        {"local_url": "http://user:secret@ha.local"},
        {"local_url": "http://ha.local/path"},
        {"local_url": "http://ha.local?token=x"},
        {"local_url": ""},
        {"filter_items": ["sensor.test"]},
        {"filter_items": ["light.missing"]},
        {"filter_items": None},
        {"filter_items": "light.test"},
    ],
)
async def test_invalid_customization_creates_no_token(setup, hass_owner_user, values):
    before = set(hass_owner_user.refresh_tokens)
    assert (await create_token_qr(setup, **values)).status == 400
    assert set(hass_owner_user.refresh_tokens) == before


async def test_oversize_filter_qr_cleanup(setup, hass, hass_owner_user):
    items = ["light." + "a" * 100 + str(i) for i in range(30)]
    for item in items:
        hass.states.async_set(item, "off")
    before = set(hass_owner_user.refresh_tokens)
    result = await create_token_qr(setup, filter_items=items)
    assert result.status == 400
    assert (await result.json())["error"] == "qr_too_large_select_fewer_entities"
    assert set(hass_owner_user.refresh_tokens) == before
