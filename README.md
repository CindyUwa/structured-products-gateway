# Structured Products API Gateway

REST API gateway simulating integration between a bank's internal
pricing system and external structured products distribution platforms
— SIMON, Luma, HALO connectivity pattern.

## What it does
- Submits structured products to vendor platforms via REST API
- Handles OAuth2 bearer token authentication
- Maps internal data models to vendor payload format
- Implements retry logic with exponential backoff
- Enforces idempotency to prevent duplicate submissions
- Provides pricing requests with Greeks (delta, gamma, vega)

## Structured Products Covered
- **Autocall** — early redemption if barrier breached
- **Reverse Convertible** — high coupon, equity downside risk  
- **Capital Protected Note** — capital protection + upside participation

## Run
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Interactive docs → http://localhost:8000/docs

## Architecture
```
config.py   → configuration + constants
models.py   → Pydantic data models (internal + vendor payload)
auth.py     → OAuth2 bearer token management
gateway.py  → vendor integration logic (mapping, retry, idempotency)
main.py     → FastAPI endpoints
```

## Integration Runbook
1. POST /products — submit new structured product
2. GET /products/{isin} — verify submission
3. POST /products/pricing — request fair value + Greeks
4. GET /health — verify system status

## Context
Built to demonstrate Capital Markets API integration patterns
for structured products distribution — OAuth2 authentication,
payload mapping, error handling, and idempotency implementation.