# Architecture — Structured Products API Gateway

## Overview

The gateway sits between the bank's internal pricing system
and external distribution platforms.

## Components

### config.py
Central configuration — vendor URLs, credentials, retry settings.
In production: loaded from Azure Key Vault or AWS Secrets Manager.
Never hardcoded.

### models.py
Pydantic data models defining the API contract.
Two schemas:
- StructuredProduct — internal format
- VendorPayload — vendor format (SIMON/Luma)

### auth.py
OAuth2 bearer token management.
- Requests token on first call
- Caches token in memory
- Renews 60 seconds before expiry
- Adds Authorization header to every outgoing request

### gateway.py
Core integration logic:
- map_to_vendor_payload() — translates internal → vendor format
- _call_with_retry() — HTTP calls with exponential backoff
- submit_product() — idempotency check + vendor submission

### main.py
FastAPI application — 5 endpoints, in-memory store,
idempotency tracking.

## Data Flow
Client sends POST /products with StructuredProduct payload
main.py validates via Pydantic (models.py)
Idempotency check — reject if duplicate key
gateway.py maps payload to VendorPayload
auth.py provides Bearer Token
HTTP POST to vendor with retry logic
Vendor response stored and returned

## Key Design Patterns

| Pattern | Implementation | Why |
| Idempotency | UUID key in header | Prevent duplicate submissions |
| Retry + Backoff | 3 attempts, 1/2/4s | Resilience against transient failures |
| Token caching | In-memory with TTL | Avoid unnecessary auth roundtrips |
| Payload mapping | Dedicated function | Clean separation, easy to extend |