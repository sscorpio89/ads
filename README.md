# Ozon FBO Supply Bot - Telegram Mini App

Telegram Mini App для управления заявками на поставку FBO (Fulfillment by Ozon) через Ozon Seller API.

## Возможности

### Основной функционал

- **Создание заявок на поставку FBO** - автоматическое создание заявок с указанием склада, даты и временного слота
- **Редактирование заявок** - изменение параметров существующих заявок (ребукинг)
- **Удаление заявок** - отмена ненужных заявок на поставку
- **Просмотр списка заявок** - получение всех заявок с фильтрацией по статусу
- **Управление грузоместами** - добавление и редактирование информации о грузоместах
- **Проверка доступных слотов** - просмотр свободных временных окон на складах Ozon

### Дополнительный функционал

- Получение списка доступных складов
- Валидация временных слотов перед созданием заявки
- Автоматическая обработка ошибок с повторными попытками
- Безопасное хранение API ключей (шифрование)

## Структура проекта

```
ads/
├── src/
│   ├── api/                        # API клиенты
│   │   ├── __init__.py
│   │   └── ozon_client.py         # Клиент для Ozon Seller API
│   ├── models/                     # Модели данных (Pydantic)
│   │   ├── __init__.py
│   │   └── supply.py              # Модели заявок, грузомест, слотов
│   ├── services/                   # Бизнес-логика
│   │   ├── __init__.py
│   │   └── supply_service.py      # Сервис для управления заявками
│   ├── handlers/                   # API handlers (FastAPI)
│   │   ├── __init__.py
│   │   └── supply_handlers.py     # REST API endpoints
│   ├── config/                     # Конфигурация
│   │   ├── __init__.py
│   │   └── settings.py            # Настройки приложения
│   ├── __init__.py
│   └── main.py                    # Точка входа приложения
├── static/                         # Статические файлы для Mini App
├── requirements.txt                # Python зависимости
├── .env.example                   # Пример переменных окружения
└── README.md                      # Документация
```

## Установка и запуск

### 1. Требования

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Telegram Bot Token

### 2. Установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env файл
nano .env
```

Обязательные переменные:
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `SECRET_KEY` - секретный ключ для сессий
- `ENCRYPTION_KEY` - ключ для шифрования API ключей пользователей
- `POSTGRES_*` - настройки подключения к PostgreSQL
- `REDIS_*` - настройки подключения к Redis

### 4. Запуск приложения

```bash
# Запуск в режиме разработки
cd src
python main.py

# Или через uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: `http://localhost:8000`

API документация (Swagger): `http://localhost:8000/docs`

## API Методы

### Создание заявки на поставку

**Endpoint:** `POST /api/supplies/create`

**Описание:** Создает новую заявку на поставку FBO с автоматическим созданием черновика.

**Request Body:**
```json
{
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
        {
          "product_id": 123456,
          "quantity": 10
        }
      ],
      "weight": 15.5,
      "width": 40,
      "height": 30,
      "depth": 50
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "supply": {
    "supply_id": "SUP123456",
    "supply_date": "2025-11-15",
    "warehouse_id": 12345,
    "status": "confirmed",
    "timeslot_from": "10:00",
    "timeslot_to": "14:00",
    "total_items": 10
  }
}
```

**Пример использования в Python:**

```python
from src.api.ozon_client import OzonAPIClient
from src.services.supply_service import SupplyService
from src.models.supply import CargoItem, ProductInCargo, CargoType

# Инициализация клиента
async with OzonAPIClient(client_id="your_id", api_key="your_key") as client:
    service = SupplyService(client)

    # Создание грузоместа
    cargo = CargoItem(
        cargo_id="CARGO001",
        cargo_type=CargoType.BOX,
        products=[ProductInCargo(product_id=123456, quantity=10)],
        weight=15.5
    )

    # Создание заявки
    supply = await service.create_supply_request(
        warehouse_id=12345,
        supply_date="2025-11-15",
        timeslot_from="10:00",
        timeslot_to="14:00",
        cargoes=[cargo]
    )

    print(f"Created supply: {supply.supply_id}")
```

---

### Получение списка заявок

**Endpoint:** `GET /api/supplies/list`

**Описание:** Возвращает список заявок на поставку с возможностью фильтрации.

**Query Parameters:**
- `limit` (int, optional) - Количество заявок (по умолчанию 50)
- `offset` (int, optional) - Смещение для пагинации (по умолчанию 0)
- `status` (string, optional) - Фильтр по статусу: `draft`, `confirmed`, `in_transit`, `delivered`, `cancelled`

**Response:**
```json
{
  "success": true,
  "supplies": [
    {
      "supply_id": "SUP123456",
      "supply_date": "2025-11-15",
      "warehouse_id": 12345,
      "warehouse_name": "Склад Котельники",
      "status": "confirmed",
      "timeslot_from": "10:00",
      "timeslot_to": "14:00",
      "total_items": 10
    }
  ],
  "total": 1
}
```

**Пример использования:**

```python
# Получить все подтвержденные заявки
supplies = await service.get_supply_requests(
    limit=50,
    status=SupplyStatus.CONFIRMED
)

for supply in supplies:
    print(f"{supply.supply_id}: {supply.supply_date}")
```

---

### Получение информации о заявке

**Endpoint:** `GET /api/supplies/{supply_id}`

**Описание:** Возвращает подробную информацию о конкретной заявке.

**Path Parameters:**
- `supply_id` (string) - ID заявки

**Response:**
```json
{
  "success": true,
  "supply": {
    "supply_id": "SUP123456",
    "draft_id": "DRAFT789",
    "supply_number": "20251115-001",
    "supply_date": "2025-11-15",
    "warehouse_id": 12345,
    "warehouse_name": "Склад Котельники",
    "status": "confirmed",
    "timeslot_from": "10:00",
    "timeslot_to": "14:00",
    "total_items": 10,
    "created_at": "2025-11-07T10:00:00",
    "updated_at": "2025-11-07T10:05:00"
  }
}
```

---

### Редактирование заявки

**Endpoint:** `PUT /api/supplies/{supply_id}`

**Описание:** Обновляет параметры существующей заявки (ребукинг). Фактически создает новую заявку с новыми параметрами и отменяет старую.

**Path Parameters:**
- `supply_id` (string) - ID заявки для редактирования

**Request Body:**
```json
{
  "supply_date": "2025-11-16",
  "timeslot_from": "14:00",
  "timeslot_to": "18:00"
}
```

**Response:**
```json
{
  "success": true,
  "supply": {
    "supply_id": "SUP123457",
    "supply_date": "2025-11-16",
    "timeslot_from": "14:00",
    "timeslot_to": "18:00",
    "status": "confirmed"
  }
}
```

**Пример использования:**

```python
# Изменить дату и время заявки
updated_supply = await service.update_supply_request(
    supply_id="SUP123456",
    new_supply_date="2025-11-16",
    new_timeslot_from="14:00",
    new_timeslot_to="18:00"
)
```

---

### Удаление заявки

**Endpoint:** `DELETE /api/supplies/{supply_id}`

**Описание:** Отменяет (удаляет) заявку на поставку.

**Path Parameters:**
- `supply_id` (string) - ID заявки

**Query Parameters:**
- `reason` (string, optional) - Причина отмены

**Response:**
```json
{
  "success": true,
  "message": "Заявка SUP123456 успешно отменена"
}
```

**Пример использования:**

```python
# Отменить заявку
success = await service.delete_supply_request(
    supply_id="SUP123456"
)

if success:
    print("Заявка успешно отменена")
```

---

### Получение доступных временных слотов

**Endpoint:** `GET /api/timeslots/{warehouse_id}`

**Описание:** Возвращает информацию о доступных временных слотах для указанного склада.

**Path Parameters:**
- `warehouse_id` (int) - ID склада

**Query Parameters:**
- `delivery_type` (string, optional) - Тип доставки: `fbo` или `crossborder` (по умолчанию `fbo`)

**Response:**
```json
{
  "success": true,
  "timeslots": {
    "warehouse_id": 12345,
    "delivery_type": "fbo",
    "timeslots": [
      {
        "date": "2025-11-15",
        "period": {
          "from_time": "10:00",
          "to_time": "14:00"
        },
        "limit": 1000,
        "available": true
      },
      {
        "date": "2025-11-15",
        "period": {
          "from_time": "14:00",
          "to_time": "18:00"
        },
        "limit": 500,
        "available": true
      }
    ]
  }
}
```

**Пример использования:**

```python
# Получить доступные слоты
timeslots = await service.get_available_timeslots(warehouse_id=12345)

for slot in timeslots.timeslots:
    if slot.available:
        print(f"Доступен слот: {slot.date} {slot.period.from_time}-{slot.period.to_time}")
```

---

### Получение списка складов

**Endpoint:** `GET /api/warehouses`

**Описание:** Возвращает список доступных складов Ozon.

**Response:**
```json
{
  "success": true,
  "warehouses": [
    {
      "warehouse_id": 12345,
      "name": "Склад Котельники",
      "address": "г. Котельники, ул. Складская, д. 1",
      "city": "Москва",
      "is_active": true
    },
    {
      "warehouse_id": 67890,
      "name": "Склад Санкт-Петербург",
      "address": "г. Санкт-Петербург, пр. Складской, д. 10",
      "city": "Санкт-Петербург",
      "is_active": true
    }
  ]
}
```

---

## Модели данных

### SupplyRequest (Заявка на поставку)

```python
class SupplyRequest(BaseModel):
    supply_id: str                    # ID заявки
    draft_id: Optional[str]           # ID черновика
    supply_number: Optional[str]      # Номер поставки
    supply_date: str                  # Дата поставки (YYYY-MM-DD)
    warehouse_id: int                 # ID склада
    warehouse_name: Optional[str]     # Название склада
    status: SupplyStatus              # Статус заявки
    timeslot_from: str                # Начало слота (HH:MM)
    timeslot_to: str                  # Конец слота (HH:MM)
    total_items: int                  # Общее количество товаров
    created_at: datetime              # Дата создания
    updated_at: Optional[datetime]    # Дата обновления
```

### CargoItem (Грузоместо)

```python
class CargoItem(BaseModel):
    cargo_id: str                     # ID грузоместа
    cargo_type: CargoType             # Тип: Короб, Паллета, Монопаллета, Суперсейф
    products: List[ProductInCargo]    # Список товаров
    weight: Optional[float]           # Вес (кг)
    width: Optional[int]              # Ширина (см)
    height: Optional[int]             # Высота (см)
    depth: Optional[int]              # Глубина (см)
```

### Timeslot (Временной слот)

```python
class Timeslot(BaseModel):
    date: str                         # Дата слота (YYYY-MM-DD)
    period: TimeslotPeriod            # Временной период
    limit: int                        # Лимит приемки
    available: bool                   # Доступен ли слот
```

## Telegram Mini App интеграция

Для интеграции с Telegram Mini App используйте следующий код:

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <script>
        // Инициализация Telegram Web App
        const tg = window.Telegram.WebApp;
        tg.expand();

        // Получение данных пользователя
        const user = tg.initDataUnsafe.user;

        // Вызов API
        async function createSupply() {
            const response = await fetch('/api/supplies/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    warehouse_id: 12345,
                    supply_date: '2025-11-15',
                    timeslot_from: '10:00',
                    timeslot_to: '14:00'
                })
            });

            const data = await response.json();
            if (data.success) {
                tg.showAlert('Заявка создана: ' + data.supply.supply_id);
            }
        }
    </script>
</body>
</html>
```

## Безопасность

### Шифрование API ключей

API ключи пользователей хранятся в БД в зашифрованном виде. Для шифрования используется AES-256.

### Rate Limiting

Ozon API ограничивает количество запросов (обычно 100-200 req/min). Клиент автоматически обрабатывает эти ограничения с повторными попытками.

### Обработка ошибок

Все ошибки API автоматически логируются и обрабатываются с понятными сообщениями для пользователя.

## Логирование и мониторинг

Приложение поддерживает интеграцию с:
- **Sentry** - для отслеживания ошибок
- **Prometheus** - для сбора метрик
- **Grafana** - для визуализации метрик

## Разработка

### Запуск тестов

```bash
pytest
```

### Форматирование кода

```bash
black src/
```

### Проверка типов

```bash
mypy src/
```

## Deployment

### Docker

```bash
# Собрать образ
docker build -t ozon-fbo-bot .

# Запустить контейнер
docker run -p 8000:8000 --env-file .env ozon-fbo-bot
```

### Docker Compose

```bash
docker-compose up -d
```

## Поддержка

По вопросам и проблемам создавайте issues в репозитории GitHub.

## Лицензия

MIT

## Автор

Разработано для автоматизации работы с заявками на поставку FBO на маркетплейсе Ozon.
