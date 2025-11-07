"""
Модели данных для магазинов (Ozon Seller аккаунтов).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Shop(BaseModel):
    """Информация о магазине Ozon Seller."""
    shop_id: int = Field(..., description="ID магазина в системе")
    user_id: int = Field(..., description="Telegram User ID владельца")
    name: str = Field(..., description="Название магазина")
    client_id: str = Field(..., description="Ozon Client ID")
    api_key_encrypted: str = Field(..., description="Зашифрованный API ключ")
    is_active: bool = Field(default=True, description="Активен ли магазин")
    created_at: datetime = Field(..., description="Дата добавления")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

    class Config:
        json_schema_extra = {
            "example": {
                "shop_id": 1,
                "user_id": 123456789,
                "name": "Мой магазин на Ozon",
                "client_id": "123456",
                "is_active": True,
                "created_at": "2025-11-07T10:00:00"
            }
        }


class ShopCreateRequest(BaseModel):
    """Запрос на добавление магазина."""
    name: str = Field(..., description="Название магазина", min_length=1, max_length=100)
    client_id: str = Field(..., description="Ozon Client ID", min_length=1)
    api_key: str = Field(..., description="Ozon API Key", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Мой магазин на Ozon",
                "client_id": "123456",
                "api_key": "your-api-key-here"
            }
        }


class ShopUpdateRequest(BaseModel):
    """Запрос на обновление магазина."""
    name: Optional[str] = Field(None, description="Новое название магазина")
    client_id: Optional[str] = Field(None, description="Новый Client ID")
    api_key: Optional[str] = Field(None, description="Новый API Key")
    is_active: Optional[bool] = Field(None, description="Статус активности")


class ShopResponse(BaseModel):
    """Ответ с информацией о магазине (без API ключа)."""
    shop_id: int
    name: str
    client_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "shop_id": 1,
                "name": "Мой магазин на Ozon",
                "client_id": "123456",
                "is_active": True,
                "created_at": "2025-11-07T10:00:00"
            }
        }


class ShopListResponse(BaseModel):
    """Ответ со списком магазинов."""
    success: bool = True
    shops: list[ShopResponse]
    total: int


class ShopCreatedResponse(BaseModel):
    """Ответ при создании магазина."""
    success: bool = True
    shop: ShopResponse
    message: str = "Магазин успешно добавлен"
