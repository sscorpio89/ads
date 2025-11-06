@echo off
chcp 65001 > nul
title Транскрибация приватного видео (с cookies)

echo.
echo ========================================================
echo     ТРАНСКРИБАЦИЯ ПРИВАТНОГО ВИДЕО (С COOKIES)
echo ========================================================
echo.
echo  Этот скрипт скачивает приватное видео используя
echo  cookies из браузера и создает транскрибацию
echo.
echo ========================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Установите Python с https://www.python.org/downloads/
    echo При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python установлен
echo.

REM Проверка наличия cookies.txt
if not exist cookies.txt (
    echo ========================================================
    echo              ФАЙЛ COOKIES НЕ НАЙДЕН!
    echo ========================================================
    echo.
    echo Файл cookies.txt необходим для скачивания приватного видео.
    echo.
    echo ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ COOKIES:
    echo.
    echo ---- Для Google Chrome / Microsoft Edge: ----
    echo 1. Откройте Chrome Web Store
    echo 2. Найдите расширение "Get cookies.txt LOCALLY"
    echo 3. Установите расширение
    echo 4. Откройте страницу с видео в браузере
    echo 5. Нажмите на иконку расширения
    echo 6. Нажмите "Export"
    echo 7. Выберите "Only site" (только для rutube.ru)
    echo 8. Сохраните файл как cookies.txt
    echo 9. Поместите cookies.txt в папку с этим скриптом
    echo.
    echo ---- Для Firefox: ----
    echo 1. Откройте Firefox Add-ons
    echo 2. Найдите "cookies.txt"
    echo 3. Установите расширение
    echo 4. Откройте страницу с видео
    echo 5. Нажмите на иконку расширения
    echo 6. Сохраните как cookies.txt в папку со скриптом
    echo.
    echo ========================================================
    echo.
    echo Текущая папка: %CD%
    echo Поместите сюда файл cookies.txt и запустите скрипт снова
    echo.
    pause
    exit /b 1
)

echo [OK] Файл cookies.txt найден
echo.

REM Проверка зависимостей
echo Проверка библиотек...
pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo [!] Устанавливаю yt-dlp...
    pip install yt-dlp
)

pip show SpeechRecognition >nul 2>&1
if errorlevel 1 (
    echo [!] Устанавливаю SpeechRecognition...
    pip install SpeechRecognition
)

pip show pydub >nul 2>&1
if errorlevel 1 (
    echo [!] Устанавливаю pydub...
    pip install pydub
)

echo [OK] Все библиотеки установлены
echo.
echo ========================================================
echo.

REM Получение URL видео
if "%~1"=="" (
    echo Введите URL приватного видео:
    echo Пример: https://rutube.ru/video/private/xxxxx/?p=xxxxx
    echo.
    set /p VIDEO_URL="URL: "
) else (
    set VIDEO_URL=%~1
)

if "%VIDEO_URL%"=="" (
    echo.
    echo [ОШИБКА] URL не указан!
    pause
    exit /b 1
)

echo.
echo --------------------------------------------------------
echo  URL: %VIDEO_URL%
echo --------------------------------------------------------
echo.
echo [1/3] Скачивание видео...
echo       Используются cookies из cookies.txt
echo.
echo [2/3] Извлечение и конвертация аудио...
echo.
echo [3/3] Распознавание речи и создание HTML...
echo.
echo Это может занять продолжительное время (5-15 минут).
echo Пожалуйста, не закрывайте это окно!
echo.

REM Запуск транскрибации
python transcribe_with_cookies.py "%VIDEO_URL%"

if errorlevel 1 (
    echo.
    echo ========================================================
    echo                    ОШИБКА!
    echo ========================================================
    echo.
    echo Возможные причины:
    echo.
    echo 1. Cookies устарели
    echo    Решение: Экспортируйте cookies заново
    echo.
    echo 2. Нет доступа к видео
    echo    Решение: Откройте видео в браузере и проверьте доступ
    echo.
    echo 3. Проблемы с интернетом
    echo    Решение: Проверьте подключение
    echo.
    echo 4. Видео защищено DRM
    echo    Решение: Используйте встроенные средства записи экрана
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo                   УСПЕШНО! ✓
echo ========================================================
echo.
echo Транскрибация завершена!
echo HTML файл: transcription.html
echo.
echo Открыть в браузере?
echo.
choice /C YN /M "Открыть (Y/N)"
if errorlevel 2 goto end
if errorlevel 1 start transcription.html

:end
echo.
echo Готово!
echo.
pause
