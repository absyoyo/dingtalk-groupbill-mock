"""Normalize and validate the backend base URL embedded in rebuilt APKs."""

from __future__ import annotations

import argparse
import ipaddress
from urllib.parse import urlsplit, urlunsplit


def normalize_server_url(value: str) -> str:
    """Return a canonical phone-reachable HTTP(S) backend base URL.

    The URL may contain a hostname or IP address and an optional port. Credentials,
    path prefixes, query strings, fragments, loopback addresses, and unspecified
    listener addresses are rejected because they are unsafe or unreachable from
    the phone.
    """
    candidate = value.strip()
    parsed = urlsplit(candidate)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("backend URL scheme must be http or https")
    if not parsed.hostname:
        raise ValueError("backend URL must contain a host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("backend URL must not contain credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("backend URL must not contain a path, query, or fragment")

    hostname = parsed.hostname.lower()
    if any(character.isspace() for character in hostname):
        raise ValueError("backend URL host must not contain whitespace")
    if hostname == "localhost":
        raise ValueError("backend URL must be reachable from the phone")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (address.is_loopback or address.is_unspecified):
        raise ValueError("backend URL must be reachable from the phone")

    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("backend URL contains an invalid port") from error
    if port == 0:
        raise ValueError("backend URL port must be greater than zero")

    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = f"{rendered_host}:{port}" if port is not None else rendered_host
    return urlunsplit((scheme, netloc, "", "", ""))


def main() -> None:
    """Validate one command-line backend URL and print its canonical form."""
    parser = argparse.ArgumentParser()
    parser.add_argument("server_url")
    args = parser.parse_args()
    try:
        normalized = normalize_server_url(args.server_url)
    except ValueError as error:
        parser.error(str(error))
    print(normalized)


if __name__ == "__main__":
    main()
