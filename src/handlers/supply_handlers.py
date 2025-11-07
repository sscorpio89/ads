"""
Handlers для работы с заявками на поставку FBO через Telegram Mini App.

Предоставляет API endpoints для веб-интерфейса:
- POST /api/supplies/create - создание заявки на поставку
- GET /api/supplies/list - получение списка заявок
- GET /api/supplies/{supply_id} - получение информации о заявке
- PUT /api/supplies/{supply_id} - редактирование заявки
- DELETE /api/supplies/{supply_id} - удаление заявки
- GET /api/timeslots/{warehouse_id} - получение доступных слотов
- GET /api/warehouses - получение списка складов
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from ..services.supply_service import SupplyService, SupplyServiceError
from ..api.ozon_client import OzonAPIClient
from ..models.supply import (
    SupplyRequest,
    TimeslotInfo,
    DeliveryType,
    SupplyStatus,
    CargoItem,
    ProductInCargo,
    CargoType,
    Warehouse,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models для API
# ============================================================================

class CreateSupplyRequest(BaseModel):
    """Запрос на создание заявки на поставку."""
    warehouse_id: int = Field(..., description="ID склада")
    supply_date: str = Field(..., description="Дата поставки (YYYY-MM-DD)", example="2025-11-15")
    timeslot_from: str = Field(..., description="Начало слота (HH:MM)", example="10:00")
    timeslot_to: str = Field(..., description="Конец слота (HH:MM)", example="14:00")
    delivery_type: DeliveryType = Field(default=DeliveryType.FBO, description="Тип доставки")
    cargoes: Optional[List[CargoItem]] = Field(None, description="Список грузомест")

    class Config:
        json_schema_extra = {
            "example": {
                "warehouse_id": 12345,
                "supply_date": "2025-11-15",
                "timeslot_from": "10:00",
                "timeslot_to": "14:00",
                "delivery_type": "fbo",
                "cargoes": [
                    {
                        "cargo_id": "CARGO001",
                        "cargo_type": "Короб",
                        "products": [
                            {"product_id": 123456, "quantity": 10}
                        ],
                        "weight": 15.5
                    }
                ]
            }
        }


class UpdateSupplyRequest(BaseModel):
    """Запрос на обновление заявки на поставку."""
    supply_date: Optional[str] = Field(None, description="Новая дата поставки")
    timeslot_from: Optional[str] = Field(None, description="Новое начало слота")
    timeslot_to: Optional[str] = Field(None, description="Новый конец слота")


class SupplyListResponse(BaseModel):
    """Ответ со списком заявок."""
    success: bool = True
    supplies: List[SupplyRequest]
    total: int


class SupplyResponse(BaseModel):
    """Ответ с информацией о заявке."""
    success: bool = True
    supply: SupplyRequest


class TimeslotsResponse(BaseModel):
    """Ответ с информацией о временных слотах."""
    success: bool = True
    timeslots: TimeslotInfo


class WarehousesResponse(BaseModel):
    """Ответ со списком складов."""
    success: bool = True
    warehouses: List[Warehouse]


class SuccessResponse(BaseModel):
    """Ответ об успешной операции."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Ответ об ошибке."""
    success: bool = False
    error: str
    details: Optional[str] = None


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_supply_service(
    client_id: str = Depends(lambda: "from_database"),  # TODO: получать из БД
    api_key: str = Depends(lambda: "from_database")     # TODO: получать из БД
) -> SupplyService:
    """
    Получить экземпляр SupplyService с инициализированным клиентом.

    TODO: В реальном приложении client_id и api_key должны:
    1. Извлекаться из БД на основе user_id из Telegram
    2. Расшифровываться перед использованием
    3. Валидироваться
    """
    ozon_client = OzonAPIClient(client_id=client_id, api_key=api_key)
    return SupplyService(ozon_client)


# ============================================================================
# Handlers для Telegram Mini App
# ============================================================================

class SupplyHandlers:
    """Класс с handlers для работы с заявками на поставку."""

    def __init__(self):
        self.router = APIRouter(prefix="/api", tags=["supplies"])
        self._setup_routes()

    def _setup_routes(self):
        """Настройка маршрутов API."""

        @self.router.post(
            "/supplies/create",
            response_model=SupplyResponse,
            summary="Создать заявку на поставку",
            description="Создает новую заявку на поставку FBO с указанными параметрами"
        )
        async def create_supply(
            request: CreateSupplyRequest = Body(...),
            service: SupplyService = Depends(get_supply_service)
        ):
            """
            Создать заявку на поставку FBO.

            - **warehouse_id**: ID склада Ozon
            - **supply_date**: Дата поставки в формате YYYY-MM-DD
            - **timeslot_from**: Начало временного слота (HH:MM)
            - **timeslot_to**: Конец временного слота (HH:MM)
            - **cargoes**: Опциональный список грузомест
            """
            try:
                logger.info(f"Creating supply for warehouse {request.warehouse_id}")

                supply = await service.create_supply_request(
                    warehouse_id=request.warehouse_id,
                    supply_date=request.supply_date,
                    timeslot_from=request.timeslot_from,
                    timeslot_to=request.timeslot_to,
                    delivery_type=request.delivery_type,
                    cargoes=request.cargoes
                )

                return SupplyResponse(supply=supply)

            except SupplyServiceError as e:
                logger.error(f"Error creating supply: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.get(
            "/supplies/list",
            response_model=SupplyListResponse,
            summary="Получить список заявок",
            description="Возвращает список заявок на поставку с возможностью фильтрации"
        )
        async def get_supplies_list(
            limit: int = 50,
            offset: int = 0,
            status: Optional[str] = None,
            service: SupplyService = Depends(get_supply_service)
        ):
            """
            Получить список заявок на поставку.

            - **limit**: Максимальное количество заявок (по умолчанию 50)
            - **offset**: Смещение для пагинации (по умолчанию 0)
            - **status**: Фильтр по статусу (draft, confirmed, in_transit, delivered, cancelled)
            """
            try:
                status_enum = SupplyStatus(status) if status else None
                supplies = await service.get_supply_requests(
                    limit=limit,
                    offset=offset,
                    status=status_enum
                )

                return SupplyListResponse(
                    supplies=supplies,
                    total=len(supplies)
                )

            except ValueError:
                raise HTTPException(status_code=400, detail=f"Неверный статус: {status}")
            except SupplyServiceError as e:
                logger.error(f"Error fetching supplies: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.get(
            "/supplies/{supply_id}",
            response_model=SupplyResponse,
            summary="Получить информацию о заявке",
            description="Возвращает подробную информацию о конкретной заявке"
        )
        async def get_supply_by_id(
            supply_id: str,
            service: SupplyService = Depends(get_supply_service)
        ):
            """
            Получить информацию о конкретной заявке на поставку.

            - **supply_id**: ID заявки
            """
            try:
                supply = await service.get_supply_by_id(supply_id)
                return SupplyResponse(supply=supply)

            except SupplyServiceError as e:
                logger.error(f"Error fetching supply {supply_id}: {str(e)}")
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.put(
            "/supplies/{supply_id}",
            response_model=SupplyResponse,
            summary="Редактировать заявку",
            description="Обновляет параметры существующей заявки (ребукинг)"
        )
        async def update_supply(
            supply_id: str,
            request: UpdateSupplyRequest = Body(...),
            service: SupplyService = Depends(get_supply_service)
        ):
            """
            Редактировать заявку на поставку.

            ВАЖНО: Фактически создается новая заявка с новыми параметрами,
            а старая отменяется (ребукинг).

            - **supply_id**: ID заявки для редактирования
            - **supply_date**: Новая дата поставки (опционально)
            - **timeslot_from**: Новое начало слота (опционально)
            - **timeslot_to**: Новый конец слота (опционально)
            """
            try:
                updated_supply = await service.update_supply_request(
                    supply_id=supply_id,
                    new_supply_date=request.supply_date,
                    new_timeslot_from=request.timeslot_from,
                    new_timeslot_to=request.timeslot_to
                )

                return SupplyResponse(supply=updated_supply)

            except SupplyServiceError as e:
                logger.error(f"Error updating supply {supply_id}: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.delete(
            "/supplies/{supply_id}",
            response_model=SuccessResponse,
            summary="Удалить заявку",
            description="Отменяет (удаляет) заявку на поставку"
        )
        async def delete_supply(
            supply_id: str,
            reason: Optional[str] = None,
            service: SupplyService = Depends(get_supply_service)
        ):
            """
            Удалить (отменить) заявку на поставку.

            - **supply_id**: ID заявки
            - **reason**: Причина отмены (опционально)
            """
            try:
                success = await service.delete_supply_request(supply_id)

                if success:
                    return SuccessResponse(
                        message=f"Заявка {supply_id} успешно отменена"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Не удалось отменить заявку"
                    )

            except SupplyServiceError as e:
                logger.error(f"Error deleting supply {supply_id}: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.get(
            "/timeslots/{warehouse_id}",
            response_model=TimeslotsResponse,
            summary="Получить доступные слоты",
            description="Возвращает информацию о доступных временных слотах для склада"
        )
        async def get_timeslots(
            warehouse_id: int,
            delivery_type: str = "fbo",
            service: SupplyService = Depends(get_supply_service)
        ):
            """
            Получить доступные временные слоты для склада.

            - **warehouse_id**: ID склада
            - **delivery_type**: Тип доставки (fbo или crossborder)
            """
            try:
                delivery_type_enum = DeliveryType(delivery_type)
                timeslots = await service.get_available_timeslots(
                    warehouse_id=warehouse_id,
                    delivery_type=delivery_type_enum
                )

                return TimeslotsResponse(timeslots=timeslots)

            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный тип доставки: {delivery_type}"
                )
            except SupplyServiceError as e:
                logger.error(f"Error fetching timeslots: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.get(
            "/warehouses",
            response_model=WarehousesResponse,
            summary="Получить список складов",
            description="Возвращает список доступных складов Ozon"
        )
        async def get_warehouses(
            service: SupplyService = Depends(get_supply_service)
        ):
            """Получить список доступных складов Ozon."""
            try:
                warehouses = await service.get_warehouses()
                return WarehousesResponse(warehouses=warehouses)

            except SupplyServiceError as e:
                logger.error(f"Error fetching warehouses: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


# ============================================================================
# Создание экземпляра handlers
# ============================================================================

supply_handlers = SupplyHandlers()
router = supply_handlers.router
