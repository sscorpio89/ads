"""
Примеры использования Ozon FBO Supply Bot API.

Демонстрирует основные сценарии работы с заявками на поставку.
"""

import asyncio
from datetime import datetime, timedelta

from src.api.ozon_client import OzonAPIClient
from src.services.supply_service import SupplyService
from src.models.supply import (
    CargoItem,
    ProductInCargo,
    CargoType,
    SupplyStatus,
    DeliveryType,
)


# ============================================================================
# Пример 1: Создание простой заявки на поставку
# ============================================================================

async def example_create_simple_supply():
    """Создать простую заявку на поставку без грузомест."""
    print("=" * 60)
    print("Пример 1: Создание простой заявки на поставку")
    print("=" * 60)

    # Инициализация клиента (замените на реальные данные)
    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            # Создаем заявку
            supply = await service.create_supply_request(
                warehouse_id=12345,
                supply_date="2025-11-15",
                timeslot_from="10:00",
                timeslot_to="14:00"
            )

            print(f"✅ Заявка создана успешно!")
            print(f"   ID: {supply.supply_id}")
            print(f"   Дата: {supply.supply_date}")
            print(f"   Склад: {supply.warehouse_id}")
            print(f"   Статус: {supply.status.value}")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 2: Создание заявки с грузоместами
# ============================================================================

async def example_create_supply_with_cargoes():
    """Создать заявку на поставку с указанием грузомест."""
    print("\n" + "=" * 60)
    print("Пример 2: Создание заявки с грузоместами")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        # Подготовка грузомест
        cargoes = [
            CargoItem(
                cargo_id="CARGO001",
                cargo_type=CargoType.BOX,
                products=[
                    ProductInCargo(product_id=123456, quantity=10),
                    ProductInCargo(product_id=789012, quantity=5),
                ],
                weight=15.5,
                width=40,
                height=30,
                depth=50
            ),
            CargoItem(
                cargo_id="CARGO002",
                cargo_type=CargoType.BOX,
                products=[
                    ProductInCargo(product_id=345678, quantity=20),
                ],
                weight=12.0,
                width=35,
                height=25,
                depth=45
            ),
        ]

        try:
            supply = await service.create_supply_request(
                warehouse_id=12345,
                supply_date="2025-11-15",
                timeslot_from="14:00",
                timeslot_to="18:00",
                cargoes=cargoes
            )

            print(f"✅ Заявка с грузоместами создана!")
            print(f"   ID: {supply.supply_id}")
            print(f"   Количество товаров: {supply.total_items}")
            print(f"   Количество грузомест: {len(cargoes)}")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 3: Получение списка заявок
# ============================================================================

async def example_get_supplies_list():
    """Получить список всех заявок на поставку."""
    print("\n" + "=" * 60)
    print("Пример 3: Получение списка заявок")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            # Получаем все заявки
            supplies = await service.get_supply_requests(limit=10)

            print(f"✅ Найдено заявок: {len(supplies)}\n")

            for supply in supplies:
                print(f"ID: {supply.supply_id}")
                print(f"  Дата: {supply.supply_date}")
                print(f"  Статус: {supply.status.value}")
                print(f"  Склад: {supply.warehouse_name or supply.warehouse_id}")
                print(f"  Слот: {supply.timeslot_from} - {supply.timeslot_to}")
                print()

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 4: Получение заявок по статусу
# ============================================================================

async def example_get_supplies_by_status():
    """Получить заявки с фильтрацией по статусу."""
    print("\n" + "=" * 60)
    print("Пример 4: Фильтрация заявок по статусу")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            # Получаем только подтвержденные заявки
            confirmed = await service.get_supply_requests(
                status=SupplyStatus.CONFIRMED
            )

            print(f"✅ Подтвержденных заявок: {len(confirmed)}")

            # Получаем черновики
            drafts = await service.get_supply_requests(
                status=SupplyStatus.DRAFT
            )

            print(f"✅ Черновиков: {len(drafts)}")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 5: Проверка доступных слотов
# ============================================================================

async def example_check_available_timeslots():
    """Проверить доступные временные слоты для склада."""
    print("\n" + "=" * 60)
    print("Пример 5: Проверка доступных слотов")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            # Получаем доступные слоты
            timeslots = await service.get_available_timeslots(warehouse_id=12345)

            print(f"✅ Склад: {timeslots.warehouse_id}")
            print(f"   Тип доставки: {timeslots.delivery_type.value}\n")

            available_count = 0
            for slot in timeslots.timeslots:
                if slot.available:
                    available_count += 1
                    print(f"📅 {slot.date}")
                    print(f"   Время: {slot.period.from_time} - {slot.period.to_time}")
                    print(f"   Лимит: {slot.limit}")
                    print()

            print(f"Всего доступно слотов: {available_count}")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 6: Редактирование заявки (ребукинг)
# ============================================================================

async def example_update_supply():
    """Изменить параметры существующей заявки."""
    print("\n" + "=" * 60)
    print("Пример 6: Редактирование заявки (ребукинг)")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            # Получаем существующую заявку
            supply_id = "SUP123456"  # Замените на реальный ID

            print(f"Обновляем заявку {supply_id}...")

            # Изменяем дату и время
            updated_supply = await service.update_supply_request(
                supply_id=supply_id,
                new_supply_date="2025-11-16",
                new_timeslot_from="14:00",
                new_timeslot_to="18:00"
            )

            print(f"✅ Заявка обновлена!")
            print(f"   Новый ID: {updated_supply.supply_id}")
            print(f"   Новая дата: {updated_supply.supply_date}")
            print(f"   Новый слот: {updated_supply.timeslot_from} - {updated_supply.timeslot_to}")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 7: Отмена заявки
# ============================================================================

async def example_cancel_supply():
    """Отменить заявку на поставку."""
    print("\n" + "=" * 60)
    print("Пример 7: Отмена заявки")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            supply_id = "SUP123456"  # Замените на реальный ID

            print(f"Отменяем заявку {supply_id}...")

            success = await service.delete_supply_request(supply_id)

            if success:
                print(f"✅ Заявка {supply_id} успешно отменена")
            else:
                print(f"⚠️  Не удалось отменить заявку")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 8: Получение информации о складах
# ============================================================================

async def example_get_warehouses():
    """Получить список доступных складов."""
    print("\n" + "=" * 60)
    print("Пример 8: Список доступных складов")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        try:
            warehouses = await service.get_warehouses()

            print(f"✅ Найдено складов: {len(warehouses)}\n")

            for wh in warehouses:
                if wh.is_active:
                    print(f"🏢 {wh.name}")
                    print(f"   ID: {wh.warehouse_id}")
                    print(f"   Город: {wh.city or 'Не указан'}")
                    print(f"   Адрес: {wh.address or 'Не указан'}")
                    print()

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Пример 9: Валидация слота перед созданием заявки
# ============================================================================

async def example_validate_and_create():
    """Проверить доступность слота перед созданием заявки."""
    print("\n" + "=" * 60)
    print("Пример 9: Валидация слота перед созданием")
    print("=" * 60)

    async with OzonAPIClient(
        client_id="your_client_id",
        api_key="your_api_key"
    ) as client:
        service = SupplyService(client)

        warehouse_id = 12345
        supply_date = "2025-11-15"
        timeslot_from = "10:00"
        timeslot_to = "14:00"

        try:
            # Проверяем доступность слота
            print("Проверка доступности слота...")

            is_available = await service.validate_timeslot(
                warehouse_id=warehouse_id,
                supply_date=supply_date,
                timeslot_from=timeslot_from,
                timeslot_to=timeslot_to
            )

            if is_available:
                print("✅ Слот доступен! Создаем заявку...")

                supply = await service.create_supply_request(
                    warehouse_id=warehouse_id,
                    supply_date=supply_date,
                    timeslot_from=timeslot_from,
                    timeslot_to=timeslot_to
                )

                print(f"✅ Заявка создана: {supply.supply_id}")
            else:
                print("⚠️  Слот недоступен. Выберите другой.")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


# ============================================================================
# Запуск всех примеров
# ============================================================================

async def run_all_examples():
    """Запустить все примеры по очереди."""
    examples = [
        example_create_simple_supply,
        example_create_supply_with_cargoes,
        example_get_supplies_list,
        example_get_supplies_by_status,
        example_check_available_timeslots,
        example_update_supply,
        example_cancel_supply,
        example_get_warehouses,
        example_validate_and_create,
    ]

    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)  # Пауза между примерами
        except Exception as e:
            print(f"Ошибка в примере {example.__name__}: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Примеры использования Ozon FBO Supply Bot API\n")
    print("⚠️  Замените 'your_client_id' и 'your_api_key' на реальные значения!")
    print()

    # Раскомментируйте нужный пример:

    # Запустить конкретный пример:
    # asyncio.run(example_create_simple_supply())
    # asyncio.run(example_check_available_timeslots())

    # Или запустить все примеры:
    # asyncio.run(run_all_examples())

    print("\n✨ Для запуска примеров раскомментируйте нужную строку в main блоке")
