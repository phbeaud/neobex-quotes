"""Authentification OAuth2 Zoho Invoice."""
from __future__ import annotations

import time
import requests
from src.config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN

_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"

# Cache du token en mémoire (valide ~55 min, Zoho donne 1h)
_cached_token = None
_token_expires_at = 0.0


def get_access_token(force_refresh: bool = False) -> str:
    """Obtient un access token via le refresh token OAuth2.

    Utilise un cache en mémoire pour éviter le rate limiting.
    Le token Zoho est valide 1h ; on le renouvelle à 55 min.
    """
    global _cached_token, _token_expires_at

    # Retourner le token en cache s'il est encore valide
    if not force_refresh and _cached_token and time.time() < _token_expires_at:
        return _cached_token

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
    # Cache pour 55 minutes (Zoho donne 1h)
    _token_expires_at = time.time() + 55 * 60
    return _cached_token


def get_headers() -> dict:
    """Retourne les headers HTTP pour les appels API Zoho."""
    token = get_access_token()
    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }
