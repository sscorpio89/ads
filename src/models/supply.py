"""
Модели данных для работы с заявками на поставку FBO (Ozon Seller API).

Основные сущности:
- TimeslotInfo: информация о доступных временных слотах
- SupplyDraft: черновик заявки на поставку
- SupplyRequest: заявка на поставку
- CargoItem: информация о грузоместе
- CargoRequest: запрос на создание грузомест
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DeliveryType(str, Enum):
    """Тип доставки на склад Ozon."""
    FBO = "fbo"
    CROSSBORDER = "crossborder"


class SupplyStatus(str, Enum):
    """Статус заявки на поставку."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CargoType(str, Enum):
    """Тип грузоместа."""
    BOX = "Короб"
    PALLET = "Паллета"
    MONO_PALLET = "Монопаллета"
    SUPER_SAFE = "Суперсейф"


# ============================================================================
# Timeslot Models (получение доступных слотов)
# ============================================================================

class TimeslotPeriod(BaseModel):
    """Временной период слота."""
    from_time: str = Field(..., description="Начало слота (HH:MM)")
    to_time: str = Field(..., description="Конец слота (HH:MM)")


class Timeslot(BaseModel):
    """Информация о временном слоте."""
    date: str = Field(..., description="Дата слота (YYYY-MM-DD)")
    period: TimeslotPeriod = Field(..., description="Временной период")
    limit: int = Field(..., description="Лимит приемки (количество товаров)")
    available: bool = Field(..., description="Доступен ли слот для бронирования")


class TimeslotInfo(BaseModel):
    """Информация о доступных временных слотах для склада."""
    warehouse_id: int = Field(..., description="ID склада")
    delivery_type: DeliveryType = Field(..., description="Тип доставки")
    timeslots: List[Timeslot] = Field(default_factory=list, description="Список доступных слотов")


# ============================================================================
# Draft Models (создание черновика поставки)
# ============================================================================

class SupplyDraftRequest(BaseModel):
    """Запрос на создание черновика заявки на поставку."""
    supply_date: str = Field(..., description="Дата поставки (YYYY-MM-DD)")
    timeslot_from: str = Field(..., description="Начало слота (HH:MM)")
    timeslot_to: str = Field(..., description="Конец слота (HH:MM)")
    warehouse_id: int = Field(..., description="ID склада")
    delivery_type: DeliveryType = Field(default=DeliveryType.FBO, description="Тип доставки")

    class Config:
        json_schema_extra = {
            "example": {
                "supply_date": "2025-11-15",
                "timeslot_from": "10:00",
                "timeslot_to": "14:00",
                "warehouse_id": 12345,
                "delivery_type": "fbo"
            }
        }


class SupplyDraft(BaseModel):
    """Черновик заявки на поставку."""
    draft_id: str = Field(..., description="ID черновика")
    supply_date: str = Field(..., description="Дата поставки")
    warehouse_id: int = Field(..., description="ID склада")
    delivery_type: DeliveryType = Field(..., description="Тип доставки")
    created_at: Optional[datetime] = Field(None, description="Время создания")


# ============================================================================
# Supply Models (управление заявками на поставку)
# ============================================================================

class SupplyRequest(BaseModel):
    """Заявка на поставку."""
    supply_id: str = Field(..., description="ID заявки")
    draft_id: Optional[str] = Field(None, description="ID черновика")
    supply_number: Optional[str] = Field(None, description="Номер поставки")
    supply_date: str = Field(..., description="Дата поставки")
    warehouse_id: int = Field(..., description="ID склада")
    warehouse_name: Optional[str] = Field(None, description="Название склада")
    status: SupplyStatus = Field(..., description="Статус заявки")
    timeslot_from: str = Field(..., description="Начало слота")
    timeslot_to: str = Field(..., description="Конец слота")
    total_items: int = Field(default=0, description="Общее количество товаров")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")


class SupplyUpdateRequest(BaseModel):
    """Запрос на обновление заявки на поставку."""
    supply_id: str = Field(..., description="ID заявки")
    supply_date: Optional[str] = Field(None, description="Новая дата поставки")
    timeslot_from: Optional[str] = Field(None, description="Новое начало слота")
    timeslot_to: Optional[str] = Field(None, description="Новый конец слота")


class SupplyCancelRequest(BaseModel):
    """Запрос на отмену заявки на поставку."""
    supply_id: str = Field(..., description="ID заявки на отмену")
    reason: Optional[str] = Field(None, description="Причина отмены")


# ============================================================================
# Cargo Models (управление грузоместами)
# ============================================================================

class ProductInCargo(BaseModel):
    """Товар в грузоместе."""
    product_id: int = Field(..., description="ID товара (SKU)")
    quantity: int = Field(..., description="Количество единиц товара", gt=0)


class CargoItem(BaseModel):
    """Информация о грузоместе."""
    cargo_id: str = Field(..., description="ID грузоместа")
    cargo_type: CargoType = Field(..., description="Тип грузоместа")
    products: List[ProductInCargo] = Field(..., description="Список товаров в грузоместе")
    weight: Optional[float] = Field(None, description="Вес грузоместа (кг)", ge=0)
    width: Optional[int] = Field(None, description="Ширина (см)", ge=0)
    height: Optional[int] = Field(None, description="Высота (см)", ge=0)
    depth: Optional[int] = Field(None, description="Глубина (см)", ge=0)


class CargoRequest(BaseModel):
    """Запрос на создание/обновление грузомест для заявки."""
    draft_id: str = Field(..., description="ID черновика заявки")
    cargoes: List[CargoItem] = Field(..., description="Список грузомест")
    delete_current_version: bool = Field(
        default=False,
        description="Удалить предыдущие версии грузомест"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "draft_id": "12345678-abcd-1234-abcd-123456789012",
                "cargoes": [
                    {
                        "cargo_id": "CARGO001",
                        "cargo_type": "Короб",
                        "products": [
                            {"product_id": 123456, "quantity": 10},
                            {"product_id": 789012, "quantity": 5}
                        ],
                        "weight": 15.5,
                        "width": 40,
                        "height": 30,
                        "depth": 50
                    }
                ],
                "delete_current_version": False
            }
        }


# ============================================================================
# Response Models (ответы от API)
# ============================================================================

class SupplyResponse(BaseModel):
    """Ответ с информацией о заявке на поставку."""
    result: SupplyRequest
    success: bool = True
    message: Optional[str] = None


class SupplyListResponse(BaseModel):
    """Ответ со списком заявок на поставку."""
    result: List[SupplyRequest]
    total: int = Field(..., description="Общее количество заявок")
    has_next: bool = Field(default=False, description="Есть ли еще заявки")
    success: bool = True


class TimeslotInfoResponse(BaseModel):
    """Ответ с информацией о временных слотах."""
    result: TimeslotInfo
    success: bool = True


class DraftCreatedResponse(BaseModel):
    """Ответ при создании черновика."""
    result: SupplyDraft
    success: bool = True
    message: Optional[str] = None


class CargoCreatedResponse(BaseModel):
    """Ответ при создании грузомест."""
    success: bool = True
    message: Optional[str] = None
    cargoes_created: int = Field(default=0, description="Количество созданных грузомест")


# ============================================================================
# Warehouse Models
# ============================================================================

class Warehouse(BaseModel):
    """Информация о складе Ozon."""
    warehouse_id: int = Field(..., description="ID склада")
    name: str = Field(..., description="Название склада")
    address: Optional[str] = Field(None, description="Адрес склада")
    city: Optional[str] = Field(None, description="Город")
    is_active: bool = Field(default=True, description="Активен ли склад")


class WarehouseListResponse(BaseModel):
    """Ответ со списком складов."""
    result: List[Warehouse]
    success: bool = True
