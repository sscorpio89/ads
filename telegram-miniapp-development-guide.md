# Руководство по разработке Telegram Mini App

## Содержание

1. [Что такое Telegram Mini App](#что-такое-telegram-mini-app)
2. [Этапы разработки](#этапы-разработки)
3. [Технологический стек](#технологический-стек)
4. [Архитектура приложения](#архитектура-приложения)
5. [Интеграция с Telegram](#интеграция-с-telegram)
6. [Примеры реализации](#примеры-реализации)
7. [Deployment и хостинг](#deployment-и-хостинг)

---

## Что такое Telegram Mini App

**Telegram Mini App** (ранее Web App) — это веб-приложения, которые запускаются внутри Telegram с использованием встроенного браузера. Они предоставляют полноценный графический интерфейс, в отличие от традиционных ботов с кнопками и командами.

### Ключевые особенности

- **Полноценный UI/UX**: Возможность использовать современные веб-технологии (React, Vue, Angular)
- **Нативная интеграция**: Доступ к API Telegram (данные пользователя, платежи, haptic feedback)
- **Кроссплатформенность**: Работает на iOS, Android, Desktop, Web
- **Безопасность**: Автоматическая авторизация через Telegram
- **Монетизация**: Встроенные платежи через Telegram Stars

### Отличия от обычного бота

| Характеристика | Обычный бот | Mini App |
|----------------|-------------|----------|
| **Интерфейс** | Кнопки, inline клавиатуры | Полноценный веб-интерфейс |
| **UX** | Ограниченный | Как нативное приложение |
| **Разработка** | Python/Node.js + Bot API | Frontend + Backend + Bot API |
| **Сложность** | Низкая | Средняя-высокая |
| **Возможности** | Текст, кнопки, медиа | Графика, анимации, формы, charts |

---

## Этапы разработки

### Фаза 1: Подготовка и планирование (1-2 недели)

#### 1.1. Определение требований

- Анализ функциональных требований
- Разработка user flow и wireframes
- Определение MVP функционала
- Выбор технологического стека

#### 1.2. Проектирование архитектуры

- Проектирование базы данных
- API эндпоинты
- Схема взаимодействия Frontend ↔ Backend ↔ Telegram
- Security модель

#### 1.3. Настройка окружения

- Создание бота через [@BotFather](https://t.me/BotFather)
- Настройка репозитория (Git)
- Настройка CI/CD pipeline
- Выбор хостинга

### Фаза 2: Backend разработка (2-3 недели)

#### 2.1. Создание Telegram бота

```python
# Пример с aiogram 3.x
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo

bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Кнопка для запуска Mini App
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url="https://your-app.com")
            )]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать! Нажмите кнопку ниже:",
        reply_markup=kb
    )
```

#### 2.2. REST API для Mini App

```python
# FastAPI пример
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS для Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InitData(BaseModel):
    user_id: int
    username: str
    auth_date: int
    hash: str

@app.post("/api/auth")
async def authenticate(init_data: InitData):
    # Валидация данных от Telegram
    if validate_telegram_data(init_data):
        # Создание JWT токена
        token = create_access_token(user_id=init_data.user_id)
        return {"token": token, "user": get_user_data(init_data.user_id)}
    raise HTTPException(status_code=401, detail="Invalid data")

@app.get("/api/slots")
async def get_available_slots(warehouse_id: int, user_id: int):
    # Интеграция с Ozon API
    slots = await fetch_ozon_slots(warehouse_id, user_id)
    return {"slots": slots}
```

#### 2.3. База данных

```sql
-- PostgreSQL схема
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    ozon_client_id VARCHAR(255),
    ozon_api_key_encrypted TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE monitoring_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    warehouse_ids INTEGER[],
    date_from DATE,
    date_to DATE,
    delivery_type VARCHAR(50),
    min_limit INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    slot_id VARCHAR(255),
    warehouse_id INTEGER,
    slot_date TIMESTAMP,
    status VARCHAR(50), -- pending, confirmed, cancelled
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Фаза 3: Frontend разработка (3-4 недели)

#### 3.1. Выбор фреймворка

**Рекомендуемые варианты:**

1. **React + TypeScript** (наиболее популярный)
2. **Vue 3 + TypeScript**
3. **Svelte** (легковесный)
4. **Next.js** (для SSR/SEO)

#### 3.2. Интеграция Telegram Web App SDK

```typescript
// React компонент с Telegram SDK
import { useEffect, useState } from 'react';

// Подключение SDK
declare global {
  interface Window {
    Telegram: any;
  }
}

const App = () => {
  const [tg] = useState(window.Telegram.WebApp);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Инициализация приложения
    tg.ready();

    // Расширение на весь экран
    tg.expand();

    // Настройка цветовой схемы
    tg.setHeaderColor('#2481cc');
    tg.setBackgroundColor('#ffffff');

    // Получение данных пользователя
    const initDataUnsafe = tg.initDataUnsafe;
    if (initDataUnsafe.user) {
      setUser(initDataUnsafe.user);
      authenticateUser(tg.initData);
    }
  }, []);

  const authenticateUser = async (initData: string) => {
    const response = await fetch('https://your-api.com/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData })
    });
    const data = await response.json();
    localStorage.setItem('token', data.token);
  };

  return (
    <div className="app">
      <h1>Привет, {user?.first_name}!</h1>
      {/* Остальной UI */}
    </div>
  );
};

export default App;
```

#### 3.3. Структура проекта (React + Vite)

```
telegram-miniapp-frontend/
├── public/
│   └── index.html (с подключением Telegram SDK)
├── src/
│   ├── components/
│   │   ├── SlotList.tsx
│   │   ├── BookingForm.tsx
│   │   ├── Settings.tsx
│   │   └── Analytics.tsx
│   ├── hooks/
│   │   ├── useTelegram.ts
│   │   └── useOzonApi.ts
│   ├── services/
│   │   ├── api.ts
│   │   └── telegram.ts
│   ├── store/
│   │   └── index.ts (Redux/Zustand)
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
└── vite.config.ts
```

#### 3.4. Пример главного экрана

```tsx
// SlotList.tsx
import React, { useEffect, useState } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { fetchSlots, bookSlot } from '../services/api';

interface Slot {
  id: string;
  warehouse: string;
  date: string;
  time: string;
  limit: number;
  available: boolean;
}

const SlotList: React.FC = () => {
  const { tg, user } = useTelegram();
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSlots();
  }, []);

  const loadSlots = async () => {
    try {
      const data = await fetchSlots(user.id);
      setSlots(data);
    } catch (error) {
      tg.showAlert('Ошибка загрузки слотов');
    } finally {
      setLoading(false);
    }
  };

  const handleBook = async (slotId: string) => {
    tg.showConfirm('Забронировать этот слот?', async (confirmed) => {
      if (confirmed) {
        try {
          await bookSlot(slotId);
          tg.showPopup({
            title: 'Успех!',
            message: 'Слот успешно забронирован',
            buttons: [{ type: 'ok' }]
          });
          tg.HapticFeedback.notificationOccurred('success');
          loadSlots(); // Обновить список
        } catch (error) {
          tg.showAlert('Ошибка бронирования');
          tg.HapticFeedback.notificationOccurred('error');
        }
      }
    });
  };

  if (loading) {
    return <div className="loader">Загрузка...</div>;
  }

  return (
    <div className="slot-list">
      <h2>Доступные слоты</h2>
      {slots.map(slot => (
        <div key={slot.id} className="slot-card">
          <div className="slot-info">
            <h3>{slot.warehouse}</h3>
            <p>{slot.date} в {slot.time}</p>
            <p>Лимит: {slot.limit} единиц</p>
          </div>
          <button
            onClick={() => handleBook(slot.id)}
            disabled={!slot.available}
            className="book-button"
          >
            {slot.available ? 'Забронировать' : 'Недоступен'}
          </button>
        </div>
      ))}
    </div>
  );
};

export default SlotList;
```

### Фаза 4: Интеграция и тестирование (1-2 недели)

#### 4.1. Валидация данных от Telegram

```python
# Валидация initData (Python)
import hmac
import hashlib
from urllib.parse import parse_qs

def validate_telegram_init_data(init_data: str, bot_token: str) -> bool:
    try:
        parsed_data = parse_qs(init_data)
        hash_value = parsed_data.get('hash', [None])[0]

        if not hash_value:
            return False

        # Удаляем hash из данных
        data_check_string = '\n'.join(
            f"{k}={v[0]}" for k, v in sorted(parsed_data.items())
            if k != 'hash'
        )

        # Создаем секретный ключ
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return calculated_hash == hash_value
    except Exception:
        return False
```

#### 4.2. Тестирование

- **Unit тесты**: Backend API, бизнес-логика
- **E2E тесты**: Playwright/Cypress для frontend
- **Telegram тестирование**: Использование test environment
- **Нагрузочное тестирование**: k6, Locust

### Фаза 5: Deployment (1 неделя)

#### 5.1. Frontend (Static hosting)

**Варианты хостинга:**
- Vercel (рекомендуется для Next.js)
- Netlify
- Cloudflare Pages
- GitHub Pages (только для статических сайтов)
- AWS S3 + CloudFront

```bash
# Пример деплоя на Vercel
npm install -g vercel
vercel --prod
```

#### 5.2. Backend (Containerized)

```dockerfile
# Dockerfile для FastAPI
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/miniapp
      - REDIS_URL=redis://redis:6379
      - BOT_TOKEN=${BOT_TOKEN}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: miniapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl

volumes:
  postgres_data:
  redis_data:
```

---

## Технологический стек

### Рекомендуемый стек для Mini App

#### Frontend

| Технология | Назначение | Альтернативы |
|------------|-----------|--------------|
| **React 18+** | UI библиотека | Vue 3, Svelte, Angular |
| **TypeScript** | Type safety | JavaScript |
| **Vite** | Build tool | Webpack, Parcel |
| **TanStack Query** | Data fetching | SWR, Apollo Client |
| **Zustand / Redux Toolkit** | State management | MobX, Recoil |
| **React Router** | Routing | TanStack Router |
| **Tailwind CSS** | Styling | Styled Components, MUI |
| **Telegram UI Kit** | UI components | Собственные компоненты |
| **@twa-dev/sdk** | Telegram SDK | Vanilla Telegram WebApp API |

#### Backend

| Технология | Назначение | Альтернативы |
|------------|-----------|--------------|
| **Python 3.11+** | Язык программирования | Node.js, Go, Rust |
| **FastAPI** | Web framework | Flask, Django, Express |
| **aiogram 3.x** | Telegram Bot API | python-telegram-bot |
| **SQLAlchemy 2.0** | ORM | Prisma (Node.js), GORM (Go) |
| **PostgreSQL 15** | База данных | MySQL, MongoDB |
| **Redis 7** | Cache & Sessions | Memcached |
| **Celery** | Background tasks | Dramatiq, RQ |
| **Pydantic** | Data validation | marshmallow |

#### DevOps & Infrastructure

| Технология | Назначение |
|------------|-----------|
| **Docker & Docker Compose** | Контейнеризация |
| **Nginx** | Reverse proxy & SSL |
| **GitHub Actions** | CI/CD |
| **Sentry** | Error tracking |
| **Prometheus + Grafana** | Monitoring |
| **Let's Encrypt** | SSL сертификаты |

---

## Архитектура приложения

### Общая схема

```
┌─────────────────────────────────────────────────────────┐
│                   TELEGRAM CLIENT                        │
│              (iOS / Android / Desktop / Web)             │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 MINI APP FRONTEND                        │
│                 (React + TypeScript)                     │
│                                                          │
│  • Telegram WebApp SDK integration                      │
│  • UI Components (Slot list, booking form, settings)   │
│  • State Management (Zustand/Redux)                     │
│  • API Client (Axios/Fetch)                             │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ REST API (HTTPS)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  API GATEWAY (Nginx)                     │
│              SSL Termination, Rate Limiting              │
└───────────┬──────────────────────────┬──────────────────┘
            │                          │
            ▼                          ▼
┌──────────────────────┐    ┌──────────────────────┐
│   BACKEND (FastAPI)  │    │  TELEGRAM BOT        │
│                      │    │  (aiogram)           │
│ • REST API           │◄───┤                      │
│ • Authentication     │    │ • Bot commands       │
│ • Business Logic     │    │ • Notifications      │
│ • Ozon API Client    │    │ • Deep links         │
└──────────┬───────────┘    └──────────────────────┘
           │                          ▲
           │                          │
           │                          │ Webhook
           │                          │
           ▼                          │
┌──────────────────────┐    ┌──────────────────────┐
│    PostgreSQL        │    │  Telegram Bot API    │
│                      │    └──────────────────────┘
│ • Users              │
│ • Settings           │              ▲
│ • Bookings           │              │
│ • History            │              │
└──────────────────────┘              │
           │                          │
           │                ┌─────────┴─────────┐
           ▼                │                   │
┌──────────────────────┐    │  External APIs   │
│       Redis          │    │                   │
│                      │    │ • Ozon Seller API │
│ • Session Store      │    │ • Payment APIs    │
│ • Cache              │    └───────────────────┘
│ • Rate Limiting      │
│ • Celery Queue       │
└──────────────────────┘
           │
           ▼
┌──────────────────────┐
│  Celery Workers      │
│                      │
│ • Slot monitoring    │
│ • Notifications      │
│ • Analytics          │
└──────────────────────┘
```

---

## Интеграция с Telegram

### 1. Создание Mini App через BotFather

```
1. Открыть @BotFather в Telegram
2. Создать бота: /newbot
3. Получить токен бота
4. Настроить Mini App: /newapp
5. Указать URL приложения (HTTPS обязателен!)
6. Загрузить иконку и скриншоты
7. Указать короткое название (для ссылок)
```

### 2. Telegram WebApp API методы

```typescript
// Основные методы Telegram WebApp
const tg = window.Telegram.WebApp;

// Инициализация
tg.ready();

// Расширение на весь экран
tg.expand();

// Данные пользователя
const user = tg.initDataUnsafe.user;
// { id, first_name, last_name, username, language_code }

// Тема оформления
const theme = tg.themeParams;
// { bg_color, text_color, hint_color, link_color, button_color, ... }

// Haptic feedback (вибрация)
tg.HapticFeedback.impactOccurred('light'); // light, medium, heavy
tg.HapticFeedback.notificationOccurred('success'); // success, warning, error
tg.HapticFeedback.selectionChanged();

// Main Button (кнопка внизу экрана)
tg.MainButton.setText('Забронировать слот');
tg.MainButton.show();
tg.MainButton.onClick(() => {
  // Обработка нажатия
});

// Back Button
tg.BackButton.show();
tg.BackButton.onClick(() => {
  // Возврат назад
});

// Popup и Alert
tg.showPopup({
  title: 'Заголовок',
  message: 'Сообщение',
  buttons: [
    { id: 'ok', type: 'ok', text: 'ОК' },
    { id: 'cancel', type: 'cancel' }
  ]
}, (buttonId) => {
  console.log('Нажата кнопка:', buttonId);
});

tg.showAlert('Простое сообщение');

tg.showConfirm('Вы уверены?', (confirmed) => {
  if (confirmed) {
    // Действие подтверждено
  }
});

// Закрытие Mini App
tg.close();

// Открытие ссылки
tg.openLink('https://example.com');

// Открытие Telegram ссылки
tg.openTelegramLink('https://t.me/username');

// Отправка данных боту
tg.sendData(JSON.stringify({ action: 'book', slotId: 123 }));

// CloudStorage (хранилище данных)
tg.CloudStorage.setItem('key', 'value', (error, success) => {
  if (success) console.log('Сохранено');
});

tg.CloudStorage.getItem('key', (error, value) => {
  console.log('Значение:', value);
});

// Настройка цветов
tg.setHeaderColor('#2481cc');
tg.setBackgroundColor('#ffffff');
```

### 3. Кастомный хук для React

```typescript
// hooks/useTelegram.ts
import { useEffect, useState } from 'react';

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
}

export const useTelegram = () => {
  const [tg] = useState(() => window.Telegram.WebApp);
  const [user, setUser] = useState<TelegramUser | null>(null);

  useEffect(() => {
    tg.ready();
    tg.expand();

    if (tg.initDataUnsafe?.user) {
      setUser(tg.initDataUnsafe.user);
    }

    // Применение темы Telegram
    document.documentElement.style.setProperty(
      '--tg-theme-bg-color',
      tg.themeParams.bg_color || '#ffffff'
    );
    document.documentElement.style.setProperty(
      '--tg-theme-text-color',
      tg.themeParams.text_color || '#000000'
    );
  }, [tg]);

  const showMainButton = (text: string, onClick: () => void) => {
    tg.MainButton.setText(text);
    tg.MainButton.show();
    tg.MainButton.onClick(onClick);
  };

  const hideMainButton = () => {
    tg.MainButton.hide();
  };

  const hapticFeedback = (type: 'light' | 'medium' | 'heavy') => {
    tg.HapticFeedback.impactOccurred(type);
  };

  return {
    tg,
    user,
    showMainButton,
    hideMainButton,
    hapticFeedback,
    theme: tg.themeParams,
    isReady: !!user,
  };
};
```

---

## Примеры реализации

### Пример 1: Страница бронирования слота

```tsx
// pages/BookingPage.tsx
import React, { useState, useEffect } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { bookSlot } from '../services/api';

interface Slot {
  id: string;
  warehouse_name: string;
  date: string;
  time_from: string;
  time_to: string;
  limit: number;
}

const BookingPage: React.FC<{ slot: Slot }> = ({ slot }) => {
  const { tg, showMainButton, hideMainButton, hapticFeedback } = useTelegram();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    showMainButton('Забронировать', handleBook);
    return () => hideMainButton();
  }, []);

  const handleBook = async () => {
    hapticFeedback('medium');

    tg.showConfirm(
      `Забронировать слот на ${slot.date} с ${slot.time_from} до ${slot.time_to}?`,
      async (confirmed) => {
        if (confirmed) {
          setLoading(true);
          try {
            await bookSlot(slot.id);
            hapticFeedback('heavy');
            tg.showPopup({
              title: '✅ Успешно!',
              message: 'Слот забронирован',
              buttons: [{ type: 'ok' }]
            });
            tg.close();
          } catch (error) {
            tg.showAlert('❌ Ошибка бронирования. Попробуйте снова.');
          } finally {
            setLoading(false);
          }
        }
      }
    );
  };

  return (
    <div className="booking-page">
      <div className="slot-card">
        <h2>{slot.warehouse_name}</h2>
        <div className="slot-details">
          <p><strong>Дата:</strong> {slot.date}</p>
          <p><strong>Время:</strong> {slot.time_from} - {slot.time_to}</p>
          <p><strong>Лимит приёмки:</strong> {slot.limit} единиц</p>
        </div>
      </div>
      {loading && <div className="loader">Бронирование...</div>}
    </div>
  );
};

export default BookingPage;
```

### Пример 2: Интеграция платежей (Telegram Stars)

```typescript
// services/payments.ts
export const initPayment = async (amount: number, description: string) => {
  const tg = window.Telegram.WebApp;

  // Создание invoice на бэкенде
  const response = await fetch('/api/create-invoice', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, description })
  });

  const { invoice_link } = await response.json();

  // Открытие формы оплаты
  tg.openInvoice(invoice_link, (status) => {
    if (status === 'paid') {
      tg.showPopup({
        title: 'Оплата успешна!',
        message: 'Подписка активирована',
        buttons: [{ type: 'ok' }]
      });
    } else if (status === 'failed') {
      tg.showAlert('Ошибка оплаты');
    }
  });
};
```

```python
# backend/payments.py
from aiogram import types

async def create_invoice(user_id: int, amount: int, description: str):
    """Создание invoice для оплаты в Telegram"""
    prices = [types.LabeledPrice(label=description, amount=amount * 100)]

    invoice_link = await bot.create_invoice_link(
        title="Подписка Pro",
        description=description,
        payload=f"user_{user_id}_subscription",
        provider_token="",  # Пустой для Telegram Stars
        currency="XTR",  # Telegram Stars
        prices=prices
    )

    return invoice_link
```

---

## Deployment и хостинг

### Требования к хостингу

1. **HTTPS обязателен** - Telegram требует SSL
2. **Домен** - Нужен собственный домен
3. **SSL сертификат** - Let's Encrypt или платный
4. **Низкая latency** - Для лучшего UX

### Варианты хостинга

#### Frontend

**Vercel (рекомендуется)**
```bash
# vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Cloudflare Pages**
- Бесплатный SSL
- CDN по всему миру
- Unlimited bandwidth

**Netlify**
- Простой деплой из Git
- Автоматический SSL
- Preview deploys

#### Backend

**DigitalOcean App Platform**
```yaml
# .do/app.yaml
name: miniapp-backend
services:
  - name: api
    source:
      repo: github.com/username/repo
      branch: main
    dockerfile_path: Dockerfile
    http_port: 8000
    envs:
      - key: DATABASE_URL
        scope: RUN_AND_BUILD_TIME
        type: SECRET
```

**Railway**
- Автодеплой из GitHub
- Managed PostgreSQL
- Простая настройка

**AWS ECS / Google Cloud Run**
- Для масштабируемых проектов
- Автоскейлинг
- Pay-per-use

### SSL сертификат (Let's Encrypt)

```bash
# Установка certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Автообновление
sudo certbot renew --dry-run
```

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name your-miniapp.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-miniapp.com;

    ssl_certificate /etc/letsencrypt/live/your-miniapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-miniapp.com/privkey.pem;

    # Frontend (Static files)
    location / {
        root /var/www/miniapp/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Best Practices

### Безопасность

1. **Всегда валидировать initData** от Telegram
2. **Использовать HTTPS** для всех запросов
3. **Шифровать чувствительные данные** (API ключи пользователей)
4. **Rate limiting** для защиты от DDoS
5. **CSP headers** для защиты от XSS

### Производительность

1. **Lazy loading** компонентов React
2. **Кэширование** API запросов (React Query)
3. **Code splitting** для уменьшения bundle size
4. **Оптимизация изображений** (WebP, lazy loading)
5. **CDN** для статических файлов

### UX

1. **Haptic feedback** при взаимодействиях
2. **Loading states** для всех асинхронных операций
3. **Поддержка темной темы** Telegram
4. **Адаптивный дизайн** под все устройства
5. **MainButton** для основного действия

### Тестирование

1. **Тестирование в разных клиентах** (iOS, Android, Desktop, Web)
2. **Разные версии Telegram** (официальная, unofficial)
3. **Светлая и темная темы**
4. **Разные языки интерфейса**

---

## Полезные ресурсы

### Официальная документация

- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)
- [Bot API Documentation](https://core.telegram.org/bots/api)
- [Telegram WebApp JS SDK](https://github.com/twa-dev/SDK)

### Библиотеки и инструменты

- [@twa-dev/sdk](https://www.npmjs.com/package/@twa-dev/sdk) - TypeScript SDK
- [twa-dev/boilerplate](https://github.com/twa-dev/Boilerplate) - React boilerplate
- [Telegram UI Kit](https://github.com/telegram-mini-apps/telegram-ui) - UI компоненты

### Примеры проектов

- [Durger King Bot](https://t.me/DurgerKingBot) - Заказ еды
- [Wallet Pay](https://t.me/wallet) - Криптовалютный кошелек
- [Fragment](https://t.me/fragment) - Маркетплейс username

### Сообщества

- [Telegram Developers Chat](https://t.me/devs)
- [Mini Apps Developers](https://t.me/miniapps_dev)
- [aiogram Community](https://t.me/aiogram_en)

---

## Чеклист запуска Mini App

### Перед запуском

- [ ] Создан бот через @BotFather
- [ ] Настроен Mini App через @BotFather
- [ ] Получен SSL сертификат (HTTPS)
- [ ] Настроен домен
- [ ] Валидация initData работает корректно
- [ ] Backend API защищен аутентификацией
- [ ] Тестирование на всех платформах (iOS, Android, Desktop, Web)
- [ ] Настроены analytics (Amplitude, Mixpanel)
- [ ] Настроен error tracking (Sentry)
- [ ] Подготовлены иконки и скриншоты
- [ ] Написана документация для пользователей
- [ ] Настроен мониторинг (Grafana, Prometheus)
- [ ] Load testing пройден успешно
- [ ] Backup стратегия настроена
- [ ] CI/CD pipeline работает

### После запуска

- [ ] Мониторинг ошибок в Sentry
- [ ] Отслеживание метрик (DAU, retention)
- [ ] Сбор feedback от пользователей
- [ ] A/B тестирование ключевых функций
- [ ] Регулярные обновления и багфиксы
- [ ] Масштабирование при росте пользователей

---

## Заключение

Разработка Telegram Mini App — это сочетание классической веб-разработки с уникальными возможностями экосистемы Telegram. Следуя этому руководству, вы сможете создать полноценное приложение, которое будет работать на всех платформах Telegram.

**Ключевые преимущества Mini App:**
- Не требует установки из App Store/Google Play
- Мгновенный доступ через Telegram
- Встроенная аутентификация
- Нативная интеграция с Telegram функциями
- Быстрое распространение через ссылки

**Следующие шаги:**
1. Создайте прототип за 1-2 недели
2. Соберите feedback от первых пользователей
3. Итерируйте на основе данных
4. Масштабируйте при росте

Удачи в разработке! 🚀
