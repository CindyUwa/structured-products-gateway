# API Contracts — Structured Products API Gateway

## Authentication

All requests to the vendor platform include:
Authorization: Bearer <token>
Content-Type: application/json
X-Idempotency-Key: <uuid>
## Endpoints

### POST /products
Submit a structured product to the vendor platform.

**Request:**
```json
{
  "product_type": "AUTOCALL",
  "underlying": "AAPL",
  "notional": 1000000,
  "issue_date": "2026-06-01",
  "maturity_date": "2029-06-01",
  "barrier_level": 0.70,
  "coupon_rate": 0.08,
  "currency": "USD"
}
```

**Response 201:**
```json
{
  "isin": "XS4CF805A825",
  "status": "SUBMITTED",
  "vendor_response": {
    "vendor_id": "VND-54417",
    "status": "ACCEPTED",
    "timestamp": "2026-05-08T10:00:00"
  },
  "idempotency_key": "550e8400-e29b-41d4-a716"
}
```

**Response 200 (duplicate):**
```json
{
  "status": "DUPLICATE",
  "idempotency_key": "550e8400-e29b-41d4-a716"
}
```

### POST /products/pricing
Request fair value and Greeks for a submitted product.

**Request:**
```json
{
  "product_isin": "XS4CF805A825",
  "pricing_date": "2026-05-08",
  "spot_price": 185.50,
  "volatility": 0.25,
  "risk_free_rate": 0.05
}
```

**Response 200:**
```json
{
  "product_isin": "XS4CF805A825",
  "fair_value": 179.935,
  "delta": 0.65,
  "gamma": 0.02,
  "vega": 0.18,
  "pricing_date": "2026-05-08",
  "vendor_ref": "PRC-XS4CF805A825-2026-05-08"
}
```

## Payload Mapping

| Internal Field | Vendor Field | Notes |
| product_type | instrumentType | AUTOCALL, REVERSE_CONVERTIBLE |
| notional | principalAmount | USD amount |
| barrier_level | barrierPercentage | 0.70 = 70% |
| coupon_rate | annualCouponRate | 0.08 = 8% |
| issue_date | issuanceDate | ISO 8601 |