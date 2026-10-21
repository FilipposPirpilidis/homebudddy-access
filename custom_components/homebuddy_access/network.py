"""Endpoint metadata and credential-free server identity proofs."""

import ipaddress
from urllib.parse import urlsplit

from .core import Denied


def external_origin(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise Denied("invalid_external_url")
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
            or any(c.isspace() for c in value)
            or "\\" in value
        ):
            raise ValueError
        port = parsed.port
        if port == 0:
            raise ValueError
        host = parsed.hostname.encode("idna").decode("ascii")
        host = f"[{host}]" if ":" in host else host
        return f"https://{host}" + (f":{port}" if port and port != 443 else "")
    except ValueError, UnicodeError:
        raise Denied("invalid_external_url") from None


def local_origin(hass):
    """Use HA's own detected local IP and actual HTTP listener settings."""
    api = hass.config.api
    if api is None:
        return None
    try:
        address = ipaddress.ip_address(api.local_ip)
    except ValueError, TypeError:
        return None
    networks = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
    if not any(address in ipaddress.ip_network(n) for n in networks):
        return None
    host = f"[{address}]" if address.version == 6 else str(address)
    return f"{'https' if api.use_ssl else 'http'}://{host}:{api.port}"


def editable_local_origin(value):
    """Accept HTTPS or private IP/.local HTTP origins without URL credentials."""
    if not isinstance(value, str):
        raise Denied("invalid_local_url")
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https"):
            raise ValueError
        normalized = external_origin("https:" + value[len(parsed.scheme) + 1 :])
        if parsed.scheme == "https":
            return normalized
        host = parsed.hostname or ""
        if not host.endswith(".local"):
            address = ipaddress.ip_address(host)
            if not any(
                address in ipaddress.ip_network(n)
                for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
            ):
                raise ValueError
        # Normalize through HTTPS validation, preserving HTTP's explicit port.
        return "http:" + normalized[6:] + (":443" if parsed.port == 443 else "")
    except ValueError, Denied:
        raise Denied("invalid_local_url") from None
