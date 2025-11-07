"""
Сервисный слой для управления магазинами (Ozon Seller аккаунтами).

Предоставляет методы для:
- Добавления магазина с Client ID и API Key
- Получения списка магазинов пользователя
- Удаления магазина
- Обновления данных магазина
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..models.shop import Shop, ShopCreateRequest, ShopUpdateRequest, ShopResponse
from ..utils.encryption import encrypt_api_key, decrypt_api_key
from ..api.ozon_client import OzonAPIClient


logger = logging.getLogger(__name__)


class ShopServiceError(Exception):
    """Исключение для ошибок сервиса магазинов."""
    pass


class ShopService:
    """
    Сервис для управления магазинами пользователей.

    ВАЖНО: Это упрощенная версия с in-memory хранилищем.
    В production версии нужно использовать PostgreSQL для хранения данных.
    """

    def __init__(self):
        """Инициализация сервиса."""
        # In-memory хранилище: {user_id: {shop_id: Shop}}
        self._shops: Dict[int, Dict[int, Shop]] = {}
        self._next_shop_id = 1

    async def add_shop(
        self,
        user_id: int,
        shop_request: ShopCreateRequest
    ) -> ShopResponse:
        """
        Добавить новый магазин для пользователя.

        Args:
            user_id: Telegram User ID
            shop_request: Данные магазина (название, client_id, api_key)

        Returns:
            ShopResponse: Информация о добавленном магазине

        Raises:
            ShopServiceError: При ошибке добавления магазина

        Example:
            >>> service = ShopService()
            >>> shop = await service.add_shop(
            ...     user_id=123456789,
            ...     shop_request=ShopCreateRequest(
            ...         name="Мой магазин",
            ...         client_id="123456",
            ...         api_key="secret-key"
            ...     )
            ... )
        """
        try:
            logger.info(f"Adding shop for user {user_id}: {shop_request.name}")

            # Проверка валидности API ключей
            is_valid = await self._validate_credentials(
                shop_request.client_id,
                shop_request.api_key
            )

            if not is_valid:
                raise ShopServiceError(
                    "Неверный Client ID или API Key. Проверьте данные и попробуйте снова."
                )

            # Шифруем API ключ
            encrypted_key = encrypt_api_key(shop_request.api_key)

            # Создаем объект магазина
            shop_id = self._next_shop_id
            self._next_shop_id += 1

            shop = Shop(
                shop_id=shop_id,
                user_id=user_id,
                name=shop_request.name,
                client_id=shop_request.client_id,
                api_key_encrypted=encrypted_key,
                is_active=True,
                created_at=datetime.now()
            )

            # Сохраняем в хранилище
            if user_id not in self._shops:
                self._shops[user_id] = {}

            self._shops[user_id][shop_id] = shop

            logger.info(f"Shop {shop_id} added successfully for user {user_id}")

            # Возвращаем ответ без API ключа
            return ShopResponse(
                shop_id=shop.shop_id,
                name=shop.name,
                client_id=shop.client_id,
                is_active=shop.is_active,
                created_at=shop.created_at
            )

        except ShopServiceError:
            raise
        except Exception as e:
            logger.error(f"Error adding shop: {str(e)}")
            raise ShopServiceError(f"Не удалось добавить магазин: {str(e)}")

    async def get_user_shops(self, user_id: int) -> List[ShopResponse]:
        """
        Получить список всех магазинов пользователя.

        Args:
            user_id: Telegram User ID

        Returns:
            List[ShopResponse]: Список магазинов

        Example:
            >>> shops = await service.get_user_shops(user_id=123456789)
            >>> for shop in shops:
            ...     print(f"{shop.name}: {shop.client_id}")
        """
        try:
            user_shops = self._shops.get(user_id, {})

            return [
                ShopResponse(
                    shop_id=shop.shop_id,
                    name=shop.name,
                    client_id=shop.client_id,
                    is_active=shop.is_active,
                    created_at=shop.created_at,
                    updated_at=shop.updated_at
                )
                for shop in user_shops.values()
            ]

        except Exception as e:
            logger.error(f"Error getting shops for user {user_id}: {str(e)}")
            raise ShopServiceError(f"Не удалось получить список магазинов: {str(e)}")

    async def get_shop_by_id(self, user_id: int, shop_id: int) -> Shop:
        """
        Получить магазин по ID (с расшифрованным API ключом).

        Args:
            user_id: Telegram User ID
            shop_id: ID магазина

        Returns:
            Shop: Объект магазина с расшифрованным API ключом

        Raises:
            ShopServiceError: Если магазин не найден
        """
        try:
            user_shops = self._shops.get(user_id, {})

            if shop_id not in user_shops:
                raise ShopServiceError(f"Магазин с ID {shop_id} не найден")

            return user_shops[shop_id]

        except ShopServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting shop {shop_id}: {str(e)}")
            raise ShopServiceError(f"Не удалось получить магазин: {str(e)}")

    async def delete_shop(self, user_id: int, shop_id: int) -> bool:
        """
        Удалить магазин.

        Args:
            user_id: Telegram User ID
            shop_id: ID магазина для удаления

        Returns:
            bool: True если магазин успешно удален

        Raises:
            ShopServiceError: Если магазин не найден

        Example:
            >>> success = await service.delete_shop(user_id=123456789, shop_id=1)
            >>> if success:
            ...     print("Магазин удален")
        """
        try:
            logger.info(f"Deleting shop {shop_id} for user {user_id}")

            user_shops = self._shops.get(user_id, {})

            if shop_id not in user_shops:
                raise ShopServiceError(f"Магазин с ID {shop_id} не найден")

            # Удаляем магазин
            del user_shops[shop_id]

            logger.info(f"Shop {shop_id} deleted successfully")
            return True

        except ShopServiceError:
            raise
        except Exception as e:
            logger.error(f"Error deleting shop {shop_id}: {str(e)}")
            raise ShopServiceError(f"Не удалось удалить магазин: {str(e)}")

    async def update_shop(
        self,
        user_id: int,
        shop_id: int,
        update_request: ShopUpdateRequest
    ) -> ShopResponse:
        """
        Обновить данные магазина.

        Args:
            user_id: Telegram User ID
            shop_id: ID магазина
            update_request: Новые данные магазина

        Returns:
            ShopResponse: Обновленная информация о магазине

        Raises:
            ShopServiceError: При ошибке обновления
        """
        try:
            logger.info(f"Updating shop {shop_id} for user {user_id}")

            shop = await self.get_shop_by_id(user_id, shop_id)

            # Обновляем поля
            if update_request.name is not None:
                shop.name = update_request.name

            if update_request.client_id is not None:
                shop.client_id = update_request.client_id

            if update_request.api_key is not None:
                # Проверяем новые credentials
                is_valid = await self._validate_credentials(
                    shop.client_id,
                    update_request.api_key
                )

                if not is_valid:
                    raise ShopServiceError("Неверный API Key")

                shop.api_key_encrypted = encrypt_api_key(update_request.api_key)

            if update_request.is_active is not None:
                shop.is_active = update_request.is_active

            shop.updated_at = datetime.now()

            logger.info(f"Shop {shop_id} updated successfully")

            return ShopResponse(
                shop_id=shop.shop_id,
                name=shop.name,
                client_id=shop.client_id,
                is_active=shop.is_active,
                created_at=shop.created_at,
                updated_at=shop.updated_at
            )

        except ShopServiceError:
            raise
        except Exception as e:
            logger.error(f"Error updating shop {shop_id}: {str(e)}")
            raise ShopServiceError(f"Не удалось обновить магазин: {str(e)}")

    async def get_shop_credentials(
        self,
        user_id: int,
        shop_id: int
    ) -> tuple[str, str]:
        """
        Получить расшифрованные credentials магазина.

        Args:
            user_id: Telegram User ID
            shop_id: ID магазина

        Returns:
            tuple[str, str]: (client_id, api_key)

        Example:
            >>> client_id, api_key = await service.get_shop_credentials(123456789, 1)
        """
        try:
            shop = await self.get_shop_by_id(user_id, shop_id)

            if not shop.is_active:
                raise ShopServiceError("Магазин неактивен")

            # Расшифровываем API ключ
            api_key = decrypt_api_key(shop.api_key_encrypted)

            return shop.client_id, api_key

        except ShopServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting credentials for shop {shop_id}: {str(e)}")
            raise ShopServiceError(f"Не удалось получить данные магазина: {str(e)}")

    async def _validate_credentials(
        self,
        client_id: str,
        api_key: str
    ) -> bool:
        """
        Проверить валидность API ключей через запрос к Ozon API.

        Args:
            client_id: Ozon Client ID
            api_key: Ozon API Key

        Returns:
            bool: True если credentials валидны
        """
        try:
            # Пытаемся получить список складов как проверку валидности
            async with OzonAPIClient(client_id=client_id, api_key=api_key) as client:
                await client.get_warehouses()
                return True

        except Exception as e:
            logger.warning(f"Credentials validation failed: {str(e)}")
            return False


# Глобальный экземпляр сервиса
# В production версии использовать dependency injection
shop_service = ShopService()
