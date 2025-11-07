"""
Сервисный слой для управления заявками на поставку FBO.

Предоставляет высокоуровневые методы для:
- Создания заявок на поставку
- Редактирования заявок
- Удаления (отмены) заявок
- Получения списка заявок
- Работы с грузоместами
"""

import logging
from typing import List, Optional
from datetime import datetime

from ..api.ozon_client import OzonAPIClient, OzonAPIError
from ..models.supply import (
    TimeslotInfo,
    SupplyDraft,
    SupplyDraftRequest,
    SupplyRequest,
    SupplyUpdateRequest,
    SupplyCancelRequest,
    CargoRequest,
    CargoItem,
    DeliveryType,
    SupplyStatus,
    Warehouse,
)


logger = logging.getLogger(__name__)


class SupplyServiceError(Exception):
    """Исключение для ошибок сервиса заявок на поставку."""
    pass


class SupplyService:
    """
    Сервис для управления заявками на поставку FBO через Telegram Mini App.

    Основной функционал:
    1. Создание заявок на поставку (с автоматическим созданием черновика)
    2. Редактирование существующих заявок
    3. Отмена/удаление заявок
    4. Получение списка заявок с фильтрацией
    5. Управление грузоместами
    """

    def __init__(self, ozon_client: OzonAPIClient):
        """
        Инициализация сервиса.

        Args:
            ozon_client: Инициализированный клиент Ozon API
        """
        self.ozon_client = ozon_client

    # ========================================================================
    # Создание заявок на поставку
    # ========================================================================

    async def create_supply_request(
        self,
        warehouse_id: int,
        supply_date: str,
        timeslot_from: str,
        timeslot_to: str,
        delivery_type: DeliveryType = DeliveryType.FBO,
        cargoes: Optional[List[CargoItem]] = None
    ) -> SupplyRequest:
        """
        Создать полную заявку на поставку.

        Этот метод автоматически:
        1. Создает черновик заявки
        2. Добавляет грузоместа (если указаны)
        3. Формирует итоговую заявку на поставку

        Args:
            warehouse_id: ID склада
            supply_date: Дата поставки (YYYY-MM-DD)
            timeslot_from: Начало временного слота (HH:MM)
            timeslot_to: Конец временного слота (HH:MM)
            delivery_type: Тип доставки (по умолчанию FBO)
            cargoes: Список грузомест (опционально)

        Returns:
            SupplyRequest: Созданная заявка на поставку

        Raises:
            SupplyServiceError: При ошибке создания заявки

        Example:
            >>> service = SupplyService(ozon_client)
            >>> supply = await service.create_supply_request(
            ...     warehouse_id=12345,
            ...     supply_date="2025-11-15",
            ...     timeslot_from="10:00",
            ...     timeslot_to="14:00",
            ...     cargoes=[cargo_item1, cargo_item2]
            ... )
            >>> print(f"Created supply: {supply.supply_id}")
        """
        try:
            logger.info(f"Creating supply request for warehouse {warehouse_id} on {supply_date}")

            # Шаг 1: Создаем черновик заявки
            draft_request = SupplyDraftRequest(
                supply_date=supply_date,
                timeslot_from=timeslot_from,
                timeslot_to=timeslot_to,
                warehouse_id=warehouse_id,
                delivery_type=delivery_type
            )

            draft = await self.ozon_client.create_draft(draft_request)
            logger.info(f"Draft created: {draft.draft_id}")

            # Шаг 2: Добавляем грузоместа, если указаны
            if cargoes:
                cargo_request = CargoRequest(
                    draft_id=draft.draft_id,
                    cargoes=cargoes,
                    delete_current_version=False
                )
                await self.ozon_client.create_cargoes(cargo_request)
                logger.info(f"Added {len(cargoes)} cargoes to draft {draft.draft_id}")

            # Шаг 3: Создаем финальную заявку из черновика
            supply = await self.ozon_client.create_supply(draft.draft_id)
            logger.info(f"Supply created: {supply.supply_id}")

            return supply

        except OzonAPIError as e:
            logger.error(f"Ozon API error while creating supply: {e.message}")
            raise SupplyServiceError(f"Не удалось создать заявку на поставку: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error while creating supply: {str(e)}")
            raise SupplyServiceError(f"Произошла ошибка при создании заявки: {str(e)}")

    async def get_available_timeslots(
        self,
        warehouse_id: int,
        delivery_type: DeliveryType = DeliveryType.FBO
    ) -> TimeslotInfo:
        """
        Получить доступные временные слоты для склада.

        Args:
            warehouse_id: ID склада
            delivery_type: Тип доставки

        Returns:
            TimeslotInfo: Информация о доступных слотах

        Example:
            >>> timeslots = await service.get_available_timeslots(warehouse_id=12345)
            >>> available_slots = [slot for slot in timeslots.timeslots if slot.available]
            >>> print(f"Found {len(available_slots)} available slots")
        """
        try:
            return await self.ozon_client.get_timeslots(warehouse_id, delivery_type)
        except OzonAPIError as e:
            logger.error(f"Error fetching timeslots: {e.message}")
            raise SupplyServiceError(f"Не удалось получить слоты: {e.message}")

    # ========================================================================
    # Редактирование заявок на поставку
    # ========================================================================

    async def update_supply_request(
        self,
        supply_id: str,
        new_supply_date: Optional[str] = None,
        new_timeslot_from: Optional[str] = None,
        new_timeslot_to: Optional[str] = None
    ) -> SupplyRequest:
        """
        Обновить существующую заявку на поставку (ребукинг).

        ВАЖНО: Ozon API не всегда позволяет прямое редактирование заявок.
        В некоторых случаях требуется отменить старую заявку и создать новую.

        Args:
            supply_id: ID заявки на обновление
            new_supply_date: Новая дата поставки
            new_timeslot_from: Новое начало слота
            new_timeslot_to: Новый конец слота

        Returns:
            SupplyRequest: Обновленная заявка

        Raises:
            SupplyServiceError: При ошибке обновления

        Example:
            >>> updated_supply = await service.update_supply_request(
            ...     supply_id="SUP123456",
            ...     new_supply_date="2025-11-16",
            ...     new_timeslot_from="14:00",
            ...     new_timeslot_to="18:00"
            ... )
        """
        try:
            logger.info(f"Updating supply request: {supply_id}")

            # Получаем текущую заявку
            current_supply = await self.ozon_client.get_supply_by_id(supply_id)

            # Проверяем, можно ли редактировать заявку
            if current_supply.status not in [SupplyStatus.DRAFT, SupplyStatus.CONFIRMED]:
                raise SupplyServiceError(
                    f"Невозможно редактировать заявку со статусом '{current_supply.status.value}'"
                )

            # В Ozon API обычно нужно создать новую заявку вместо редактирования
            # Поэтому мы отменяем старую и создаем новую с измененными параметрами
            await self.cancel_supply_request(
                supply_id=supply_id,
                reason="Изменение параметров поставки"
            )

            # Создаем новую заявку с обновленными параметрами
            new_supply = await self.create_supply_request(
                warehouse_id=current_supply.warehouse_id,
                supply_date=new_supply_date or current_supply.supply_date,
                timeslot_from=new_timeslot_from or current_supply.timeslot_from,
                timeslot_to=new_timeslot_to or current_supply.timeslot_to,
                delivery_type=DeliveryType.FBO
            )

            logger.info(f"Supply rebooked: old {supply_id} -> new {new_supply.supply_id}")
            return new_supply

        except OzonAPIError as e:
            logger.error(f"Error updating supply: {e.message}")
            raise SupplyServiceError(f"Не удалось обновить заявку: {e.message}")

    # ========================================================================
    # Удаление (отмена) заявок на поставку
    # ========================================================================

    async def cancel_supply_request(
        self,
        supply_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Отменить (удалить) заявку на поставку.

        Args:
            supply_id: ID заявки для отмены
            reason: Причина отмены (опционально)

        Returns:
            bool: True если заявка успешно отменена

        Raises:
            SupplyServiceError: При ошибке отмены

        Example:
            >>> success = await service.cancel_supply_request(
            ...     supply_id="SUP123456",
            ...     reason="Изменение планов"
            ... )
            >>> if success:
            ...     print("Заявка успешно отменена")
        """
        try:
            logger.info(f"Cancelling supply request: {supply_id}")

            cancel_request = SupplyCancelRequest(
                supply_id=supply_id,
                reason=reason or "Отмена через Telegram Mini App"
            )

            success = await self.ozon_client.cancel_supply(cancel_request)

            if success:
                logger.info(f"Supply {supply_id} cancelled successfully")
            else:
                logger.warning(f"Supply {supply_id} cancellation returned False")

            return success

        except OzonAPIError as e:
            logger.error(f"Error cancelling supply: {e.message}")
            raise SupplyServiceError(f"Не удалось отменить заявку: {e.message}")

    async def delete_supply_request(self, supply_id: str) -> bool:
        """
        Удалить заявку на поставку (алиас для cancel_supply_request).

        Args:
            supply_id: ID заявки

        Returns:
            bool: True если успешно удалена

        Example:
            >>> await service.delete_supply_request(supply_id="SUP123456")
        """
        return await self.cancel_supply_request(
            supply_id=supply_id,
            reason="Удаление заявки"
        )

    # ========================================================================
    # Получение списка заявок
    # ========================================================================

    async def get_supply_requests(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[SupplyStatus] = None
    ) -> List[SupplyRequest]:
        """
        Получить список заявок на поставку с фильтрацией.

        Args:
            limit: Максимальное количество заявок
            offset: Смещение для пагинации
            status: Фильтр по статусу

        Returns:
            List[SupplyRequest]: Список заявок

        Example:
            >>> # Получить все активные заявки
            >>> active_supplies = await service.get_supply_requests(
            ...     status=SupplyStatus.CONFIRMED
            ... )
            >>> for supply in active_supplies:
            ...     print(f"{supply.supply_id}: {supply.supply_date}")
        """
        try:
            return await self.ozon_client.get_supply_list(
                limit=limit,
                offset=offset,
                status=status
            )
        except OzonAPIError as e:
            logger.error(f"Error fetching supply list: {e.message}")
            raise SupplyServiceError(f"Не удалось получить список заявок: {e.message}")

    async def get_supply_by_id(self, supply_id: str) -> SupplyRequest:
        """
        Получить информацию о конкретной заявке.

        Args:
            supply_id: ID заявки

        Returns:
            SupplyRequest: Информация о заявке

        Example:
            >>> supply = await service.get_supply_by_id("SUP123456")
            >>> print(f"Status: {supply.status}, Warehouse: {supply.warehouse_name}")
        """
        try:
            return await self.ozon_client.get_supply_by_id(supply_id)
        except OzonAPIError as e:
            logger.error(f"Error fetching supply {supply_id}: {e.message}")
            raise SupplyServiceError(f"Не удалось получить заявку: {e.message}")

    # ========================================================================
    # Управление грузоместами
    # ========================================================================

    async def add_cargoes_to_draft(
        self,
        draft_id: str,
        cargoes: List[CargoItem],
        replace_existing: bool = False
    ) -> bool:
        """
        Добавить грузоместа к черновику заявки.

        Args:
            draft_id: ID черновика
            cargoes: Список грузомест
            replace_existing: Заменить существующие грузоместа

        Returns:
            bool: True если успешно добавлены

        Example:
            >>> cargoes = [
            ...     CargoItem(cargo_id="CARGO001", cargo_type=CargoType.BOX, products=[...])
            ... ]
            >>> await service.add_cargoes_to_draft(draft_id="...", cargoes=cargoes)
        """
        try:
            cargo_request = CargoRequest(
                draft_id=draft_id,
                cargoes=cargoes,
                delete_current_version=replace_existing
            )

            result = await self.ozon_client.create_cargoes(cargo_request)
            return result.get("success", False)

        except OzonAPIError as e:
            logger.error(f"Error adding cargoes: {e.message}")
            raise SupplyServiceError(f"Не удалось добавить грузоместа: {e.message}")

    # ========================================================================
    # Вспомогательные методы
    # ========================================================================

    async def get_warehouses(self) -> List[Warehouse]:
        """
        Получить список доступных складов.

        Returns:
            List[Warehouse]: Список складов

        Example:
            >>> warehouses = await service.get_warehouses()
            >>> for wh in warehouses:
            ...     print(f"{wh.name} ({wh.city})")
        """
        try:
            return await self.ozon_client.get_warehouses()
        except OzonAPIError as e:
            logger.error(f"Error fetching warehouses: {e.message}")
            raise SupplyServiceError(f"Не удалось получить список складов: {e.message}")

    async def validate_timeslot(
        self,
        warehouse_id: int,
        supply_date: str,
        timeslot_from: str,
        timeslot_to: str
    ) -> bool:
        """
        Проверить доступность временного слота.

        Args:
            warehouse_id: ID склада
            supply_date: Дата поставки
            timeslot_from: Начало слота
            timeslot_to: Конец слота

        Returns:
            bool: True если слот доступен

        Example:
            >>> is_available = await service.validate_timeslot(
            ...     warehouse_id=12345,
            ...     supply_date="2025-11-15",
            ...     timeslot_from="10:00",
            ...     timeslot_to="14:00"
            ... )
        """
        try:
            timeslots = await self.get_available_timeslots(warehouse_id)

            for slot in timeslots.timeslots:
                if (slot.date == supply_date and
                    slot.period.from_time == timeslot_from and
                    slot.period.to_time == timeslot_to and
                    slot.available):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error validating timeslot: {str(e)}")
            return False
