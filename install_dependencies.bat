@echo off
chcp 65001 > nul
title Установка зависимостей для транскрибации

color 0A
echo.
echo ========================================================
echo         УСТАНОВКА ЗАВИСИМОСТЕЙ
echo ========================================================
echo.
echo  Этот скрипт установит все необходимые библиотеки
echo  для работы программы транскрибации видео
echo.
echo ========================================================
echo.

REM Проверка наличия Python
echo [Шаг 1/5] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo ╔════════════════════════════════════════════════════════╗
    echo ║              PYTHON НЕ УСТАНОВЛЕН!                     ║
    echo ╚════════════════════════════════════════════════════════╝
    echo.
    echo Для работы программы необходим Python 3.8 или выше.
    echo.
    echo ИНСТРУКЦИЯ ПО УСТАНОВКЕ:
    echo.
    echo 1. Сейчас откроется страница загрузки Python
    echo 2. Нажмите "Download Python 3.12.x" (последняя версия)
    echo 3. Запустите скачанный файл
    echo 4. [!] ВАЖНО: Поставьте галочку "Add Python to PATH"
    echo 5. Нажмите "Install Now"
    echo 6. После установки запустите этот скрипт заново
    echo.

    choice /C YN /M "Открыть страницу загрузки Python"
    if errorlevel 2 goto manual
    if errorlevel 1 start https://www.python.org/downloads/

    :manual
    echo.
    echo После установки Python запустите этот скрипт заново.
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python установлен
echo.

REM Обновление pip
echo [Шаг 2/5] Обновление pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [ВНИМАНИЕ] Не удалось обновить pip, продолжаем...
) else (
    echo [OK] pip обновлен
)
echo.

REM Установка yt-dlp
echo [Шаг 3/5] Установка yt-dlp (загрузчик видео)...
pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    pip install yt-dlp
    if errorlevel 1 (
        color 0C
        echo [ОШИБКА] Не удалось установить yt-dlp
        pause
        exit /b 1
    )
    echo [OK] yt-dlp установлен
) else (
    echo [OK] yt-dlp уже установлен
)
echo.

REM Установка SpeechRecognition
echo [Шаг 4/5] Установка SpeechRecognition (распознавание речи)...
pip show SpeechRecognition >nul 2>&1
if errorlevel 1 (
    pip install SpeechRecognition
    if errorlevel 1 (
        color 0C
        echo [ОШИБКА] Не удалось установить SpeechRecognition
        pause
        exit /b 1
    )
    echo [OK] SpeechRecognition установлен
) else (
    echo [OK] SpeechRecognition уже установлен
)
echo.

REM Установка pydub
echo [Шаг 5/5] Установка pydub (обработка аудио)...
pip show pydub >nul 2>&1
if errorlevel 1 (
    pip install pydub
    if errorlevel 1 (
        color 0C
        echo [ОШИБКА] Не удалось установить pydub
        pause
        exit /b 1
    )
    echo [OK] pydub установлен
) else (
    echo [OK] pydub уже установлен
)
echo.

REM Проверка FFmpeg (опционально)
echo ========================================================
echo.
echo [Опционально] Проверка FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [!] FFmpeg не найден
    echo.
    echo FFmpeg не обязателен, но улучшает совместимость с форматами.
    echo.
    echo Хотите установить FFmpeg через Chocolatey?
    echo (Требуется администраторский запуск)
    echo.
    choice /C YN /M "Установить FFmpeg (Y/N)"
    if errorlevel 2 goto skip_ffmpeg
    if errorlevel 1 goto install_ffmpeg

    :install_ffmpeg
    echo.
    echo Проверка Chocolatey...
    choco --version >nul 2>&1
    if errorlevel 1 (
        echo Chocolatey не установлен.
        echo.
        echo Установка FFmpeg вручную:
        echo 1. Скачайте: https://www.gyan.dev/ffmpeg/builds/
        echo 2. Распакуйте в C:\ffmpeg
        echo 3. Добавьте C:\ffmpeg\bin в PATH
        echo.
        choice /C YN /M "Открыть страницу загрузки FFmpeg"
        if errorlevel 2 goto skip_ffmpeg
        if errorlevel 1 start https://www.gyan.dev/ffmpeg/builds/
        goto skip_ffmpeg
    )

    echo Установка FFmpeg...
    choco install ffmpeg -y
    if errorlevel 1 (
        echo [!] Не удалось установить через Chocolatey
        echo Попробуйте установить вручную
    ) else (
        echo [OK] FFmpeg установлен
    )
) else (
    echo [OK] FFmpeg уже установлен
    ffmpeg -version 2>&1 | findstr "version"
)

:skip_ffmpeg
echo.
echo ========================================================
echo.
echo              ПРОВЕРКА УСТАНОВЛЕННЫХ ПАКЕТОВ
echo.
echo ========================================================
echo.
pip list | findstr "yt-dlp SpeechRecognition pydub"
echo.
echo ========================================================

color 0A
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║          УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО! ✓                ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo Все необходимые компоненты установлены.
echo.
echo СЛЕДУЮЩИЕ ШАГИ:
echo.
echo 1. Прочитайте README_WINDOWS.md для подробных инструкций
echo 2. Используйте run_transcribe.bat для транскрибации локальных файлов
echo 3. Используйте run_transcribe_with_cookies.bat для приватных видео
echo.
echo ========================================================
echo.
pause
