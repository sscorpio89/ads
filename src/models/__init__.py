"""Models package for Ozon FBO Supply Bot."""

from .supply import (
    TimeslotInfo,
    SupplyDraft,
    SupplyRequest,
    CargoItem,
    CargoRequest,
    SupplyResponse,
    SupplyListResponse,
)

from .shop import (
    Shop,
    ShopCreateRequest,
    ShopUpdateRequest,
    ShopResponse,
    ShopListResponse,
    ShopCreatedResponse,
)

__all__ = [
    "TimeslotInfo",
    "SupplyDraft",
    "SupplyRequest",
    "CargoItem",
    "CargoRequest",
    "SupplyResponse",
    "SupplyListResponse",
    "Shop",
    "ShopCreateRequest",
    "ShopUpdateRequest",
    "ShopResponse",
    "ShopListResponse",
    "ShopCreatedResponse",
]
