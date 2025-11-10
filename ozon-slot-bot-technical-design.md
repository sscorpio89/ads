# Техническая документация: Ozon Slot Monitor Bot

## Содержание
1. [Архитектура системы](#архитектура-системы)
2. [Компоненты системы](#компоненты-системы)
3. [Схема базы данных](#схема-базы-данных)
4. [API спецификация](#api-спецификация)
5. [Roadmap разработки](#roadmap-разработки)

---

# 1. Архитектура системы

## 1.1 Общая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Telegram   │  │  Web Admin   │  │  Mobile App  │         │
│  │     Bot      │  │   Panel      │  │  (Future)    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼────────────────┐
│         │      APPLICATION LAYER              │                │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌───────▼──────┐         │
│  │   Bot        │  │   FastAPI    │  │   GraphQL    │         │
│  │   Server     │◄─┤   REST API   │◄─┤   Gateway    │         │
│  │  (Aiogram)   │  │              │  │   (Future)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘         │
│         │                  │                                    │
│         └──────────┬───────┘                                    │
│                    │                                            │
│  ┌─────────────────▼────────────────────────────────┐          │
│  │          Business Logic Layer                    │          │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────┐│          │
│  │  │   Slot       │ │  User        │ │ Payment  ││          │
│  │  │   Monitor    │ │  Service     │ │ Service  ││          │
│  │  │   Service    │ │              │ │          ││          │
│  │  └──────────────┘ └──────────────┘ └──────────┘│          │
│  └───────────────────────────────────────────────────┘         │
└─────────────────────────────────┬──────────────────────────────┘
                                  │
┌─────────────────────────────────▼──────────────────────────────┐
│                      TASK QUEUE LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Celery     │  │   Celery     │  │    Redis     │         │
│  │   Worker 1   │  │   Worker N   │  │    Broker    │         │
│  │ (Monitoring) │  │ (Notifications)│ │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────┬──────────────────────────────┘
                                  │
┌─────────────────────────────────▼──────────────────────────────┐
│                      DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │    Redis     │  │   S3/Minio   │         │
│  │  (Main DB)   │  │    Cache     │  │  (Files)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────┬──────────────────────────────┘
                                  │
┌─────────────────────────────────▼──────────────────────────────┐
│                   EXTERNAL SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Ozon API   │  │  Telegram    │  │   Sentry     │         │
│  │   Seller     │  │     API      │  │  (Errors)    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────────────────────────────────────────┘
```

## 1.2 Поток данных

### Регистрация пользователя
```
User → Telegram Bot → Bot Server → User Service → PostgreSQL
                                  → Validate Ozon API
                                  → Create User Record
                                  → Send Welcome Message
```

### Мониторинг слотов
```
Celery Beat (Scheduler)
  → Celery Worker (Monitor Task)
    → Get Active Users from PostgreSQL
    → For each user:
      → Fetch Slots from Ozon API
      → Compare with previous state (Redis Cache)
      → If new slots found:
        → Save to PostgreSQL
        → Queue Notification Task
        → Celery Worker (Notification)
          → Send to Telegram
          → Update notification status
```

### Обработка webhook от Ozon (Future)
```
Ozon → Nginx → FastAPI → Webhook Handler
                       → Validate signature
                       → Process event
                       → Update database
                       → Notify user (if needed)
```

---

# 2. Компоненты системы

## 2.1 Telegram Bot (Aiogram 3.x)

### Структура проекта
```
bot/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration
├── handlers/                  # Message handlers
│   ├── __init__.py
│   ├── start.py              # /start, /help commands
│   ├── registration.py       # User registration flow
│   ├── settings.py           # User settings management
│   ├── warehouses.py         # Warehouse selection
│   ├── notifications.py      # Notification settings
│   ├── stats.py              # Statistics
│   └── payment.py            # Subscription & payments
├── keyboards/                 # Telegram keyboards
│   ├── __init__.py
│   ├── inline.py             # Inline keyboards
│   └── reply.py              # Reply keyboards
├── middlewares/               # Bot middlewares
│   ├── __init__.py
│   ├── auth.py               # Authentication
│   ├── throttling.py         # Rate limiting
│   └── logging.py            # Request logging
├── filters/                   # Custom filters
│   ├── __init__.py
│   ├── subscription.py       # Check subscription status
│   └── admin.py              # Admin filter
├── states/                    # FSM states
│   ├── __init__.py
│   ├── registration.py
│   └── settings.py
└── utils/                     # Utilities
    ├── __init__.py
    ├── formatters.py         # Message formatters
    └── validators.py         # Input validators
```

### Основные хендлеры

#### 2.1.1 Регистрация (`handlers/registration.py`)
```python
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    # Check if user exists
    # If not, start registration
    # If yes, show main menu

@router.message(StateFilter(RegistrationStates.waiting_for_api_key))
async def process_client_id(message: Message, state: FSMContext):
    """Process Ozon Client-ID"""
    # Validate format
    # Save to FSM context
    # Ask for API key

@router.message(StateFilter(RegistrationStates.waiting_for_api_key))
async def process_api_key(message: Message, state: FSMContext):
    """Process Ozon API Key"""
    # Validate with Ozon API
    # Create user record
    # Show success message
```

#### 2.1.2 Настройки (`handlers/settings.py`)
```python
@router.callback_query(F.data == "settings_warehouses")
async def settings_warehouses(callback: CallbackQuery):
    """Warehouse selection"""
    # Fetch available warehouses from Ozon
    # Show selection keyboard

@router.callback_query(F.data == "settings_quiet_hours")
async def settings_quiet_hours(callback: CallbackQuery, state: FSMContext):
    """Configure quiet hours"""
    # Show time range selection
    # Save preferences
```

#### 2.1.3 Уведомления о слотах
```python
async def send_slot_notification(
    bot: Bot,
    user_id: int,
    slot: SlotModel
):
    """Send slot notification to user"""
    text = format_slot_message(slot)
    keyboard = create_slot_keyboard(slot)

    await bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
```

## 2.2 FastAPI REST API

### Структура проекта
```
api/
├── __init__.py
├── main.py                    # FastAPI app
├── dependencies.py            # DI dependencies
├── routers/                   # API routes
│   ├── __init__.py
│   ├── users.py              # User management
│   ├── slots.py              # Slot data
│   ├── warehouses.py         # Warehouses
│   ├── subscriptions.py      # Subscriptions
│   ├── webhooks.py           # Webhooks
│   └── analytics.py          # Analytics
├── schemas/                   # Pydantic models
│   ├── __init__.py
│   ├── user.py
│   ├── slot.py
│   ├── warehouse.py
│   └── subscription.py
├── crud/                      # Database operations
│   ├── __init__.py
│   ├── user.py
│   ├── slot.py
│   └── subscription.py
└── middleware/
    ├── __init__.py
    ├── auth.py               # JWT authentication
    ├── cors.py               # CORS
    └── rate_limit.py         # Rate limiting
```

## 2.3 Business Logic Services

### 2.3.1 Slot Monitor Service (`services/slot_monitor.py`)
```python
class SlotMonitorService:
    """Service for monitoring Ozon slots"""

    def __init__(
        self,
        ozon_client: OzonAPIClient,
        db: Database,
        cache: Redis
    ):
        self.ozon = ozon_client
        self.db = db
        self.cache = cache

    async def check_slots_for_user(
        self,
        user_id: int
    ) -> list[SlotFound]:
        """Check slots for a specific user"""
        # Get user preferences
        user = await self.db.get_user(user_id)

        # Fetch slots from Ozon
        slots = await self.ozon.get_available_slots(
            client_id=user.ozon_client_id,
            api_key=user.ozon_api_key
        )

        # Filter by user preferences
        filtered = self._filter_slots(slots, user.preferences)

        # Compare with cache to find new slots
        cache_key = f"slots:{user_id}"
        cached_slots = await self.cache.get(cache_key)

        new_slots = self._find_new_slots(filtered, cached_slots)

        # Update cache
        await self.cache.set(cache_key, filtered, expire=300)

        # Save new slots to database
        if new_slots:
            await self.db.save_slots(user_id, new_slots)

        return new_slots

    def _filter_slots(
        self,
        slots: list[OzonSlot],
        preferences: UserPreferences
    ) -> list[OzonSlot]:
        """Filter slots by user preferences"""
        result = []

        for slot in slots:
            # Check warehouse filter
            if preferences.warehouses and \
               slot.warehouse_id not in preferences.warehouses:
                continue

            # Check delivery type filter
            if preferences.delivery_types and \
               slot.delivery_type not in preferences.delivery_types:
                continue

            # Check time range
            if not self._is_in_time_range(
                slot.datetime,
                preferences.time_range
            ):
                continue

            result.append(slot)

        return result

    def _find_new_slots(
        self,
        current: list[OzonSlot],
        cached: list[OzonSlot]
    ) -> list[OzonSlot]:
        """Find new slots that weren't in cache"""
        if not cached:
            return current

        cached_ids = {s.id for s in cached}
        return [s for s in current if s.id not in cached_ids]
```

### 2.3.2 User Service (`services/user.py`)
```python
class UserService:
    """User management service"""

    async def create_user(
        self,
        telegram_id: int,
        ozon_client_id: str,
        ozon_api_key: str
    ) -> User:
        """Create new user"""
        # Validate Ozon credentials
        is_valid = await self.ozon.validate_credentials(
            ozon_client_id,
            ozon_api_key
        )

        if not is_valid:
            raise InvalidCredentialsError()

        # Encrypt API key
        encrypted_key = self._encrypt_api_key(ozon_api_key)

        # Create user record
        user = await self.db.create_user(
            telegram_id=telegram_id,
            ozon_client_id=ozon_client_id,
            ozon_api_key=encrypted_key,
            subscription_status="trial",
            trial_ends_at=datetime.now() + timedelta(days=7)
        )

        return user

    async def update_preferences(
        self,
        user_id: int,
        preferences: UserPreferencesUpdate
    ) -> User:
        """Update user preferences"""
        return await self.db.update_user_preferences(
            user_id,
            preferences
        )

    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key before storing"""
        from cryptography.fernet import Fernet
        cipher = Fernet(settings.ENCRYPTION_KEY)
        return cipher.encrypt(api_key.encode()).decode()

    def _decrypt_api_key(self, encrypted: str) -> str:
        """Decrypt API key for use"""
        from cryptography.fernet import Fernet
        cipher = Fernet(settings.ENCRYPTION_KEY)
        return cipher.decrypt(encrypted.encode()).decode()
```

### 2.3.3 Notification Service (`services/notification.py`)
```python
class NotificationService:
    """Service for sending notifications"""

    async def notify_new_slots(
        self,
        user_id: int,
        slots: list[SlotFound]
    ):
        """Send notifications about new slots"""
        user = await self.db.get_user(user_id)

        # Check quiet hours
        if self._is_quiet_time(user.preferences.quiet_hours):
            # Schedule for later
            await self._schedule_notification(user_id, slots)
            return

        # Group slots if needed
        if len(slots) > 5:
            await self._send_grouped_notification(user, slots)
        else:
            for slot in slots:
                await self._send_single_notification(user, slot)

        # Update notification stats
        await self.db.increment_notification_count(user_id)

    async def _send_single_notification(
        self,
        user: User,
        slot: SlotFound
    ):
        """Send single slot notification"""
        text = self._format_slot_message(slot)
        keyboard = self._create_slot_keyboard(slot)

        await self.bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            reply_markup=keyboard
        )

        # Log notification
        await self.db.log_notification(
            user_id=user.id,
            slot_id=slot.id,
            sent_at=datetime.now()
        )
```

### 2.3.4 Payment Service (`services/payment.py`)
```python
class PaymentService:
    """Payment and subscription management"""

    async def create_subscription(
        self,
        user_id: int,
        plan: SubscriptionPlan,
        stars_amount: int
    ) -> Subscription:
        """Create new subscription"""
        # Validate plan and amount
        if plan.price_stars != stars_amount:
            raise InvalidPaymentError()

        # Create subscription record
        subscription = await self.db.create_subscription(
            user_id=user_id,
            plan=plan.name,
            status="pending",
            started_at=datetime.now(),
            expires_at=datetime.now() + plan.duration
        )

        return subscription

    async def confirm_payment(
        self,
        subscription_id: int,
        telegram_payment_id: str
    ):
        """Confirm payment and activate subscription"""
        subscription = await self.db.get_subscription(subscription_id)

        # Verify payment with Telegram
        is_paid = await self._verify_telegram_payment(
            telegram_payment_id
        )

        if not is_paid:
            raise PaymentVerificationError()

        # Activate subscription
        await self.db.update_subscription(
            subscription_id,
            status="active",
            payment_id=telegram_payment_id
        )

        # Update user status
        await self.db.update_user(
            subscription.user_id,
            subscription_status="active"
        )

    async def check_expired_subscriptions(self):
        """Check and deactivate expired subscriptions"""
        expired = await self.db.get_expired_subscriptions()

        for subscription in expired:
            await self.db.update_subscription(
                subscription.id,
                status="expired"
            )

            await self.db.update_user(
                subscription.user_id,
                subscription_status="expired"
            )

            # Notify user
            await self.notification.send_subscription_expired(
                subscription.user_id
            )
```

## 2.4 Celery Workers

### 2.4.1 Celery Configuration (`celery_app.py`)
```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "ozon_slot_bot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "tasks.monitor.*": {"queue": "monitoring"},
        "tasks.notify.*": {"queue": "notifications"},
        "tasks.payment.*": {"queue": "payments"}
    },

    # Beat schedule
    beat_schedule={
        "check-slots-every-minute": {
            "task": "tasks.monitor.check_all_users_slots",
            "schedule": 60.0,  # Every 60 seconds
        },
        "check-expired-subscriptions": {
            "task": "tasks.payment.check_expired_subscriptions",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
        },
        "cleanup-old-slots": {
            "task": "tasks.cleanup.delete_old_slots",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        }
    }
)
```

### 2.4.2 Monitoring Tasks (`tasks/monitor.py`)
```python
from celery import shared_task
from services.slot_monitor import SlotMonitorService

@shared_task(
    name="tasks.monitor.check_all_users_slots",
    bind=True,
    max_retries=3
)
def check_all_users_slots(self):
    """Check slots for all active users"""
    try:
        service = SlotMonitorService()
        active_users = service.get_active_users()

        for user in active_users:
            # Create subtask for each user
            check_user_slots.delay(user.id)

        return {
            "status": "success",
            "users_processed": len(active_users)
        }
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(
    name="tasks.monitor.check_user_slots",
    bind=True,
    max_retries=3,
    rate_limit="30/m"  # Max 30 per minute per worker
)
def check_user_slots(self, user_id: int):
    """Check slots for specific user"""
    try:
        service = SlotMonitorService()
        new_slots = service.check_slots_for_user(user_id)

        if new_slots:
            # Queue notifications
            from tasks.notify import send_slot_notifications
            send_slot_notifications.delay(user_id, new_slots)

        return {
            "user_id": user_id,
            "new_slots": len(new_slots)
        }
    except OzonAPIError as exc:
        # Don't retry on API errors
        logger.error(f"Ozon API error for user {user_id}: {exc}")
        return {"error": str(exc)}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### 2.4.3 Notification Tasks (`tasks/notify.py`)
```python
@shared_task(
    name="tasks.notify.send_slot_notifications",
    bind=True,
    max_retries=5
)
def send_slot_notifications(self, user_id: int, slots: list[dict]):
    """Send slot notifications to user"""
    try:
        service = NotificationService()
        service.notify_new_slots(user_id, slots)

        return {
            "user_id": user_id,
            "notifications_sent": len(slots)
        }
    except TelegramError as exc:
        # Retry Telegram errors
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)
```

---

# 3. Схема базы данных

## 3.1 PostgreSQL Schema

```sql
-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),

    -- Ozon credentials (encrypted)
    ozon_client_id VARCHAR(255) NOT NULL,
    ozon_api_key TEXT NOT NULL,

    -- Subscription
    subscription_status VARCHAR(50) DEFAULT 'trial',
    subscription_plan VARCHAR(50),
    trial_ends_at TIMESTAMP,
    subscription_expires_at TIMESTAMP,

    -- Preferences (JSONB for flexibility)
    preferences JSONB DEFAULT '{}'::jsonb,

    -- Stats
    total_notifications INT DEFAULT 0,
    total_slots_found INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP,

    -- Soft delete
    deleted_at TIMESTAMP
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_subscription_status ON users(subscription_status);
CREATE INDEX idx_users_subscription_expires_at ON users(subscription_expires_at);

-- User preferences structure example:
-- {
--   "warehouses": [123, 456, 789],
--   "delivery_types": ["FBO"],
--   "quiet_hours": {
--     "enabled": true,
--     "start": "22:00",
--     "end": "08:00",
--     "timezone": "Europe/Moscow"
--   },
--   "notification_grouping": true,
--   "favorite_warehouses": [123]
-- }

-- Warehouses table (cached from Ozon)
CREATE TABLE warehouses (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    region VARCHAR(255),
    warehouse_type VARCHAR(50),
    is_active BOOLEAN DEFAULT true,

    -- Additional data from Ozon API
    metadata JSONB,

    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_warehouses_city ON warehouses(city);
CREATE INDEX idx_warehouses_is_active ON warehouses(is_active);

-- Slots table
CREATE TABLE slots (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    -- Slot details
    warehouse_id BIGINT REFERENCES warehouses(id),
    warehouse_name VARCHAR(255),

    delivery_type VARCHAR(50),
    slot_datetime TIMESTAMP NOT NULL,

    -- Ozon specific data
    ozon_slot_id VARCHAR(255),
    cluster_name VARCHAR(255),

    -- Metadata
    metadata JSONB,

    -- Tracking
    found_at TIMESTAMP DEFAULT NOW(),
    notified_at TIMESTAMP,
    clicked_at TIMESTAMP,

    -- Status
    is_available BOOLEAN DEFAULT true
);

CREATE INDEX idx_slots_user_id ON slots(user_id);
CREATE INDEX idx_slots_slot_datetime ON slots(slot_datetime);
CREATE INDEX idx_slots_warehouse_id ON slots(warehouse_id);
CREATE INDEX idx_slots_found_at ON slots(found_at);

-- Subscriptions table
CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',

    -- Payment
    price_amount INT,
    price_currency VARCHAR(10),
    payment_method VARCHAR(50),
    payment_id VARCHAR(255),

    -- Period
    started_at TIMESTAMP,
    expires_at TIMESTAMP,

    -- Tracking
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_expires_at ON subscriptions(expires_at);

-- Notifications log table
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    slot_id BIGINT REFERENCES slots(id) ON DELETE CASCADE,

    notification_type VARCHAR(50),

    sent_at TIMESTAMP DEFAULT NOW(),
    delivered BOOLEAN DEFAULT false,
    error_message TEXT
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at);

-- Analytics events table
CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,

    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);

-- API keys table (for API access)
CREATE TABLE api_keys (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),

    -- Permissions
    scopes TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Rate limiting
    rate_limit_per_minute INT DEFAULT 60,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Webhook subscriptions (for future integrations)
CREATE TABLE webhook_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    url TEXT NOT NULL,
    secret VARCHAR(255),

    -- Events to subscribe
    events TEXT[] NOT NULL,

    -- Status
    is_active BOOLEAN DEFAULT true,
    failed_attempts INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    last_triggered_at TIMESTAMP
);

CREATE INDEX idx_webhook_subscriptions_user_id ON webhook_subscriptions(user_id);
```

## 3.2 Redis Schema

```
# User slot cache (TTL: 5 minutes)
slots:{user_id} → JSON array of slot objects

# User session state (FSM)
fsm:{telegram_id}:state → state name
fsm:{telegram_id}:data → JSON state data

# Rate limiting
rate_limit:api:{api_key}:{minute} → request count (TTL: 60s)
rate_limit:ozon:{user_id}:{minute} → request count (TTL: 60s)

# Ozon API cache (TTL: 10 minutes)
ozon:warehouses → JSON array of warehouses
ozon:user:{user_id}:profile → JSON user profile

# Task locks
lock:monitor:{user_id} → lock to prevent duplicate monitoring

# Notification queue
queue:notifications:pending → List of notification IDs

# Analytics counters
stats:daily:{date}:new_users → counter
stats:daily:{date}:notifications_sent → counter
stats:daily:{date}:slots_found → counter
```

---

# 4. API Спецификация

## 4.1 REST API Endpoints

### Base URL
```
Production: https://api.ozonslotbot.com/v1
Staging: https://staging-api.ozonslotbot.com/v1
```

### Authentication
```
Bearer Token (JWT) in Authorization header:
Authorization: Bearer <token>

API Key in header:
X-API-Key: <api_key>
```

---

### 4.1.1 Users

#### GET /users/me
Получить информацию о текущем пользователе

**Response 200:**
```json
{
  "id": 123,
  "telegram_id": 987654321,
  "username": "john_doe",
  "subscription": {
    "status": "active",
    "plan": "standard",
    "expires_at": "2025-12-31T23:59:59Z"
  },
  "preferences": {
    "warehouses": [123, 456],
    "delivery_types": ["FBO"],
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00"
    }
  },
  "stats": {
    "total_notifications": 150,
    "total_slots_found": 45
  },
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### PATCH /users/me
Обновить настройки пользователя

**Request:**
```json
{
  "preferences": {
    "warehouses": [123, 456, 789],
    "quiet_hours": {
      "enabled": true,
      "start": "23:00",
      "end": "09:00"
    }
  }
}
```

**Response 200:**
```json
{
  "id": 123,
  "preferences": {...},
  "updated_at": "2025-11-10T15:30:00Z"
}
```

#### POST /users/me/ozon-credentials
Обновить Ozon API credentials

**Request:**
```json
{
  "client_id": "123456",
  "api_key": "secret-api-key"
}
```

**Response 200:**
```json
{
  "status": "verified",
  "message": "Credentials validated successfully"
}
```

---

### 4.1.2 Slots

#### GET /slots
Получить историю найденных слотов

**Query Parameters:**
- `limit` (int, default: 50): Количество слотов
- `offset` (int, default: 0): Смещение для пагинации
- `warehouse_id` (int, optional): Фильтр по складу
- `from_date` (datetime, optional): Начало периода
- `to_date` (datetime, optional): Конец периода

**Response 200:**
```json
{
  "total": 150,
  "items": [
    {
      "id": 1001,
      "warehouse": {
        "id": 123,
        "name": "Москва (Южное Бутово)"
      },
      "delivery_type": "FBO",
      "slot_datetime": "2025-11-15T14:00:00Z",
      "found_at": "2025-11-10T10:30:00Z",
      "notified_at": "2025-11-10T10:30:05Z",
      "clicked": true,
      "is_available": false
    }
  ]
}
```

#### GET /slots/stats
Получить статистику по слотам

**Query Parameters:**
- `period` (string): "day", "week", "month"

**Response 200:**
```json
{
  "period": "week",
  "total_slots_found": 45,
  "by_warehouse": [
    {
      "warehouse_id": 123,
      "warehouse_name": "Москва (Южное Бутово)",
      "count": 25
    },
    {
      "warehouse_id": 456,
      "warehouse_name": "Санкт-Петербург",
      "count": 20
    }
  ],
  "by_day": [
    {
      "date": "2025-11-04",
      "count": 8
    },
    {
      "date": "2025-11-05",
      "count": 12
    }
  ],
  "by_hour": {
    "10": 5,
    "14": 8,
    "16": 12
  }
}
```

---

### 4.1.3 Warehouses

#### GET /warehouses
Получить список складов Ozon

**Query Parameters:**
- `city` (string, optional): Фильтр по городу
- `is_active` (bool, optional): Только активные склады

**Response 200:**
```json
{
  "items": [
    {
      "id": 123,
      "name": "Москва (Южное Бутово)",
      "city": "Москва",
      "region": "Московская область",
      "warehouse_type": "FBO",
      "is_active": true,
      "coordinates": {
        "lat": 55.123456,
        "lon": 37.654321
      }
    }
  ]
}
```

#### GET /warehouses/{warehouse_id}
Получить детальную информацию о складе

**Response 200:**
```json
{
  "id": 123,
  "name": "Москва (Южное Бутово)",
  "city": "Москва",
  "address": "ул. Складская, д. 10",
  "working_hours": "Пн-Пт: 9:00-18:00",
  "contacts": {
    "phone": "+7 (495) 123-45-67"
  },
  "recent_availability": {
    "last_7_days": 15,
    "last_30_days": 45
  }
}
```

---

### 4.1.4 Subscriptions

#### GET /subscriptions/plans
Получить доступные тарифные планы

**Response 200:**
```json
{
  "plans": [
    {
      "id": "free",
      "name": "Бесплатный",
      "price": 0,
      "duration_days": 7,
      "features": {
        "max_shops": 1,
        "max_warehouses": 2,
        "check_interval_seconds": 300,
        "history_days": 7
      }
    },
    {
      "id": "standard",
      "name": "Стандарт",
      "price": 500,
      "price_currency": "stars",
      "duration_days": 30,
      "features": {
        "max_shops": 1,
        "max_warehouses": null,
        "check_interval_seconds": 60,
        "history_days": 30,
        "quiet_hours": true,
        "filters": true
      }
    },
    {
      "id": "pro",
      "name": "Про",
      "price": 1000,
      "price_currency": "stars",
      "duration_days": 30,
      "features": {
        "max_shops": 5,
        "max_warehouses": null,
        "check_interval_seconds": 60,
        "history_days": 90,
        "quiet_hours": true,
        "filters": true,
        "analytics": true,
        "export": true,
        "web_access": true
      }
    }
  ]
}
```

#### POST /subscriptions
Создать новую подписку

**Request:**
```json
{
  "plan_id": "standard",
  "payment_method": "telegram_stars"
}
```

**Response 201:**
```json
{
  "subscription_id": 456,
  "plan": "standard",
  "status": "pending",
  "payment": {
    "amount": 500,
    "currency": "stars",
    "payment_url": "https://t.me/invoice/..."
  },
  "expires_at": "2025-12-10T23:59:59Z"
}
```

#### GET /subscriptions/current
Получить текущую подписку

**Response 200:**
```json
{
  "id": 456,
  "plan": "standard",
  "status": "active",
  "started_at": "2025-11-10T00:00:00Z",
  "expires_at": "2025-12-10T23:59:59Z",
  "auto_renew": false
}
```

---

### 4.1.5 Webhooks

#### POST /webhooks
Создать webhook подписку

**Request:**
```json
{
  "url": "https://your-app.com/webhooks/ozon-slots",
  "secret": "your-secret-key",
  "events": ["slot.found", "subscription.expired"]
}
```

**Response 201:**
```json
{
  "id": 789,
  "url": "https://your-app.com/webhooks/ozon-slots",
  "events": ["slot.found", "subscription.expired"],
  "is_active": true,
  "created_at": "2025-11-10T15:00:00Z"
}
```

#### GET /webhooks
Получить список webhook подписок

**Response 200:**
```json
{
  "items": [
    {
      "id": 789,
      "url": "https://your-app.com/webhooks/ozon-slots",
      "events": ["slot.found"],
      "is_active": true,
      "failed_attempts": 0,
      "last_triggered_at": "2025-11-10T14:30:00Z"
    }
  ]
}
```

#### DELETE /webhooks/{webhook_id}
Удалить webhook подписку

**Response 204:** No content

---

### 4.1.6 Analytics

#### GET /analytics/dashboard
Получить данные для дашборда

**Response 200:**
```json
{
  "overview": {
    "total_slots_found": 150,
    "total_notifications": 145,
    "notification_click_rate": 0.68,
    "most_available_warehouse": {
      "id": 123,
      "name": "Москва (Южное Бутово)",
      "slots_count": 45
    }
  },
  "recent_activity": [
    {
      "type": "slot_found",
      "warehouse": "Москва (Южное Бутово)",
      "datetime": "2025-11-10T14:00:00Z",
      "timestamp": "2025-11-10T10:30:00Z"
    }
  ],
  "availability_forecast": {
    "next_7_days": [
      {
        "date": "2025-11-11",
        "probability": 0.75,
        "expected_slots": 8
      }
    ]
  }
}
```

---

## 4.2 Webhook Events

### Event: slot.found
Отправляется когда найден новый слот

**Payload:**
```json
{
  "event": "slot.found",
  "timestamp": "2025-11-10T10:30:00Z",
  "data": {
    "user_id": 123,
    "slot": {
      "id": 1001,
      "warehouse": {
        "id": 123,
        "name": "Москва (Южное Бутово)"
      },
      "delivery_type": "FBO",
      "slot_datetime": "2025-11-15T14:00:00Z",
      "found_at": "2025-11-10T10:30:00Z"
    }
  }
}
```

### Event: subscription.expired
Отправляется когда истекает подписка

**Payload:**
```json
{
  "event": "subscription.expired",
  "timestamp": "2025-12-10T23:59:59Z",
  "data": {
    "user_id": 123,
    "subscription": {
      "id": 456,
      "plan": "standard",
      "expired_at": "2025-12-10T23:59:59Z"
    }
  }
}
```

### Event: subscription.renewed
Отправляется при продлении подписки

**Payload:**
```json
{
  "event": "subscription.renewed",
  "timestamp": "2025-12-10T12:00:00Z",
  "data": {
    "user_id": 123,
    "subscription": {
      "id": 789,
      "plan": "standard",
      "started_at": "2025-12-10T12:00:00Z",
      "expires_at": "2026-01-10T23:59:59Z"
    }
  }
}
```

---

## 4.3 Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid Ozon API credentials",
    "details": {
      "field": "api_key",
      "reason": "API key validation failed"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | INVALID_REQUEST | Неверный формат запроса |
| 401 | UNAUTHORIZED | Отсутствует или неверная аутентификация |
| 403 | FORBIDDEN | Недостаточно прав |
| 404 | NOT_FOUND | Ресурс не найден |
| 409 | CONFLICT | Конфликт (например, пользователь уже существует) |
| 422 | VALIDATION_ERROR | Ошибка валидации данных |
| 429 | RATE_LIMIT_EXCEEDED | Превышен лимит запросов |
| 500 | INTERNAL_ERROR | Внутренняя ошибка сервера |
| 503 | SERVICE_UNAVAILABLE | Сервис временно недоступен |

---

# 5. Roadmap разработки

## Sprint 1: Фундамент (2 недели)

### Week 1: Infrastructure & Database

#### День 1-2: Настройка инфраструктуры
- [ ] **INFRA-001**: Настроить Docker Compose для локальной разработки
  - PostgreSQL 15
  - Redis 7
  - PgAdmin
  - Redis Commander
- [ ] **INFRA-002**: Создать структуру проекта (monorepo)
  ```
  /backend
  /bot
  /api
  /workers
  /shared
  /frontend (future)
  ```
- [ ] **INFRA-003**: Настроить pre-commit hooks (black, flake8, mypy)
- [ ] **INFRA-004**: Настроить CI/CD pipeline (GitHub Actions)
  - Lint
  - Tests
  - Build Docker images

#### День 3-4: База данных
- [ ] **DB-001**: Создать PostgreSQL схему
  - Таблица users
  - Таблица warehouses
  - Таблица slots
  - Таблица subscriptions
- [ ] **DB-002**: Настроить Alembic для миграций
- [ ] **DB-003**: Создать SQLAlchemy модели
- [ ] **DB-004**: Написать базовые CRUD операции
- [ ] **DB-005**: Добавить индексы для оптимизации
- [ ] **DB-006**: Написать unit тесты для CRUD

#### День 5: Ozon API интеграция
- [ ] **OZON-001**: Создать Ozon API client
  - Аутентификация
  - Rate limiting
  - Retry механизм
  - Error handling
- [ ] **OZON-002**: Реализовать методы:
  - Валидация credentials
  - Получение списка складов
  - Получение доступных слотов
- [ ] **OZON-003**: Написать unit тесты (с mock)
- [ ] **OZON-004**: Документация по Ozon API wrapper

### Week 2: Telegram Bot Core

#### День 6-7: Базовый бот
- [ ] **BOT-001**: Инициализация Aiogram 3.x проекта
- [ ] **BOT-002**: Создать структуру handlers
- [ ] **BOT-003**: Реализовать команды:
  - `/start` - приветствие
  - `/help` - справка
  - `/status` - статус подписки
- [ ] **BOT-004**: Настроить middleware:
  - Logging
  - Authentication
  - Throttling
- [ ] **BOT-005**: Создать базовые keyboards (inline/reply)

#### День 8-9: Регистрация пользователей
- [ ] **BOT-006**: Создать FSM для регистрации
  - Состояние: ожидание Client-ID
  - Состояние: ожидание API Key
  - Состояние: подтверждение
- [ ] **BOT-007**: Реализовать handler регистрации
  - Валидация формата
  - Проверка через Ozon API
  - Сохранение в БД (с шифрованием)
- [ ] **BOT-008**: Обработка ошибок:
  - Неверные credentials
  - Таймауты API
  - Дубликаты пользователей
- [ ] **BOT-009**: Написать интеграционные тесты

#### День 10: Настройки пользователя
- [ ] **BOT-010**: Меню настроек
  - Список складов для мониторинга
  - Тихие часы
  - Типы поставки
- [ ] **BOT-011**: Реализовать выбор складов
  - Загрузка списка из Ozon
  - Множественный выбор
  - Сохранение preferences
- [ ] **BOT-012**: Реализовать настройку тихих часов
  - Выбор временного диапазона
  - Выбор timezone
- [ ] **BOT-013**: Команда `/settings` для быстрого доступа

---

## Sprint 2: Мониторинг и уведомления (2 недели)

### Week 3: Slot Monitoring

#### День 11-12: Service Layer
- [ ] **SVC-001**: Создать SlotMonitorService
  - Метод check_slots_for_user()
  - Фильтрация по preferences
  - Сравнение с кешем (Redis)
- [ ] **SVC-002**: Создать NotificationService
  - Метод notify_new_slots()
  - Проверка тихих часов
  - Группировка уведомлений
- [ ] **SVC-003**: Написать unit тесты
- [ ] **SVC-004**: Интеграционные тесты с Redis

#### День 13-14: Celery Workers
- [ ] **WORKER-001**: Настроить Celery + Redis
  - Конфигурация очередей
  - Настройка beat schedule
- [ ] **WORKER-002**: Создать задачу мониторинга
  - check_all_users_slots (каждую минуту)
  - check_user_slots (для каждого юзера)
- [ ] **WORKER-003**: Создать задачу уведомлений
  - send_slot_notifications
  - Retry логика для Telegram errors
- [ ] **WORKER-004**: Настроить rate limiting
  - Ozon API: 30 запросов/минуту
  - Telegram API: 30 сообщений/секунду
- [ ] **WORKER-005**: Добавить мониторинг задач (Flower)

#### День 15-16: Уведомления в боте
- [ ] **BOT-014**: Форматирование сообщений о слотах
  - HTML разметка
  - Emoji для визуального восприятия
  - Понятная информация
- [ ] **BOT-015**: Inline клавиатура для слотов
  - Кнопка "Забронировать" (deep link в Ozon)
  - Кнопка "Настройки"
  - Кнопка "Остановить уведомления"
- [ ] **BOT-016**: Группировка уведомлений
  - Если > 5 слотов, отправить одним сообщением
- [ ] **BOT-017**: Callback handlers для кнопок
  - Трекинг кликов
  - Обновление статистики

#### День 17: Testing & Bug Fixes
- [ ] **TEST-001**: End-to-end тест полного цикла
  - Регистрация → Настройки → Мониторинг → Уведомление
- [ ] **TEST-002**: Нагрузочное тестирование
  - 100 пользователей
  - 1000 проверок/минуту
- [ ] **BUG-001**: Исправление найденных багов
- [ ] **DOC-001**: Документация по архитектуре

---

## Sprint 3: Подписки и платежи (1.5 недели)

### Week 4-5: Payment System

#### День 18-19: Subscription Logic
- [ ] **SUB-001**: Создать SubscriptionService
  - Проверка активности подписки
  - Создание trial подписки
  - Активация платной подписки
- [ ] **SUB-002**: Добавить middleware проверки подписки
  - Блокировка функций для free тарифа
  - Информирование о лимитах
- [ ] **SUB-003**: Команда `/subscription` в боте
  - Показать текущий тариф
  - Показать доступные планы
  - Кнопки для покупки

#### День 20-21: Telegram Stars Integration
- [ ] **PAY-001**: Интеграция с Telegram Payments API
  - Создание invoice
  - Обработка successful_payment
  - Обработка pre_checkout_query
- [ ] **PAY-002**: Реализовать процесс покупки в боте
  - Выбор тарифа
  - Отправка invoice
  - Подтверждение оплаты
- [ ] **PAY-003**: PaymentService
  - Создание subscription после оплаты
  - Обновление user.subscription_status
- [ ] **PAY-004**: Тесты платежной системы (mock)

#### День 22-23: Subscription Management
- [ ] **SUB-004**: Celery задача проверки истекших подписок
  - Ежедневно в полночь
  - Деактивация expired subscriptions
  - Уведомление пользователей
- [ ] **SUB-005**: Уведомления о подписке
  - За 3 дня до окончания
  - В день окончания
  - После окончания (предложение продлить)
- [ ] **SUB-006**: Команда `/extend` для продления
- [ ] **SUB-007**: История платежей `/payments`

#### День 24: Polish & Deploy MVP
- [ ] **POL-001**: Улучшение UX
  - Более понятные сообщения
  - Добавить emoji
  - Анимированные сообщения (опционально)
- [ ] **POL-002**: Обработка edge cases
  - Ozon API недоступен
  - Telegram API недоступен
  - Database connection lost
- [ ] **DEPLOY-001**: Подготовка к деплою
  - Environment variables
  - Secrets management
  - Docker images
- [ ] **DEPLOY-002**: Деплой на VPS
  - Docker Compose
  - Nginx reverse proxy
  - SSL сертификаты (Let's Encrypt)
- [ ] **DEPLOY-003**: Настройка мониторинга
  - Healthchecks
  - Uptime monitoring
  - Error tracking (Sentry)

---

## Sprint 4: Analytics & Admin (2 недели)

### Week 6: Analytics

#### День 25-26: Статистика в боте
- [ ] **STAT-001**: Команда `/stats` - личная статистика
  - Найдено слотов за период
  - Кликнутые слоты
  - Самые доступные склады
- [ ] **STAT-002**: AnalyticsService
  - Агрегация данных по периодам
  - Графики в виде текста (ASCII art или эмодзи)
- [ ] **STAT-003**: Экспорт статистики (только Pro план)
  - Генерация CSV файла
  - Отправка через Telegram

#### День 27-28: Analytics API
- [ ] **API-001**: Создать FastAPI приложение
  - Базовая структура
  - JWT authentication
- [ ] **API-002**: Эндпоинты для аналитики
  - GET /analytics/dashboard
  - GET /analytics/slots/stats
  - GET /analytics/warehouses/availability
- [ ] **API-003**: Документация API (OpenAPI/Swagger)
- [ ] **API-004**: Rate limiting middleware
- [ ] **API-005**: CORS configuration

### Week 7: Admin Panel (Backend)

#### День 29-30: Admin API
- [ ] **ADM-001**: Admin authentication
  - Роли: admin, moderator
  - Отдельная таблица admin_users
- [ ] **ADM-002**: Admin endpoints
  - GET /admin/users - список пользователей
  - GET /admin/users/{id} - детали пользователя
  - PATCH /admin/users/{id} - изменение пользователя
  - DELETE /admin/users/{id} - блокировка
- [ ] **ADM-003**: Статистика системы
  - GET /admin/stats/overview
  - GET /admin/stats/monitoring
- [ ] **ADM-004**: Управление подписками
  - POST /admin/subscriptions/grant - дать подписку
  - DELETE /admin/subscriptions/{id} - отменить

#### День 31-32: System Monitoring
- [ ] **MON-001**: Health check endpoint
  - GET /health
  - Проверка DB, Redis, Celery
- [ ] **MON-002**: Metrics endpoint (Prometheus format)
  - GET /metrics
- [ ] **MON-003**: Настройка Grafana dashboard
  - Основные метрики
  - Алерты
- [ ] **MON-004**: Логирование
  - Структурированные логи (JSON)
  - ELK stack (опционально)

---

## Sprint 5: Web Interface (3 недели)

### Week 8-9: Frontend Development

#### Week 8: Core Pages
- [ ] **FE-001**: Инициализация Next.js проекта
  - TypeScript
  - Tailwind CSS
  - shadcn/ui components
- [ ] **FE-002**: Аутентификация
  - Login через Telegram Widget
  - JWT token management
  - Protected routes
- [ ] **FE-003**: Dashboard page
  - Обзор подписки
  - Последние найденные слоты
  - Быстрые действия
- [ ] **FE-004**: Slots history page
  - Таблица с фильтрами
  - Пагинация
  - Сортировка
- [ ] **FE-005**: Settings page
  - Форма редактирования preferences
  - Управление Ozon credentials
  - Тихие часы настройка

#### Week 9: Advanced Features
- [ ] **FE-006**: Analytics page
  - Графики доступности
  - Статистика по складам
  - Интеграция с Chart.js или Recharts
- [ ] **FE-007**: Subscription management page
  - Текущий тариф
  - Upgrade/Downgrade
  - История платежей
- [ ] **FE-008**: Warehouses explorer
  - Карта складов
  - Детальная информация
  - История доступности
- [ ] **FE-009**: Responsive design
  - Mobile optimization
  - Tablet layout
- [ ] **FE-010**: Dark mode

### Week 10: Admin Panel Frontend
- [ ] **FE-011**: Admin layout
- [ ] **FE-012**: Users management page
- [ ] **FE-013**: System stats dashboard
- [ ] **FE-014**: Monitoring page (интеграция с Grafana)

---

## Sprint 6: Advanced Features (2-3 недели)

### Week 11: Draft Management

#### День 33-35: Создание черновиков
- [ ] **DRAFT-001**: Ozon API методы для черновиков
  - Создание черновика
  - Добавление товаров
  - Обновление черновика
- [ ] **DRAFT-002**: DraftService
  - create_draft()
  - add_products()
  - list_drafts()
- [ ] **DRAFT-003**: Бот: создание черновика
  - FSM для процесса создания
  - Выбор склада
  - Выбор товаров (поиск по артикулу)
  - Указание количества
- [ ] **DRAFT-004**: Бот: список черновиков
  - Команда `/drafts`
  - Inline клавиатура для действий
- [ ] **DRAFT-005**: API endpoints
  - GET /drafts
  - POST /drafts
  - PATCH /drafts/{id}
  - DELETE /drafts/{id}

#### День 36-37: Редактирование заявок
- [ ] **DRAFT-006**: Ozon API методы для редактирования
  - Изменение состава
  - Изменение количества
- [ ] **DRAFT-007**: Бот: редактирование
  - Выбор заявки
  - Изменение позиций
  - Подтверждение
- [ ] **DRAFT-008**: Шаблоны поставок
  - Сохранение часто используемых составов
  - Быстрое создание по шаблону

### Week 12: Smart Features

#### День 38-39: Умное перебронирование
- [ ] **SMART-001**: RebookingService
  - Поиск более выгодных слотов
  - Критерии: дата, стоимость, удобство
- [ ] **SMART-002**: Уведомления о лучших вариантах
  - "Найден более выгодный слот"
  - Предложение перебронировать
- [ ] **SMART-003**: Автоматическое перебронирование (опция)
  - Только для Business плана
  - Настройка критериев

#### День 40-41: Прогнозирование
- [ ] **PRED-001**: Сбор исторических данных
  - Агрегация данных о доступности
- [ ] **PRED-002**: Простая модель прогнозирования
  - На основе исторических паттернов
  - По дням недели и времени суток
- [ ] **PRED-003**: Отображение прогноза
  - В боте: вероятность появления слотов
  - На веб: графики прогноза

---

## Sprint 7: Integrations & Scaling (2 недели)

### Week 13: Webhook & API

#### День 42-43: Webhook система
- [ ] **HOOK-001**: Webhook подписки в БД
- [ ] **HOOK-002**: API endpoints
  - POST /webhooks
  - GET /webhooks
  - DELETE /webhooks/{id}
- [ ] **HOOK-003**: WebhookService
  - Отправка событий
  - Retry механизм
  - Signature verification
- [ ] **HOOK-004**: Бот: управление webhooks
  - Настройка через команды
- [ ] **HOOK-005**: Документация по webhook events

#### День 44-45: Public API
- [ ] **PAPI-001**: API keys management
  - Генерация ключей
  - Управление scopes
  - Ротация ключей
- [ ] **PAPI-002**: API documentation
  - Swagger UI
  - Code examples (Python, JS, cURL)
- [ ] **PAPI-003**: SDK для разработчиков (Python)
  - Обертка над API
  - Примеры использования

### Week 14: Scaling & Optimization

#### День 46-47: Performance
- [ ] **PERF-001**: Database query optimization
  - Анализ slow queries
  - Добавление индексов
  - Query optimization
- [ ] **PERF-002**: Redis caching strategy
  - Cache frequently accessed data
  - Cache invalidation
- [ ] **PERF-003**: Celery optimization
  - Task prefetch optimization
  - Worker autoscaling
- [ ] **PERF-004**: Connection pooling
  - PostgreSQL connection pool
  - Redis connection pool

#### День 48-49: Reliability
- [ ] **REL-001**: Graceful shutdown
  - Handle SIGTERM
  - Finish running tasks
- [ ] **REL-002**: Circuit breaker для Ozon API
  - Предотвращение каскадных ошибок
- [ ] **REL-003**: Backup strategy
  - Automated database backups
  - Restore procedures
- [ ] **REL-004**: Disaster recovery plan
  - Documentation
  - Runbooks

---

## Sprint 8: Wildberries Support (2-3 недели)

### Week 15-16: WB Integration
- [ ] **WB-001**: Wildberries API client
- [ ] **WB-002**: Адаптация моделей данных
  - Multi-marketplace support
- [ ] **WB-003**: WB мониторинг слотов
- [ ] **WB-004**: Единый интерфейс в боте
  - Выбор маркетплейса
  - Переключение между магазинами
- [ ] **WB-005**: Кросс-платформенная аналитика
- [ ] **WB-006**: Тестирование

### Week 17: Multi-marketplace Features
- [ ] **MM-001**: Сравнение доступности слотов
  - Ozon vs Wildberries
- [ ] **MM-002**: Рекомендации по выбору маркетплейса
- [ ] **MM-003**: Единый календарь поставок

---

## Sprint 9: Mobile App (4-6 недель)

### Week 18-20: React Native App
- [ ] **MOB-001**: Инициализация RN проекта
  - Expo или bare RN
- [ ] **MOB-002**: Аутентификация
- [ ] **MOB-003**: Core screens
  - Dashboard
  - Slots list
  - Settings
- [ ] **MOB-004**: Push notifications
  - Firebase Cloud Messaging
  - Notification handlers
- [ ] **MOB-005**: Offline mode
  - Local storage
  - Sync when online

### Week 21-23: Advanced Mobile Features
- [ ] **MOB-006**: Widgets (iOS & Android)
  - Quick stats
  - Recent slots
- [ ] **MOB-007**: Deep linking
  - Open slot details from notification
- [ ] **MOB-008**: Biometric authentication
- [ ] **MOB-009**: App Store & Google Play submission
- [ ] **MOB-010**: Beta testing (TestFlight, Play Console)

---

## Sprint 10: AI/ML Features (3-4 недели)

### Week 24-25: Data Collection & Preparation
- [ ] **ML-001**: Расширенный сбор данных
  - Все проверки слотов (не только новые)
  - Метаданные (погода, праздники, etc.)
- [ ] **ML-002**: Data pipeline
  - ETL процесс
  - Feature engineering
- [ ] **ML-003**: Exploratory Data Analysis
  - Паттерны доступности
  - Корреляции

### Week 26-27: ML Models
- [ ] **ML-004**: Модель прогнозирования доступности
  - Time series forecasting
  - LSTM или Prophet
- [ ] **ML-005**: Рекомендательная система
  - Оптимальное время для поставок
  - Выбор склада
- [ ] **ML-006**: Интеграция в API
  - Endpoint для прогнозов
  - Realtime inference
- [ ] **ML-007**: A/B тестирование рекомендаций

---

## Continuous Tasks (На протяжении всего проекта)

### Documentation
- [ ] **DOC-001**: API documentation (Swagger/OpenAPI)
- [ ] **DOC-002**: User guide (для бота)
- [ ] **DOC-003**: Developer documentation
- [ ] **DOC-004**: Architecture documentation
- [ ] **DOC-005**: Deployment guide

### Testing
- [ ] **TEST-001**: Unit tests (80%+ coverage)
- [ ] **TEST-002**: Integration tests
- [ ] **TEST-003**: E2E tests
- [ ] **TEST-004**: Load testing
- [ ] **TEST-005**: Security testing

### DevOps
- [ ] **OPS-001**: CI/CD pipeline
- [ ] **OPS-002**: Monitoring & Alerting
- [ ] **OPS-003**: Logging
- [ ] **OPS-004**: Backup & Recovery
- [ ] **OPS-005**: Infrastructure as Code (Terraform)

### Security
- [ ] **SEC-001**: Security audit
- [ ] **SEC-002**: Penetration testing
- [ ] **SEC-003**: GDPR compliance
- [ ] **SEC-004**: Data encryption
- [ ] **SEC-005**: Rate limiting

---

## Release Schedule

### MVP Release (Конец Sprint 3) - ~6 недель
**Функционал:**
- Telegram бот с регистрацией
- Мониторинг слотов
- Уведомления
- Базовые настройки
- Telegram Stars подписка
- Пробный период 7 дней

**Тарифы:**
- Free (trial): 7 дней
- Standard: 500 Stars/мес

### v1.0 Release (Конец Sprint 5) - ~10 недель
**Добавлено:**
- Web интерфейс
- Расширенная аналитика
- Admin panel
- API endpoints
- Несколько магазинов

**Тарифы:**
- Free (trial)
- Standard: 500 Stars
- Pro: 1000 Stars

### v2.0 Release (Конец Sprint 7) - ~14 недель
**Добавлено:**
- Черновики поставок
- Редактирование заявок
- Умное перебронирование
- Webhooks
- Public API

**Тарифы:**
- Free, Standard, Pro
- Business: 2500 Stars (с API и webhooks)

### v3.0 Release (Конец Sprint 9) - ~23 недели
**Добавлено:**
- Wildberries поддержка
- Mobile app (iOS & Android)
- Кросс-платформенная аналитика

### v4.0 Release (Конец Sprint 10) - ~27 недель
**Добавлено:**
- AI/ML прогнозирование
- Рекомендательная система
- Advanced analytics

---

## Метрики успеха по спринтам

### Sprint 1-3 (MVP)
- ✅ 50+ beta testers
- ✅ 90%+ регистраций завершены успешно
- ✅ <5% error rate в мониторинге
- ✅ <1s задержка уведомлений

### Sprint 4-5 (v1.0)
- ✅ 200+ активных пользователей
- ✅ 30%+ конверсия trial → paid
- ✅ NPS > 40
- ✅ 70%+ retention через месяц

### Sprint 6-7 (v2.0)
- ✅ 500+ активных пользователей
- ✅ 10+ API integration partners
- ✅ <200ms API response time (p95)

### Sprint 8-9 (v3.0)
- ✅ 1000+ активных пользователей
- ✅ 50%+ на mobile app
- ✅ Поддержка 2 маркетплейсов

### Sprint 10 (v4.0)
- ✅ 2000+ активных пользователей
- ✅ 75%+ accuracy в прогнозах
- ✅ Выход в прибыль

---

## Приоритеты для команды разных размеров

### Solo Developer (1 человек)
**Фокус:** MVP за 8-10 недель
- Sprint 1-3 полностью
- Упростить UI (только Telegram, без web)
- Минимальная аналитика
- Telegram Stars только

### Small Team (2-3 человека)
**Фокус:** v1.0 за 10-12 недель
- Sprint 1-5
- Backend + Bot + Basic Web
- Распределение:
  - Dev 1: Backend + API
  - Dev 2: Bot + Workers
  - Dev 3: Frontend (если есть)

### Medium Team (4-6 человек)
**Фокус:** v2.0 за 14-16 недель
- Sprint 1-7
- Полный функционал
- Распределение:
  - 2x Backend
  - 1x Bot
  - 2x Frontend
  - 1x DevOps

### Large Team (7+ человек)
**Фокус:** v3.0-4.0 за 20-25 недель
- Все спринты параллельно
- Специализированные роли:
  - Backend team
  - Frontend team
  - Mobile team
  - ML/AI team
  - DevOps/SRE
  - QA engineer
  - Product manager

---

## Риски и митигация

### Технические риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Изменения Ozon API | Высокая | Критическое | Мониторинг API, версионирование, быстрая реакция |
| Блокировка пользователей | Средняя | Высокое | Rate limiting, предупреждения, no-autobook в MVP |
| Проблемы с масштабированием | Средняя | Среднее | Нагрузочное тестирование, horizontal scaling |
| Data loss | Низкая | Критическое | Регулярные backups, репликация |

### Бизнес риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Низкий спрос | Средняя | Критическое | MVP validation, market research, beta testing |
| Высокая конкуренция | Высокая | Среднее | Уникальные фичи, лучший UX, competitive pricing |
| Юридические проблемы | Низкая | Высокое | Консультация с юристом, ToS, Privacy Policy |
| Высокие затраты на инфраструктуру | Средняя | Среднее | Оптимизация, auto-scaling, cost monitoring |

---

# Заключение

Этот техдизайн и roadmap предоставляют полный план разработки от MVP до полнофункционального продукта с AI/ML возможностями.

**Рекомендация для старта:**
1. Начать с MVP (Sprint 1-3) - 6 недель
2. Получить обратную связь от real users
3. Итерировать на основе feedback
4. Постепенно добавлять advanced features

**Ключевые принципы:**
- ✅ Start small, iterate fast
- ✅ User feedback driven development
- ✅ Security & reliability first
- ✅ Measure everything
- ✅ Automated testing & deployment
