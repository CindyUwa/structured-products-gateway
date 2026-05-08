"""
gateway.py — Logique d'intégration avec le vendor externe.

Responsabilités :
- Payload mapping : format interne → format vendor
- Appels HTTP with retry logic and exponential backoff
- Idempotency : no duplicate if retry
- Structured error handling

Pattern used to connect internals systems
de pricing/booking to plateformes de distribution
like SIMON, Luma, HALO.
"""

import asyncio
import logging
import httpx
from datetime import datetime
from models import StructuredProduct, PricingRequest, PricingResponse, VendorPayload
from auth import get_access_token, get_auth_headers
from config import VENDOR_BASE_URL, MAX_RETRIES, RETRY_BACKOFF_SECONDS

log = logging.getLogger(__name__)

# Stockage en mémoire des idempotency keys (en prod : Redis ou DB)
_processed_requests: set = set()


def map_to_vendor_payload(product: StructuredProduct) -> VendorPayload:
    """
    Payload mapping : traduit le format interne vers le format vendor.

    C'est le coeur de l'intégration chaque vendor (SIMON, Luma, HALO)
    a son propre schéma. Cette fonction assure la traduction.
    """
    return VendorPayload(
        instrumentType=product.product_type.value,
        underlyingAsset=product.underlying,
        principalAmount=product.notional,
        barrierPercentage=product.barrier_level,
        annualCouponRate=product.coupon_rate,
        capitalProtectionLevel=product.capital_protection,
        issuanceDate=product.issue_date.isoformat(),
        maturityDate=product.maturity_date.isoformat(),
        currencyCode=product.currency,
        idempotencyKey=product.idempotency_key
    )


async def _call_with_retry(
    method: str,
    endpoint: str,
    payload: dict,
    headers: dict
) -> dict:
    """
    Appel HTTP avec retry logic et exponential backoff.

    Retry sur :
    - Erreurs réseau (timeout, connexion refusée)
    - HTTP 429 (rate limit)
    - HTTP 5xx (erreur serveur)

    Pas de retry sur :
    - HTTP 4xx (erreur client — inutile de réessayer)
    """
    url = f"{VENDOR_BASE_URL}{endpoint}"
    backoff = RETRY_BACKOFF_SECONDS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("Attempt %d/%d → %s %s", attempt, MAX_RETRIES, method, endpoint)

            # En prod : vrai appel HTTP
            # Ici simulé pour la démo
            await asyncio.sleep(0.1)  # simule latence réseau

            # Simulation réponse vendor
            mock_response = {
                "vendor_id": f"VND-{hash(str(payload)) % 100000:05d}",
                "status": "ACCEPTED",
                "timestamp": datetime.utcnow().isoformat()
            }
            log.info("Vendor responded: %s", mock_response)
            return mock_response

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            log.warning("Attempt %d failed: %s", attempt, e)
            if attempt < MAX_RETRIES:
                log.info("Retrying in %ds (exponential backoff)", backoff)
                await asyncio.sleep(backoff)
                backoff *= 2  # exponential backoff
            else:
                raise RuntimeError(f"All {MAX_RETRIES} attempts failed: {e}")


async def submit_product(product: StructuredProduct) -> dict:
    """
    Soumet un produit structuré à la plateforme vendor.

    Vérifie l'idempotency key avant de soumettre —
    évite les doublons en cas de retry réseau.
    """
    # Idempotency check
    if product.idempotency_key:
        if product.idempotency_key in _processed_requests:
            log.warning(
                "Duplicate request detected — idempotency_key=%s already processed",
                product.idempotency_key
            )
            return {"status": "DUPLICATE", "idempotency_key": product.idempotency_key}
        _processed_requests.add(product.idempotency_key)

    # Payload mapping
    vendor_payload = map_to_vendor_payload(product)
    log.info("Mapped product %s → vendor payload", product.product_type)

    # Auth
    token = await get_access_token()
    headers = get_auth_headers(token)

    # Appel vendor avec retry
    response = await _call_with_retry(
        method="POST",
        endpoint="/v1/products",
        payload=vendor_payload.dict(),
        headers=headers
    )

    return response


async def request_pricing(pricing_req: PricingRequest) -> PricingResponse:
    """
    Demande un pricing au vendor pour un produit donné.
    Retourne fair value + Greeks (delta, gamma, vega).
    """
    token = await get_access_token()
    headers = get_auth_headers(token)

    await _call_with_retry(
        method="POST",
        endpoint=f"/v1/products/{pricing_req.product_isin}/pricing",
        payload=pricing_req.dict(),
        headers=headers
    )

    # Simulation réponse pricing
    return PricingResponse(
        product_isin=pricing_req.product_isin,
        fair_value=round(pricing_req.spot_price * 0.97, 4),
        delta=0.65,
        gamma=0.02,
        vega=0.18,
        pricing_date=pricing_req.pricing_date,
        vendor_ref=f"PRC-{pricing_req.product_isin}-{pricing_req.pricing_date}"
    )