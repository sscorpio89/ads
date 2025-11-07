"""
Handlers для управления магазинами через Telegram Mini App.

API endpoints:
- POST /api/shops/add - добавление магазина
- GET /api/shops/list - список магазинов пользователя
- GET /api/shops/{shop_id} - информация о магазине
- PUT /api/shops/{shop_id} - обновление магазина
- DELETE /api/shops/{shop_id} - удаление магазина
"""

import logging
from fastapi import APIRouter, HTTPException, Body, Header
from typing import Optional

from ..services.shop_service import shop_service, ShopServiceError
from ..models.shop import (
    ShopCreateRequest,
    ShopUpdateRequest,
    ShopResponse,
    ShopListResponse,
    ShopCreatedResponse,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================

class SuccessResponse:
    """Успешный ответ."""
    success: bool = True
    message: str


class ErrorResponse:
    """Ответ об ошибке."""
    success: bool = False
    error: str


# ============================================================================
# Helper функции
# ============================================================================

def get_user_id_from_header(x_telegram_user_id: Optional[str] = Header(None)) -> int:
    """
    Получить User ID из заголовка запроса.

    В production версии нужно:
    1. Валидировать данные через Telegram WebApp initData
    2. Проверять подпись данных
    3. Использовать middleware для аутентификации
    """
    if not x_telegram_user_id:
        # Для тестирования возвращаем тестовый ID
        return 123456789

    try:
        return int(x_telegram_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверный формат User ID")


# ============================================================================
# Handlers
# ============================================================================

class ShopHandlers:
    """Класс с handlers для управления магазинами."""

    def __init__(self):
        self.router = APIRouter(prefix="/api/shops", tags=["shops"])
        self._setup_routes()

    def _setup_routes(self):
        """Настройка маршрутов API."""

        @self.router.post(
            "/add",
            response_model=ShopCreatedResponse,
            summary="Добавить магазин",
            description="Добавляет новый магазин Ozon Seller для пользователя"
        )
        async def add_shop(
            request: ShopCreateRequest = Body(...),
            user_id: int = Header(..., alias="X-Telegram-User-Id")
        ):
            """
            Добавить новый магазин.

            - **name**: Название магазина (для удобства)
            - **client_id**: Ozon Client ID из личного кабинета
            - **api_key**: Ozon API Key из личного кабинета

            Заголовки:
            - **X-Telegram-User-Id**: ID пользователя Telegram
            """
            try:
                logger.info(f"Adding shop for user {user_id}")

                shop = await shop_service.add_shop(
                    user_id=user_id,
                    shop_request=request
                )

                return ShopCreatedResponse(
                    shop=shop,
                    message=f"Магазин '{shop.name}' успешно добавлен"
                )

            except ShopServiceError as e:
                logger.error(f"Error adding shop: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.get(
            "/list",
            response_model=ShopListResponse,
            summary="Список магазинов",
            description="Возвращает все магазины пользователя"
        )
        async def get_shops_list(
            user_id: int = Header(..., alias="X-Telegram-User-Id")
        ):
            """
            Получить список всех магазинов пользователя.

            Заголовки:
            - **X-Telegram-User-Id**: ID пользователя Telegram
            """
            try:
                shops = await shop_service.get_user_shops(user_id)

                return ShopListResponse(
                    shops=shops,
                    total=len(shops)
                )

            except ShopServiceError as e:
                logger.error(f"Error getting shops: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.get(
            "/{shop_id}",
            response_model=ShopResponse,
            summary="Информация о магазине",
            description="Возвращает информацию о конкретном магазине"
        )
        async def get_shop(
            shop_id: int,
            user_id: int = Header(..., alias="X-Telegram-User-Id")
        ):
            """
            Получить информацию о магазине.

            - **shop_id**: ID магазина

            Заголовки:
            - **X-Telegram-User-Id**: ID пользователя Telegram
            """
            try:
                shop = await shop_service.get_shop_by_id(user_id, shop_id)

                return ShopResponse(
                    shop_id=shop.shop_id,
                    name=shop.name,
                    client_id=shop.client_id,
                    is_active=shop.is_active,
                    created_at=shop.created_at,
                    updated_at=shop.updated_at
                )

            except ShopServiceError as e:
                logger.error(f"Error getting shop: {str(e)}")
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.put(
            "/{shop_id}",
            response_model=ShopResponse,
            summary="Обновить магазин",
            description="Обновляет данные магазина"
        )
        async def update_shop(
            shop_id: int,
            request: ShopUpdateRequest = Body(...),
            user_id: int = Header(..., alias="X-Telegram-User-Id")
        ):
            """
            Обновить данные магазина.

            - **shop_id**: ID магазина
            - **name**: Новое название (опционально)
            - **client_id**: Новый Client ID (опционально)
            - **api_key**: Новый API Key (опционально)
            - **is_active**: Статус активности (опционально)

            Заголовки:
            - **X-Telegram-User-Id**: ID пользователя Telegram
            """
            try:
                shop = await shop_service.update_shop(user_id, shop_id, request)
                return shop

            except ShopServiceError as e:
                logger.error(f"Error updating shop: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        @self.router.delete(
            "/{shop_id}",
            summary="Удалить магазин",
            description="Удаляет магазин из системы"
        )
        async def delete_shop(
            shop_id: int,
            user_id: int = Header(..., alias="X-Telegram-User-Id")
        ):
            """
            Удалить магазин.

            - **shop_id**: ID магазина для удаления

            Заголовки:
            - **X-Telegram-User-Id**: ID пользователя Telegram
            """
            try:
                success = await shop_service.delete_shop(user_id, shop_id)

                if success:
                    return {
                        "success": True,
                        "message": f"Магазин {shop_id} успешно удален"
                    }
                else:
                    raise HTTPException(status_code=400, detail="Не удалось удалить магазин")

            except ShopServiceError as e:
                logger.error(f"Error deleting shop: {str(e)}")
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


# Создание экземпляра handlers
shop_handlers = ShopHandlers()
router = shop_handlers.router
