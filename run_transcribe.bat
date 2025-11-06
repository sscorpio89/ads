@echo off
chcp 65001 > nul
title Транскрибация видео в HTML

echo.
echo ========================================================
echo            ТРАНСКРИБАЦИЯ ВИДЕО В HTML
echo ========================================================
echo.
echo  Этот скрипт преобразует видео/аудио в текст
echo  и создает красивый HTML файл с транскрибацией
echo.
echo ========================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста, установите Python:
    echo 1. Перейдите на https://www.python.org/downloads/
    echo 2. Скачайте последнюю версию
    echo 3. При установке поставьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python установлен
echo.

REM Проверка зависимостей
echo Проверка установленных библиотек...
pip show SpeechRecognition >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Библиотека SpeechRecognition не установлена
    echo Устанавливаю...
    pip install SpeechRecognition
)

pip show pydub >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Библиотека pydub не установлена
    echo Устанавливаю...
    pip install pydub
)

echo [OK] Все библиотеки установлены
echo.
echo ========================================================
echo.

REM Получение пути к файлу
if "%~1"=="" (
    echo СПОСОБ 1: Перетащите видео/аудио файл на этот .bat
    echo СПОСОБ 2: Введите путь к файлу ниже
    echo.
    set /p VIDEO_PATH="Путь к видео/аудио файлу: "
) else (
    set VIDEO_PATH=%~1
)

REM Проверка существования файла
if not exist "%VIDEO_PATH%" (
    echo.
    echo [ОШИБКА] Файл не найден: %VIDEO_PATH%
    echo.
    echo Убедитесь, что:
    echo - Путь указан правильно
    echo - Файл существует
    echo - Путь заключен в кавычки, если содержит пробелы
    echo.
    pause
    exit /b 1
)

echo.
echo --------------------------------------------------------
echo  Файл: %VIDEO_PATH%
echo --------------------------------------------------------
echo.
echo Начинаю обработку...
echo Это может занять несколько минут в зависимости от длительности видео.
echo.
echo [Статус] Конвертация аудио...
echo [Статус] Распознавание речи...
echo [Статус] Создание HTML...
echo.
echo Пожалуйста, подождите...
echo.

REM Запуск транскрибации
python transcribe_local_file.py "%VIDEO_PATH%"

if errorlevel 1 (
    echo.
    echo ========================================================
    echo                    ОШИБКА!
    echo ========================================================
    echo.
    echo Произошла ошибка при транскрибации.
    echo Возможные причины:
    echo - Файл поврежден или в неподдерживаемом формате
    echo - Нет подключения к интернету
    echo - Отсутствует аудио дорожка в видео
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo                   ГОТОВО! ✓
echo ========================================================
echo.
echo HTML файл создан: transcription.html
echo.
echo Открыть результат в браузере?
echo.
choice /C YN /M "Открыть (Y/N)"
if errorlevel 2 goto end
if errorlevel 1 start transcription.html

:end
echo.
echo Спасибо за использование!
echo.
pause
