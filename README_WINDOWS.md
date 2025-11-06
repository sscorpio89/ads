# 📝 Транскрибация видео в HTML - Инструкция для Windows

## 📋 Содержание
- [Быстрый старт](#-быстрый-старт)
- [Подробная установка](#-подробная-установка)
- [Способы транскрибации](#-способы-транскрибации)
- [Примеры использования](#-примеры-использования)
- [Решение проблем](#-решение-проблем)

---

## 🚀 Быстрый старт

### Шаг 1: Установите Python

1. Скачайте Python с официального сайта: https://www.python.org/downloads/
2. Запустите установщик
3. ⚠️ **ВАЖНО**: Поставьте галочку **"Add Python to PATH"**
4. Нажмите "Install Now"

![Python Installation](https://i.imgur.com/9jHKmvE.png)

### Шаг 2: Установите зависимости

Откройте **PowerShell** или **Командную строку** (Win + R → `cmd`):

```powershell
# Установка необходимых библиотек
pip install yt-dlp SpeechRecognition pydub

# Проверка установки
python --version
pip list
```

### Шаг 3: Скачайте скрипты

Скачайте следующие файлы в одну папку (например, `C:\Transcription`):
- `transcribe_local_file.py`
- `transcribe_with_cookies.py`
- `run_transcribe.bat` (создадим ниже)

---

## 📦 Подробная установка

### 1. Установка Python (детально)

**Windows 10/11:**

1. Перейдите на https://www.python.org/downloads/
2. Нажмите "Download Python 3.12.x" (последняя версия)
3. Запустите скачанный файл `python-3.12.x-amd64.exe`
4. В окне установки:
   - ✅ Поставьте галочку **"Add Python to PATH"**
   - ✅ Выберите **"Install Now"**
5. Дождитесь завершения установки

**Проверка установки:**
```powershell
python --version
# Должно вывести: Python 3.12.x
```

### 2. Установка зависимостей

Откройте **PowerShell** (правой кнопкой мыши на кнопке Пуск → Windows PowerShell):

```powershell
# Обновляем pip
python -m pip install --upgrade pip

# Устанавливаем основные библиотеки
pip install yt-dlp
pip install SpeechRecognition
pip install pydub

# Проверяем установку
pip list | Select-String "yt-dlp|SpeechRecognition|pydub"
```

**Ожидаемый результат:**
```
pydub                     0.25.1
SpeechRecognition         3.14.3
yt-dlp                    2025.10.22
```

### 3. Установка FFmpeg (опционально, для некоторых форматов)

FFmpeg нужен для работы с некоторыми видеоформатами.

**Способ 1: Через Chocolatey (рекомендуется)**
```powershell
# Установка Chocolatey (если еще не установлен)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Установка FFmpeg
choco install ffmpeg
```

**Способ 2: Вручную**
1. Скачайте FFmpeg: https://www.gyan.dev/ffmpeg/builds/
2. Выберите "ffmpeg-release-essentials.zip"
3. Распакуйте в `C:\ffmpeg`
4. Добавьте `C:\ffmpeg\bin` в PATH:
   - Win + R → `sysdm.cpl` → вкладка "Дополнительно"
   - "Переменные среды"
   - В "Системные переменные" найдите "Path" → "Изменить"
   - "Создать" → введите `C:\ffmpeg\bin`
   - OK → OK → OK

**Проверка:**
```powershell
ffmpeg -version
```

---

## 🎯 Способы транскрибации

### ⚠️ Важно: Проблема с приватным видео

Видео по вашей ссылке является **приватным** и защищено от прямого скачивания.
Используйте один из следующих способов:

---

### 🥇 Способ 1: Транскрибация локального файла (САМЫЙ ПРОСТОЙ)

Если вы можете скачать видео через браузер.

#### Шаг 1: Скачайте видео вручную

1. Откройте видео в браузере (Chrome, Edge, Firefox)
2. Используйте один из способов:
   - Встроенная кнопка скачивания на сайте
   - Расширение для скачивания видео (например, Video DownloadHelper)
   - Инструменты разработчика (F12 → Network → найдите .mp4 файл)

3. Сохраните видео на диск, например: `C:\Videos\video.mp4`

#### Шаг 2: Запустите транскрибацию

**Через PowerShell:**
```powershell
cd C:\Transcription
python transcribe_local_file.py "C:\Videos\video.mp4"
```

**Через проводник (drag & drop):**
1. Создайте файл `run_transcribe.bat` (см. ниже)
2. Перетащите видео на этот .bat файл
3. Готово!

#### Создание run_transcribe.bat

Создайте файл `run_transcribe.bat` в папке со скриптами:

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   ТРАНСКРИБАЦИЯ ВИДЕО В HTML
echo ========================================
echo.

if "%~1"=="" (
    echo Перетащите видео файл на этот .bat файл
    echo Или укажите путь к файлу:
    set /p VIDEO_PATH="Путь к видео: "
) else (
    set VIDEO_PATH=%~1
)

echo.
echo Обработка файла: %VIDEO_PATH%
echo.
echo Это может занять несколько минут...
echo.

python transcribe_local_file.py "%VIDEO_PATH%"

echo.
echo ========================================
echo   ГОТОВО!
echo ========================================
echo.
echo HTML файл создан в текущей папке
echo Откройте transcription.html в браузере
echo.
pause
```

**Использование:**
1. Сохраните как `run_transcribe.bat`
2. Перетащите видео файл на этот .bat файл
3. Дождитесь завершения
4. Откройте `transcription.html`

---

### 🥈 Способ 2: Транскрибация с использованием cookies

Для приватных видео, доступных через браузер.

#### Шаг 1: Экспортируйте cookies из браузера

**Для Google Chrome:**

1. Установите расширение: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Откройте страницу с видео: `https://rutube.ru/video/private/40128d8e76495245bd2ec70bda4b30bb/?p=d6tJR_LQzVg8_FdwZ0ZmnQ`
3. Нажмите на иконку расширения (в правом верхнем углу)
4. Нажмите **"Export"**
5. Выберите **"Only site"** (только для rutube.ru)
6. Сохраните файл как `cookies.txt` в папку со скриптами

**Для Microsoft Edge:**

1. Установите то же расширение из Chrome Web Store
2. Следуйте инструкциям выше

**Для Firefox:**

1. Установите расширение: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Откройте страницу с видео
3. Нажмите на иконку расширения
4. Нажмите **"Export Cookies"**
5. Сохраните как `cookies.txt`

#### Шаг 2: Поместите cookies.txt в папку со скриптами

Структура папки должна быть:
```
C:\Transcription\
├── transcribe_with_cookies.py
├── transcribe_local_file.py
├── cookies.txt  ← здесь
└── run_transcribe_with_cookies.bat
```

#### Шаг 3: Запустите транскрибацию

**Через PowerShell:**
```powershell
cd C:\Transcription
python transcribe_with_cookies.py "https://rutube.ru/video/private/40128d8e76495245bd2ec70bda4b30bb/?p=d6tJR_LQzVg8_FdwZ0ZmnQ"
```

**Через .bat файл:**

Создайте `run_transcribe_with_cookies.bat`:

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   ТРАНСКРИБАЦИЯ С COOKIES
echo ========================================
echo.

if not exist cookies.txt (
    echo ОШИБКА: Файл cookies.txt не найден!
    echo.
    echo Инструкция:
    echo 1. Установите расширение "Get cookies.txt LOCALLY"
    echo 2. Откройте видео в браузере
    echo 3. Экспортируйте cookies
    echo 4. Сохраните как cookies.txt в эту папку
    echo.
    pause
    exit
)

echo Файл cookies найден ✓
echo.

set /p VIDEO_URL="Введите URL видео: "

echo.
echo Загрузка и транскрибация...
echo Это может занять несколько минут...
echo.

python transcribe_with_cookies.py "%VIDEO_URL%"

echo.
echo ========================================
echo   ГОТОВО!
echo ========================================
echo.
pause
```

---

### 🥉 Способ 3: Ручное скачивание через yt-dlp

Если cookies работают, можно сначала скачать, потом транскрибировать.

#### Шаг 1: Скачайте видео

```powershell
cd C:\Transcription
yt-dlp --cookies cookies.txt --no-check-certificate -o "video.mp4" "https://rutube.ru/video/private/40128d8e76495245bd2ec70bda4b30bb/?p=d6tJR_LQzVg8_FdwZ0ZmnQ"
```

#### Шаг 2: Транскрибируйте

```powershell
python transcribe_local_file.py "video.mp4"
```

---

## 💡 Примеры использования

### Пример 1: Простая транскрибация MP4 файла

```powershell
python transcribe_local_file.py "C:\Users\User\Downloads\video.mp4"
```

### Пример 2: Транскрибация аудио файла

```powershell
python transcribe_local_file.py "C:\Music\podcast.mp3"
```

### Пример 3: Транскрибация с относительным путем

```powershell
# Если файл в той же папке
python transcribe_local_file.py "my_video.mp4"
```

### Пример 4: Пути с пробелами

```powershell
# Используйте кавычки для путей с пробелами
python transcribe_local_file.py "C:\My Videos\Interview 2024.mp4"
```

---

## 🎨 Результат транскрибации

После завершения работы скрипта будет создан файл **`transcription.html`**

### Что внутри:

1. **📊 Статистика:**
   - Количество сегментов
   - Количество слов
   - Количество символов

2. **⏱ Две вкладки просмотра:**
   - **По времени**: текст разбит на сегменты с таймкодами
   - **Полный текст**: весь текст одним блоком

3. **🎨 Красивый дизайн:**
   - Адаптивная верстка
   - Градиентный фон
   - Удобная навигация

### Открытие результата:

```powershell
# Автоматически открыть в браузере
start transcription.html

# Или просто двойной клик по файлу в проводнике
```

---

## 🔧 Настройки и параметры

### Изменение длительности сегментов

По умолчанию видео разбивается на сегменты по 60 секунд. Чтобы изменить:

Откройте `transcribe_local_file.py` и найдите строку:

```python
transcription_data = transcribe_audio_chunks(audio_file, chunk_duration_ms=60000)
```

Измените `60000` на нужное значение (в миллисекундах):
- `30000` = 30 секунд (для более точной разбивки)
- `120000` = 2 минуты (для более быстрой обработки)

### Изменение языка распознавания

Для распознавания другого языка найдите в скрипте:

```python
text = recognizer.recognize_google(audio_data, language="ru-RU")
```

Измените `"ru-RU"` на нужный:
- `"en-US"` - английский (США)
- `"en-GB"` - английский (Великобритания)
- `"uk-UA"` - украинский
- `"de-DE"` - немецкий
- `"fr-FR"` - французский
- `"es-ES"` - испанский

---

## 🛠 Решение проблем

### ❌ "python" не распознается как команда

**Проблема:** Python не добавлен в PATH

**Решение:**
1. Найдите где установлен Python: обычно `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python312\`
2. Добавьте в PATH:
   - Win + R → `sysdm.cpl`
   - Вкладка "Дополнительно" → "Переменные среды"
   - В "Переменные пользователя" найдите "Path" → "Изменить"
   - "Создать" → вставьте путь к Python
   - OK → OK → OK
3. Перезапустите PowerShell/CMD

**Альтернатива:** Используйте `py` вместо `python`:
```powershell
py transcribe_local_file.py "video.mp4"
```

### ❌ "pip" не распознается

**Решение:**
```powershell
python -m pip install <package_name>
```

### ❌ Ошибка "No module named 'speech_recognition'"

**Решение:**
```powershell
pip install SpeechRecognition
```

### ❌ Ошибка "Couldn't find ffmpeg"

Это предупреждение, не критичная ошибка. Для некоторых форматов нужен FFmpeg.

**Решение:** Установите FFmpeg (см. раздел "Установка FFmpeg" выше)

**Обход:** Конвертируйте видео в MP4 с помощью онлайн-конвертера:
- https://cloudconvert.com/
- https://www.online-convert.com/

### ❌ Ошибка "HTTP Error 403: Forbidden"

**Проблема:** Видео приватное и требует авторизации

**Решение:** Используйте способ с cookies (см. "Способ 2" выше)

### ❌ Речь не распознается

**Возможные причины и решения:**

1. **Низкое качество аудио**
   - Используйте видео с хорошим качеством звука
   - Избегайте видео с сильным фоновым шумом

2. **Неправильный язык**
   - Убедитесь, что указан правильный язык (`language="ru-RU"`)

3. **Нет интернета**
   - Google Speech Recognition требует подключение к интернету

4. **Слишком длинные сегменты**
   - Уменьшите `chunk_duration_ms` до 30000 (30 секунд)

### ❌ Скрипт зависает или работает очень долго

**Нормальная скорость:** 1-2 минуты обработки на каждую минуту видео

**Если слишком долго:**
1. Проверьте интернет-соединение (нужно для Google Speech API)
2. Проверьте размер видео (очень большие файлы дольше обрабатываются)
3. Увеличьте `chunk_duration_ms` для более быстрой обработки

### ❌ Ошибка кодировки в PowerShell

**Проблема:** Русские буквы отображаются неправильно

**Решение:**
```powershell
chcp 65001
python transcribe_local_file.py "video.mp4"
```

Или добавьте `chcp 65001` в начало .bat файла.

---

## 📝 Поддерживаемые форматы

### Видео форматы:
- ✅ MP4
- ✅ AVI
- ✅ MKV
- ✅ MOV
- ✅ WMV
- ✅ FLV
- ✅ WebM

### Аудио форматы:
- ✅ MP3
- ✅ WAV
- ✅ OGG
- ✅ M4A
- ✅ FLAC
- ✅ AAC

*Примечание: Для некоторых форматов может потребоваться FFmpeg*

---

## ⚡ Советы по ускорению

1. **Используйте короткие видео** для тестирования (1-2 минуты)
2. **Увеличьте размер сегментов** до 120 секунд
3. **Используйте SSD** для хранения временных файлов
4. **Закройте другие программы** для освобождения ресурсов
5. **Используйте видео с хорошим качеством звука** (меньше ошибок = быстрее)

---

## 📞 Часто задаваемые вопросы (FAQ)

### Q: Можно ли обработать несколько видео сразу?

A: Да, создайте .bat файл:

```batch
@echo off
python transcribe_local_file.py "video1.mp4"
move transcription.html transcription1.html

python transcribe_local_file.py "video2.mp4"
move transcription.html transcription2.html

python transcribe_local_file.py "video3.mp4"
move transcription.html transcription3.html

echo Все видео обработаны!
pause
```

### Q: Можно ли использовать без интернета?

A: Нет, Google Speech Recognition API требует подключение к интернету.

**Альтернатива:** Используйте Vosk (офлайн распознавание), но потребуется дополнительная настройка.

### Q: Сколько стоит использование?

A: Все инструменты **полностью бесплатны**. Google Speech Recognition API бесплатен для небольших объемов.

### Q: Можно ли улучшить точность распознавания?

A: Да:
1. Используйте видео с хорошим качеством звука
2. Уменьшите фоновый шум (предварительная обработка)
3. Используйте короткие сегменты (30-45 секунд)
4. Для профессиональной точности используйте платные API (Whisper, Google Cloud Speech-to-Text)

### Q: Можно ли редактировать транскрибацию?

A: Да, откройте `transcription.html` в браузере, скопируйте текст и отредактируйте в Word/Google Docs.

### Q: Работает ли с YouTube?

A: Да! Просто используйте URL YouTube вместо локального файла:

```powershell
yt-dlp -o "youtube_video.mp4" "https://www.youtube.com/watch?v=VIDEO_ID"
python transcribe_local_file.py "youtube_video.mp4"
```

---

## 🎓 Дополнительные ресурсы

- [Официальная документация yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [SpeechRecognition документация](https://github.com/Uberi/speech_recognition)
- [Python для начинающих](https://www.python.org/about/gettingstarted/)

---

## 📧 Поддержка

Если у вас возникли проблемы:

1. Проверьте раздел "Решение проблем"
2. Убедитесь, что все зависимости установлены
3. Попробуйте с простым коротким видео для теста
4. Опишите проблему подробно с текстом ошибки

---

## ✨ Что дальше?

После успешной транскрибации вы можете:

1. **Отредактировать HTML** для изменения дизайна
2. **Экспортировать в другие форматы** (Word, PDF, TXT)
3. **Использовать для создания субтитров** (.srt файлы)
4. **Перевести на другие языки** через Google Translate

---

**Удачной транскрибации! 🎉**
