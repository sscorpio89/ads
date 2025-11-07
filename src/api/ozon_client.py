"""
Клиент для работы с Ozon Seller API.

Основные методы:
- get_timeslots: получение доступных временных слотов
- create_draft: создание черновика заявки на поставку
- create_supply: создание заявки на поставку из черновика
- update_supply: обновление заявки на поставку
- cancel_supply: отмена заявки на поставку
- get_supply_list: получение списка заявок
- get_supply_by_id: получение информации о конкретной заявке
- create_cargoes: создание/обновление грузомест
- get_warehouses: получение списка доступных складов

API Documentation: https://docs.ozon.ru/api/seller/
"""

import logging
from typing import Dict, List, Optional
import aiohttp
from aiohttp import ClientSession, ClientTimeout

from ..models.supply import (
    TimeslotInfo,
    Timeslot,
    TimeslotPeriod,
    SupplyDraft,
    SupplyDraftRequest,
    SupplyRequest,
    SupplyUpdateRequest,
    SupplyCancelRequest,
    CargoRequest,
    DeliveryType,
    SupplyStatus,
    Warehouse,
)


logger = logging.getLogger(__name__)


class OzonAPIError(Exception):
    """Базовое исключение для ошибок Ozon API."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class OzonAPIClient:
    """
    Асинхронный клиент для работы с Ozon Seller API.

    Пример использования:
        client = OzonAPIClient(client_id="your_client_id", api_key="your_api_key")
        timeslots = await client.get_timeslots(warehouse_id=12345)
    """

    BASE_URL = "https://api-seller.ozon.ru"

    # API endpoints
    ENDPOINTS = {
        "timeslots": "/v1/draft/timeslot/info",
        "draft_create": "/v1/draft/create",
        "supply_create": "/v1/draft/supply/create",
        "supply_list": "/v1/supply/list",
        "supply_info": "/v1/supply/info",
        "supply_cancel": "/v1/supply/cancel",
        "cargoes_create": "/v1/cargoes/create",
        "cargoes_rules": "/v1/cargoes/rules/get",
        "warehouses": "/v1/warehouse/list",
    }

    def __init__(
        self,
        client_id: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Инициализация клиента Ozon API.

        Args:
            client_id: Client ID из личного кабинета Ozon Seller
            api_key: API ключ из личного кабинета Ozon Seller
            timeout: Таймаут запросов в секундах
            max_retries: Максимальное количество повторных попыток
        """
        self.client_id = client_id
        self.api_key = api_key
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        """Контекстный менеджер для автоматического управления сессией."""
        self.session = ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекста."""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Формирование заголовков для запросов к API."""
        return {
            "Client-Id": self.client_id,
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None
    ) -> dict:
        """
        Выполнение HTTP запроса к Ozon API с обработкой ошибок и retry логикой.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Тело запроса (JSON)
            params: Query параметры

        Returns:
            dict: Ответ от API

        Raises:
            OzonAPIError: При ошибке API
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        if not self.session:
            self.session = ClientSession(timeout=self.timeout)

        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        logger.debug(f"API request successful: {method} {endpoint}")
                        return response_data
                    else:
                        error_message = response_data.get("message", "Unknown error")
                        logger.error(
                            f"API error: {method} {endpoint} - "
                            f"Status: {response.status}, Message: {error_message}"
                        )
                        raise OzonAPIError(
                            message=error_message,
                            status_code=response.status,
                            response_data=response_data
                        )

            except aiohttp.ClientError as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise OzonAPIError(f"Failed after {self.max_retries} attempts: {str(e)}")
                continue

    # ========================================================================
    # Timeslots Methods (получение доступных временных слотов)
    # ========================================================================

    async def get_timeslots(
        self,
        warehouse_id: int,
        delivery_type: DeliveryType = DeliveryType.FBO
    ) -> TimeslotInfo:
        """
        Получить информацию о доступных временных слотах для склада.

        Args:
            warehouse_id: ID склада
            delivery_type: Тип доставки (fbo или crossborder)

        Returns:
            TimeslotInfo: Информация о доступных слотах

        Example:
            >>> timeslots = await client.get_timeslots(warehouse_id=12345)
            >>> for slot in timeslots.timeslots:
            ...     print(f"Date: {slot.date}, Period: {slot.period.from_time}-{slot.period.to_time}")
        """
        payload = {
            "warehouse_id": warehouse_id,
            "delivery_type": delivery_type.value
        }

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["timeslots"],
            data=payload
        )

        result = response.get("result", {})
        timeslots_data = result.get("timeslots", [])

        # Парсинг временных слотов
        timeslots = []
        for slot_data in timeslots_data:
            period = TimeslotPeriod(
                from_time=slot_data.get("from", ""),
                to_time=slot_data.get("to", "")
            )
            slot = Timeslot(
                date=slot_data.get("date", ""),
                period=period,
                limit=slot_data.get("limit", 0),
                available=slot_data.get("available", False)
            )
            timeslots.append(slot)

        return TimeslotInfo(
            warehouse_id=warehouse_id,
            delivery_type=delivery_type,
            timeslots=timeslots
        )

    # ========================================================================
    # Draft Methods (создание черновиков заявок)
    # ========================================================================

    async def create_draft(self, draft_request: SupplyDraftRequest) -> SupplyDraft:
        """
        Создать черновик заявки на поставку.

        Args:
            draft_request: Данные для создания черновика

        Returns:
            SupplyDraft: Созданный черновик

        Example:
            >>> draft_req = SupplyDraftRequest(
            ...     supply_date="2025-11-15",
            ...     timeslot_from="10:00",
            ...     timeslot_to="14:00",
            ...     warehouse_id=12345
            ... )
            >>> draft = await client.create_draft(draft_req)
            >>> print(f"Draft ID: {draft.draft_id}")
        """
        payload = {
            "supply_date": draft_request.supply_date,
            "timeslot": {
                "from": draft_request.timeslot_from,
                "to": draft_request.timeslot_to
            },
            "warehouse_id": draft_request.warehouse_id,
            "delivery_type": draft_request.delivery_type.value
        }

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["draft_create"],
            data=payload
        )

        result = response.get("result", {})
        return SupplyDraft(
            draft_id=result.get("draft_id", ""),
            supply_date=draft_request.supply_date,
            warehouse_id=draft_request.warehouse_id,
            delivery_type=draft_request.delivery_type
        )

    # ========================================================================
    # Supply Methods (управление заявками на поставку)
    # ========================================================================

    async def create_supply(self, draft_id: str) -> SupplyRequest:
        """
        Создать заявку на поставку из черновика.

        Args:
            draft_id: ID черновика

        Returns:
            SupplyRequest: Созданная заявка

        Example:
            >>> supply = await client.create_supply(draft_id="12345678-abcd-1234-abcd-123456789012")
            >>> print(f"Supply ID: {supply.supply_id}")
        """
        payload = {"draft_id": draft_id}

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["supply_create"],
            data=payload
        )

        result = response.get("result", {})
        return self._parse_supply_response(result)

    async def get_supply_list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[SupplyStatus] = None
    ) -> List[SupplyRequest]:
        """
        Получить список заявок на поставку.

        Args:
            limit: Максимальное количество заявок в ответе
            offset: Смещение для пагинации
            status: Фильтр по статусу заявок

        Returns:
            List[SupplyRequest]: Список заявок

        Example:
            >>> supplies = await client.get_supply_list(limit=50, status=SupplyStatus.CONFIRMED)
            >>> for supply in supplies:
            ...     print(f"Supply {supply.supply_id}: {supply.status}")
        """
        payload = {
            "limit": limit,
            "offset": offset
        }

        if status:
            payload["filter"] = {"status": status.value}

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["supply_list"],
            data=payload
        )

        result = response.get("result", {})
        supplies = result.get("supplies", [])

        return [self._parse_supply_response(supply_data) for supply_data in supplies]

    async def get_supply_by_id(self, supply_id: str) -> SupplyRequest:
        """
        Получить информацию о конкретной заявке на поставку.

        Args:
            supply_id: ID заявки

        Returns:
            SupplyRequest: Информация о заявке

        Example:
            >>> supply = await client.get_supply_by_id(supply_id="SUP123456")
            >>> print(f"Status: {supply.status}, Date: {supply.supply_date}")
        """
        payload = {"supply_id": supply_id}

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["supply_info"],
            data=payload
        )

        result = response.get("result", {})
        return self._parse_supply_response(result)

    async def cancel_supply(self, cancel_request: SupplyCancelRequest) -> bool:
        """
        Отменить заявку на поставку.

        Args:
            cancel_request: Данные для отмены заявки

        Returns:
            bool: True если заявка успешно отменена

        Example:
            >>> cancel_req = SupplyCancelRequest(
            ...     supply_id="SUP123456",
            ...     reason="Изменились планы поставки"
            ... )
            >>> success = await client.cancel_supply(cancel_req)
            >>> print(f"Cancelled: {success}")
        """
        payload = {"supply_id": cancel_request.supply_id}

        if cancel_request.reason:
            payload["reason"] = cancel_request.reason

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["supply_cancel"],
            data=payload
        )

        return response.get("result", {}).get("success", False)

    # ========================================================================
    # Cargo Methods (управление грузоместами)
    # ========================================================================

    async def create_cargoes(self, cargo_request: CargoRequest) -> Dict[str, any]:
        """
        Создать или обновить грузоместа для заявки на поставку.

        Args:
            cargo_request: Данные о грузоместах

        Returns:
            dict: Результат создания грузомест

        Example:
            >>> cargo_req = CargoRequest(
            ...     draft_id="12345678-abcd-1234-abcd-123456789012",
            ...     cargoes=[
            ...         CargoItem(
            ...             cargo_id="CARGO001",
            ...             cargo_type=CargoType.BOX,
            ...             products=[ProductInCargo(product_id=123456, quantity=10)],
            ...             weight=15.5
            ...         )
            ...     ],
            ...     delete_current_version=False
            ... )
            >>> result = await client.create_cargoes(cargo_req)
        """
        # Формируем payload для API
        cargoes_data = []
        for cargo in cargo_request.cargoes:
            cargo_dict = {
                "cargo_id": cargo.cargo_id,
                "cargo_type": cargo.cargo_type.value,
                "products": [
                    {"sku": product.product_id, "quantity": product.quantity}
                    for product in cargo.products
                ]
            }

            # Добавляем габариты если указаны
            if cargo.weight:
                cargo_dict["weight"] = cargo.weight
            if cargo.width and cargo.height and cargo.depth:
                cargo_dict["dimensions"] = {
                    "width": cargo.width,
                    "height": cargo.height,
                    "depth": cargo.depth
                }

            cargoes_data.append(cargo_dict)

        payload = {
            "draft_id": cargo_request.draft_id,
            "cargoes": cargoes_data,
            "delete_current_version": cargo_request.delete_current_version
        }

        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["cargoes_create"],
            data=payload
        )

        return response.get("result", {})

    # ========================================================================
    # Warehouse Methods (получение информации о складах)
    # ========================================================================

    async def get_warehouses(self) -> List[Warehouse]:
        """
        Получить список доступных складов.

        Returns:
            List[Warehouse]: Список складов

        Example:
            >>> warehouses = await client.get_warehouses()
            >>> for warehouse in warehouses:
            ...     print(f"{warehouse.name} (ID: {warehouse.warehouse_id})")
        """
        response = await self._make_request(
            method="POST",
            endpoint=self.ENDPOINTS["warehouses"],
            data={}
        )

        result = response.get("result", {})
        warehouses_data = result.get("warehouses", [])

        warehouses = []
        for wh_data in warehouses_data:
            warehouse = Warehouse(
                warehouse_id=wh_data.get("warehouse_id", 0),
                name=wh_data.get("name", ""),
                address=wh_data.get("address"),
                city=wh_data.get("city"),
                is_active=wh_data.get("is_active", True)
            )
            warehouses.append(warehouse)

        return warehouses

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _parse_supply_response(self, data: dict) -> SupplyRequest:
        """Парсинг данных заявки на поставку из ответа API."""
        return SupplyRequest(
            supply_id=data.get("supply_id", ""),
            draft_id=data.get("draft_id"),
            supply_number=data.get("supply_number"),
            supply_date=data.get("supply_date", ""),
            warehouse_id=data.get("warehouse_id", 0),
            warehouse_name=data.get("warehouse_name"),
            status=SupplyStatus(data.get("status", "draft")),
            timeslot_from=data.get("timeslot", {}).get("from", ""),
            timeslot_to=data.get("timeslot", {}).get("to", ""),
            total_items=data.get("total_items", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at")
        )

    async def close(self):
        """Закрыть сессию клиента."""
        if self.session:
            await self.session.close()
            self.session = None
