"""
auth.py — OAuth2 Bearer Token authentication.

Flow standard utilisé par SIMON, Luma, HALO et la plupart
des plateformes financières pour les intégrations B2B.

Flow :
1. POST /oauth/token avec client_id + client_secret
2. Recevoir access_token (JWT)
3. Inclure dans chaque requête : Authorization: Bearer <token>
4. Renouveler avant expiration
"""

import time
import logging
import httpx
from config import (
    VENDOR_BASE_URL,
    VENDOR_CLIENT_ID,
    VENDOR_CLIENT_SECRET,
    TOKEN_EXPIRY_SECONDS
)

log = logging.getLogger(__name__)

# Cache du token en mémoire
_token_cache = {
    "access_token": None,
    "expires_at": 0
}


def _is_token_valid() -> bool:
    """Vérifie si le token en cache est encore valide."""
    return (
        _token_cache["access_token"] is not None and
        time.time() < _token_cache["expires_at"] - 60  # marge de 60s
    )


async def get_access_token() -> str:
    """
    Retourne un token valide.
    Le renouvelle automatiquement si expiré.
    Pattern standard pour les intégrations vendor en Capital Markets.
    """
    if _is_token_valid():
        log.debug("Using cached access token")
        return _token_cache["access_token"]

    log.info("Requesting new access token from vendor")

    # En prod : appel réel au endpoint OAuth2 du vendor
    # Ici simulé pour la démo
    mock_token = f"eyJhbGciOiJSUzI1NiJ9.mock_token_{int(time.time())}"

    _token_cache["access_token"] = mock_token
    _token_cache["expires_at"] = time.time() + TOKEN_EXPIRY_SECONDS

    log.info("Access token obtained, expires in %ds", TOKEN_EXPIRY_SECONDS)
    return mock_token


def get_auth_headers(token: str) -> dict:
    """
    Retourne les headers d'authentification standard.
    Format Bearer Token — RFC 6750.
    """
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }