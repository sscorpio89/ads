#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which

# Временная директория для файлов
TEMP_DIR = "/tmp/video_transcribe"
os.makedirs(TEMP_DIR, exist_ok=True)

def download_video(url):
    """Скачивает видео и извлекает аудио используя yt-dlp"""
    print("Скачивание видео...")
    audio_file = os.path.join(TEMP_DIR, "audio.wav")

    # yt-dlp может извлекать аудио напрямую
    cmd = [
        "yt-dlp",
        "--no-check-certificate",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", audio_file.replace(".wav", ".%(ext)s"),
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"Ошибка при скачивании: {result.stderr}")
            # Попробуем альтернативный метод - скачать видео целиком
            print("Пробуем скачать видео полностью...")
            video_file = os.path.join(TEMP_DIR, "video.mp4")
            cmd = ["yt-dlp", "--no-check-certificate", "-f", "best", "-o", video_file, url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise Exception(f"Не удалось скачать видео: {result.stderr}")
            return video_file
        return audio_file
    except Exception as e:
        print(f"Ошибка: {e}")
        raise

def transcribe_audio_simple(audio_file):
    """Простая транскрибация используя Google Speech Recognition"""
    print("Начинаем транскрибацию...")

    recognizer = sr.Recognizer()

    # Если файл не в wav формате, пытаемся сконвертировать
    if not audio_file.endswith('.wav'):
        print("Конвертируем в WAV формат...")
        # Используем простой подход через subprocess
        wav_file = os.path.join(TEMP_DIR, "audio_converted.wav")
        # Попробуем использовать yt-dlp для конвертации
        try:
            cmd = ["yt-dlp", "--extract-audio", "--audio-format", "wav", "-o", wav_file.replace(".wav", ".%(ext)s"), audio_file]
            subprocess.run(cmd, check=False)
            if os.path.exists(wav_file):
                audio_file = wav_file
        except:
            pass

    try:
        # Читаем аудио файл
        with sr.AudioFile(audio_file) as source:
            print("Загружаем аудио...")
            audio_data = recognizer.record(source)

            print("Распознаем речь (это может занять время)...")
            # Используем Google Speech Recognition для русского языка
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь в аудио"
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания речи: {e}"
    except Exception as e:
        return f"Ошибка при транскрибации: {e}"

def create_html(transcription, output_file):
    """Создает HTML файл с транскрибацией"""
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Транскрибация видео</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .transcription {{
            background-color: #f9f9f9;
            padding: 20px;
            border-left: 4px solid #4CAF50;
            margin-top: 20px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Транскрибация видео</h1>
        <p class="timestamp">Создано: {subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'], capture_output=True, text=True).stdout.strip()}</p>
        <div class="transcription">
{transcription}
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nHTML файл создан: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Использование: python3 transcribe_video.py <URL>")
        sys.exit(1)

    video_url = sys.argv[1]
    output_html = "/home/user/ads/transcription.html"

    try:
        # Скачиваем и извлекаем аудио
        audio_file = download_video(video_url)
        print(f"Аудио файл: {audio_file}")

        # Транскрибируем
        transcription = transcribe_audio_simple(audio_file)

        # Создаем HTML
        create_html(transcription, output_html)

        print("\n" + "="*50)
        print("ТРАНСКРИБАЦИЯ:")
        print("="*50)
        print(transcription)
        print("="*50)

        # Очищаем временные файлы
        # import shutil
        # shutil.rmtree(TEMP_DIR)

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
