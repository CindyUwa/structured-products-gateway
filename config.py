"""
config.py — Configuration centrale.
En production : charger depuis AWS Secrets Manager ou Azure Key Vault.
"""

# Vendor platform simulée (SIMON/Luma/HALO pattern)
VENDOR_BASE_URL = "https://api.mock-vendor.com"  # SIMON simulation url
VENDOR_CLIENT_ID = "client_id_here"
VENDOR_CLIENT_SECRET = "client_secret_here"

# Auth
TOKEN_EXPIRY_SECONDS = 3600

# Retry logic
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1  # doublé à chaque essai

# Notre API
API_TITLE = "Structured Products Gateway"
API_VERSION = "1.0.0"