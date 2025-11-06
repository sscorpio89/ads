# 🚀 Быстрый старт - Windows

## ⚡ За 3 минуты

### Шаг 1: Установите Python (1 минута)

1. Скачайте: https://www.python.org/downloads/
2. Запустите установщик
3. ✅ **Поставьте галочку "Add Python to PATH"**
4. Нажмите "Install Now"

### Шаг 2: Установите зависимости (1 минута)

**Запустите файл:** `install_dependencies.bat`

Или вручную в PowerShell:
```powershell
pip install yt-dlp SpeechRecognition pydub
```

### Шаг 3: Запустите транскрибацию (1 минута)

#### Вариант A: Drag & Drop (самый простой)

1. Перетащите видео файл на `run_transcribe.bat`
2. Подождите завершения
3. Откройте `transcription.html`

#### Вариант B: Через командную строку

```powershell
python transcribe_local_file.py "C:\путь\к\видео.mp4"
```

---

## 📁 Структура файлов

После скачивания у вас должны быть:

```
C:\Transcription\
├── 📄 README_WINDOWS.md              ← Полная инструкция
├── 📄 QUICKSTART_WINDOWS.md          ← Этот файл
├── 🐍 transcribe_local_file.py       ← Основной скрипт
├── 🐍 transcribe_with_cookies.py     ← Для приватных видео
├── ⚙️ install_dependencies.bat       ← Установка зависимостей
├── ▶️ run_transcribe.bat             ← Простой запуск
└── ▶️ run_transcribe_with_cookies.bat ← Запуск с cookies
```

---

## 🎯 Примеры использования

### Пример 1: Простое видео

```powershell
# Перейдите в папку
cd C:\Transcription

# Запустите
python transcribe_local_file.py "video.mp4"

# Откройте результат
start transcription.html
```

### Пример 2: Путь с пробелами

```powershell
python transcribe_local_file.py "C:\My Videos\Interview 2024.mp4"
```

### Пример 3: Аудио файл

```powershell
python transcribe_local_file.py "podcast.mp3"
```

---

## ⚠️ Частые проблемы

### "python" не распознается

**Решение 1:** Используйте `py` вместо `python`
```powershell
py transcribe_local_file.py "video.mp4"
```

**Решение 2:** Переустановите Python с галочкой "Add to PATH"

### "No module named 'speech_recognition'"

**Решение:**
```powershell
pip install SpeechRecognition
```

### Видео не скачивается (403 Forbidden)

**Причина:** Видео приватное

**Решение:**
1. Скачайте видео вручную через браузер
2. Или используйте cookies (см. README_WINDOWS.md)

---

## 📊 Что вы получите

После транскрибации откроется HTML файл с:

- ⏱️ **Таймкодами** для каждого сегмента
- 📊 **Статистикой** (слова, символы, сегменты)
- 🎨 **Красивым дизайном** с градиентами
- 📑 **Двумя режимами просмотра** (по времени / полный текст)

---

## 🎓 Дальнейшее обучение

### Для новичков в Python:

1. **Python Tutorial**: https://www.python.org/about/gettingstarted/
2. **W3Schools Python**: https://www.w3schools.com/python/

### Для продвинутых:

- Измените настройки в скриптах (язык, длительность сегментов)
- Создайте свой дизайн HTML
- Добавьте экспорт в SRT (субтитры)

---

## 📞 Нужна помощь?

1. ✅ Прочитайте **README_WINDOWS.md** (подробные инструкции)
2. ✅ Проверьте раздел "Решение проблем"
3. ✅ Убедитесь, что все зависимости установлены
4. ✅ Попробуйте с коротким тестовым видео

---

## ⚡ Полезные команды

```powershell
# Проверка версии Python
python --version

# Проверка установленных пакетов
pip list

# Обновление пакета
pip install --upgrade yt-dlp

# Помощь по скрипту
python transcribe_local_file.py --help
```

---

## 🎉 Успехов!

**Следующие шаги:**

1. ✅ Установите Python
2. ✅ Запустите `install_dependencies.bat`
3. ✅ Перетащите видео на `run_transcribe.bat`
4. ✅ Наслаждайтесь результатом!

Для детальной информации читайте **README_WINDOWS.md**
