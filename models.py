"""
models.py — Modèles de données pour produits structurés.

Trois produits réels utilisés en Capital Markets :
- Autocall : remboursement anticipé si barrière franchie
- Reverse Convertible : coupon élevé, risque de remboursement en actions
- Capital Protected Note : protection du capital + participation à la hausse

Pydantic assure la validation des payloads — même pattern
qu'une intégration SIMON/Luma/HALO réelle.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import date
from typing import Optional


class ProductType(str, Enum):
    AUTOCALL = "AUTOCALL"
    REVERSE_CONVERTIBLE = "REVERSE_CONVERTIBLE"
    CAPITAL_PROTECTED_NOTE = "CAPITAL_PROTECTED_NOTE"


class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PRICING_REQUESTED = "PRICING_REQUESTED"
    PRICED = "PRICED"
    LIVE = "LIVE"
    CALLED = "CALLED"      # Autocall déclenché
    MATURED = "MATURED"
    CANCELLED = "CANCELLED"


class StructuredProduct(BaseModel):
    """
    Modèle principal d'un produit structuré.
    Champs mappés sur le format attendu par SIMON/Luma.
    """
    isin: Optional[str] = Field(None, description="ISIN du produit")
    product_type: ProductType
    underlying: str = Field(..., description="Sous-jacent ex: SPX, AAPL, EUROSTOXX50")
    notional: float = Field(..., gt=0, description="Montant notionnel en USD")
    issue_date: date
    maturity_date: date
    barrier_level: Optional[float] = Field(
        None, ge=0, le=1,
        description="Niveau de barrière ex: 0.70 = 70% du strike initial"
    )
    coupon_rate: Optional[float] = Field(
        None, ge=0,
        description="Taux de coupon annuel ex: 0.08 = 8%"
    )
    capital_protection: Optional[float] = Field(
        None, ge=0, le=1,
        description="Niveau de protection du capital ex: 1.0 = 100%"
    )
    currency: str = Field(default="USD")
    status: ProductStatus = Field(default=ProductStatus.DRAFT)
    idempotency_key: Optional[str] = Field(
        None,
        description="Clé unique pour éviter les doublons en cas de retry"
    )


class PricingRequest(BaseModel):
    """Demande de pricing envoyée au vendor."""
    product_isin: str
    pricing_date: date
    spot_price: float = Field(..., gt=0)
    volatility: float = Field(..., gt=0, description="Volatilité implicite ex: 0.20 = 20%")
    risk_free_rate: float = Field(..., description="Taux sans risque ex: 0.05 = 5%")


class PricingResponse(BaseModel):
    """Réponse de pricing reçue du vendor."""
    product_isin: str
    fair_value: float
    delta: float
    gamma: float
    vega: float
    pricing_date: date
    vendor_ref: str


class VendorPayload(BaseModel):
    """
    Payload mappé vers le format vendor externe.
    Démontre le payload mapping interne → externe.
    """
    instrumentType: str           # mappé depuis product_type
    underlyingAsset: str          # mappé depuis underlying
    principalAmount: float        # mappé depuis notional
    barrierPercentage: Optional[float]  # mappé depuis barrier_level
    annualCouponRate: Optional[float]   # mappé depuis coupon_rate
    capitalProtectionLevel: Optional[float]
    issuanceDate: str
    maturityDate: str
    currencyCode: str
    idempotencyKey: Optional[str]