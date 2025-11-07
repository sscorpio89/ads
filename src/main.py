"""
Главный файл приложения для Telegram Mini App.

Запускает FastAPI сервер с API для работы с заявками на поставку FBO.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .handlers.supply_handlers import router as supply_router
from .handlers.shop_handlers import router as shop_router
from .config.settings import settings


# Настройка логирования
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Создание FastAPI приложения
app = FastAPI(
    title="Ozon FBO Supply Bot API",
    description="API для управления заявками на поставку FBO через Telegram Mini App",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# CORS middleware для Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение роутеров
app.include_router(supply_router)
app.include_router(shop_router)


# Статические файлы для Telegram Mini App
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница Telegram Mini App."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ozon FBO Supply Manager</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: var(--tg-theme-bg-color, #ffffff);
                color: var(--tg-theme-text-color, #000000);
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            h1 {
                font-size: 24px;
                margin-bottom: 20px;
                color: var(--tg-theme-text-color);
            }
            .card {
                background: var(--tg-theme-secondary-bg-color, #f5f5f5);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
            }
            .button {
                background: var(--tg-theme-button-color, #3390ec);
                color: var(--tg-theme-button-text-color, #ffffff);
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                margin-top: 8px;
            }
            .button:hover {
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚚 Управление поставками Ozon FBO</h1>

            <div class="card">
                <h3>🏪 Мои магазины</h3>
                <p>Добавьте и управляйте магазинами Ozon Seller</p>
                <button class="button" onclick="manageShops()">Управление магазинами</button>
            </div>

            <div class="card">
                <h3>Создать заявку на поставку</h3>
                <p>Создайте новую заявку на поставку товаров на склад Ozon</p>
                <button class="button" onclick="createSupply()">Создать заявку</button>
            </div>

            <div class="card">
                <h3>Мои заявки</h3>
                <p>Просмотрите и управляйте существующими заявками</p>
                <button class="button" onclick="viewSupplies()">Показать заявки</button>
            </div>

            <div class="card">
                <h3>Доступные слоты</h3>
                <p>Проверьте доступные временные слоты на складах</p>
                <button class="button" onclick="viewTimeslots()">Проверить слоты</button>
            </div>
        </div>

        <script>
            // Инициализация Telegram Web App
            const tg = window.Telegram.WebApp;
            tg.expand();

            // Установка цветовой схемы
            document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';

            function manageShops() {
                window.location.href = '/static/shops.html';
            }

            function createSupply() {
                // TODO: Открыть форму создания заявки
                tg.showAlert('Функция создания заявки в разработке');
            }

            function viewSupplies() {
                // TODO: Показать список заявок
                tg.showAlert('Функция просмотра заявок в разработке');
            }

            function viewTimeslots() {
                // TODO: Показать доступные слоты
                tg.showAlert('Функция просмотра слотов в разработке');
            }

            // Показываем MainButton
            tg.MainButton.text = "Обновить";
            tg.MainButton.show();
            tg.MainButton.onClick(() => {
                window.location.reload();
            });
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.env,
        "debug": settings.debug
    }


@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения."""
    logger.info("Starting Ozon FBO Supply Bot API")
    logger.info(f"Environment: {settings.env}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения."""
    logger.info("Shutting down Ozon FBO Supply Bot API")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.api_workers
    )
