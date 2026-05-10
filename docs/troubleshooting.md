# Troubleshooting Guide — Structured Products API Gateway

## Common Issues

### Issue: 503 Service Unavailable
**Symptom:** All retries exhausted, vendor not responding
**Possible causes:**
- Vendor platform maintenance window
- Network connectivity issue
- Rate limiting by vendor

**Resolution:**
1. Check vendor status page
2. Verify network connectivity
3. Increase RETRY_BACKOFF_SECONDS in config.py
4. Implement circuit breaker if persistent

---

### Issue: 422 Validation Error
**Symptom:** Request rejected before reaching vendor
**Possible causes:**
- Invalid product_type value
- Negative notional
- maturity_date before issue_date

**Resolution:**
Check request payload against API contract in docs/api-contracts.md

---

### Issue: Duplicate products created
**Symptom:** Same product appears twice in vendor platform
**Possible cause:** Idempotency key not sent in header
**Resolution:**
Always include X-Idempotency-Key header.
If not provided, system auto-generates per request
(no deduplication guarantee).

---

### Issue: Token expiry during high load
**Symptom:** 401 Unauthorized after extended operation
**Possible cause:** Token cache expired, renewal failed
**Resolution:**
auth.py renews token 60 seconds before expiry.
If renewal fails, restart the service.
In production: implement token refresh retry logic.

---

### Issue: Pricing returns unexpected Greeks
**Symptom:** Delta/vega values seem wrong
**Note:** This demo uses simplified pricing model.
In production: Greeks come from vendor's pricing engine
(Black-Scholes or Monte Carlo simulation).