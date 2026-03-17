"""Authentification OAuth2 Zoho Invoice."""
from __future__ import annotations

import requests
from src.config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN

_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"

# Cache du token en mémoire (valide 1h)
_cached_token = None


def get_access_token() -> str:
    """Obtient un access token via le refresh token OAuth2."""
    global _cached_token

    resp = requests.post(_TOKEN_URL, data={
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    })
    resp.raise_for_status()
    data = resp.json()

    if "access_token" not in data:
        raise RuntimeError(f"Erreur OAuth Zoho: {data}")

    _cached_token = data["access_token"]
    return _cached_token


def get_headers() -> dict:
    """Retourne les headers HTTP pour les appels API Zoho."""
    token = get_access_token()
    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }
