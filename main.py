"""
main.py — FastAPI application entry point.

Exposes REST endpoints for the Structured Products Gateway.
Simulates the interface between a bank's internal pricing system (Murex)
and external structured products distribution platforms (SIMON/Luma/HALO).

Endpoints:
    POST /products          → submit a structured product to vendor
    POST /products/pricing  → request pricing (fair value + Greeks)
    GET  /products          → list all submitted products
    GET  /products/{isin}   → get a specific product by ISIN
    GET  /health            → health check

Usage:
    pip install -r requirements.txt
    uvicorn main:app --reload
    Docs: http://localhost:8000/docs
"""

import logging
import uuid
from fastapi import FastAPI, HTTPException, Header
from datetime import date

from config import API_TITLE, API_VERSION
from models import (
    StructuredProduct, ProductStatus,
    PricingRequest, PricingResponse
)
from gateway import submit_product, request_pricing

# ── Logging setup ─────────────────────────────────────────────────────────────
# Structured log format — compatible with ELK / Datadog ingestion
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
log = logging.getLogger("main")

# ── FastAPI app ───────────────────────────────────────────────────────────────
# Instantiating FastAPI automatically generates:
# - /docs  → Swagger UI interactive test page
# - /openapi.json → API contract in OpenAPI 3.1 format
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="""
    API Gateway for Structured Products distribution.
    Simulates connectivity between internal pricing systems
    and external distribution platforms (SIMON/Luma/HALO pattern).

    Implements: OAuth2 auth, payload mapping, retry logic, idempotency.
    """
)

# ── In-memory storage ─────────────────────────────────────────────────────────
# In production: replace with PostgreSQL or MongoDB
_products_db: dict = {}

# Idempotency store — tracks processed request keys
# In production: replace with Redis for distributed environments
_idempotency_store: set = set()


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Used for monitoring, pre-demo verification, and post-deployment validation.
    Returns system status and current product count.
    """
    return {
        "status": "healthy",
        "version": API_VERSION,
        "products_count": len(_products_db)
    }


# ── Submit Product ────────────────────────────────────────────────────────────

@app.post("/products", status_code=201)
async def create_product(
    product: StructuredProduct,
    x_idempotency_key: str = Header(None)
):
    """
    Submit a structured product to the vendor platform.

    Flow:
    1. Resolve idempotency key (from header or auto-generate)
    2. Check for duplicate — return DUPLICATE if already processed
    3. Register the key immediately to prevent race conditions
    4. Generate ISIN if not provided
    5. Map payload to vendor format (gateway.py)
    6. Add OAuth2 Bearer Token (auth.py)
    7. Send to vendor with retry logic (gateway.py)
    8. Store product and return vendor response

    Headers:
        x-idempotency-key: unique key to prevent duplicate submissions
                           If not provided, auto-generated per request
    """

    # Step 1 — Resolve idempotency key
    if x_idempotency_key:
        product.idempotency_key = x_idempotency_key
    else:
        # Auto-generate if not provided
        # Note: each call generates a new key → no deduplication
        product.idempotency_key = str(uuid.uuid4())

    # Step 2 — Idempotency check
    # Must happen BEFORE any processing to prevent duplicates
    if product.idempotency_key in _idempotency_store:
        log.warning(
            "Duplicate request detected — idempotency_key=%s",
            product.idempotency_key
        )
        return {
            "status": "DUPLICATE",
            "idempotency_key": product.idempotency_key
        }

    # Step 3 — Register key immediately
    _idempotency_store.add(product.idempotency_key)

    # Step 4 — Generate ISIN if not provided
    # ISIN format: XS + 10 hex characters (simulated)
    if not product.isin:
        product.isin = f"XS{uuid.uuid4().hex[:10].upper()}"

    log.info(
        "Submitting product type=%s isin=%s notional=%s",
        product.product_type, product.isin, product.notional
    )

    try:
        # Step 5-7 — Payload mapping + OAuth2 + send to vendor
        vendor_response = await submit_product(product)

        # Step 8 — Store and return
        product.status = ProductStatus.SUBMITTED
        _products_db[product.isin] = product

        log.info("Product %s successfully submitted to vendor", product.isin)

        return {
            "isin": product.isin,
            "status": product.status,
            "vendor_response": vendor_response,
            "idempotency_key": product.idempotency_key
        }

    except RuntimeError as e:
        # Remove key from store on failure — allow retry with same key
        _idempotency_store.discard(product.idempotency_key)
        log.error("Failed to submit product %s: %s", product.isin, e)
        raise HTTPException(status_code=503, detail=str(e))


# ── Request Pricing ───────────────────────────────────────────────────────────

@app.post("/products/pricing", response_model=PricingResponse)
async def get_pricing(pricing_req: PricingRequest):
    """
    Request pricing for an existing product.

    Returns fair value and Greeks (delta, gamma, vega).
    Greeks are risk sensitivity measures used by traders
    to manage their exposure.

    - delta: sensitivity to underlying price movement
    - gamma: rate of change of delta
    - vega:  sensitivity to volatility changes
    """
    # Verify product exists before requesting pricing
    if pricing_req.product_isin not in _products_db:
        raise HTTPException(
            status_code=404,
            detail=f"Product {pricing_req.product_isin} not found. "
                   f"Submit the product first via POST /products."
        )

    log.info("Pricing request for isin=%s date=%s",
             pricing_req.product_isin, pricing_req.pricing_date)

    try:
        return await request_pricing(pricing_req)
    except RuntimeError as e:
        log.error("Pricing request failed for %s: %s", pricing_req.product_isin, e)
        raise HTTPException(status_code=503, detail=str(e))


# ── List Products ─────────────────────────────────────────────────────────────

@app.get("/products")
async def list_products():
    """
    List all submitted products.
    Used for UAT verification and monitoring.
    """
    return {
        "count": len(_products_db),
        "products": list(_products_db.values())
    }


# ── Get Product by ISIN ───────────────────────────────────────────────────────

@app.get("/products/{isin}")
async def get_product(isin: str):
    """
    Retrieve a specific product by ISIN.
    Used to verify submission status after POST /products.
    """
    if isin not in _products_db:
        raise HTTPException(
            status_code=404,
            detail=f"Product {isin} not found"
        )
    return _products_db[isin]