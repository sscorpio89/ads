#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для транскрибации видео с использованием cookies

Инструкция:
1. Откройте видео в браузере Chrome/Firefox
2. Установите расширение "Get cookies.txt LOCALLY"
3. Экспортируйте cookies в файл cookies.txt в эту же директорию
4. Запустите: python3 transcribe_with_cookies.py <URL>
"""

import os
import sys
import subprocess
import speech_recognition as sr

TEMP_DIR = "/tmp/video_transcribe"
os.makedirs(TEMP_DIR, exist_ok=True)

def download_video_with_cookies(url, cookies_file):
    """Скачивает приватное видео используя cookies"""
    print("Скачивание видео с использованием cookies...")
    audio_file = os.path.join(TEMP_DIR, "audio.wav")

    cmd = [
        "yt-dlp",
        "--cookies", cookies_file,
        "--no-check-certificate",
        "--extract-audio",
        "--audio-format", "wav",
        "-o", audio_file.replace(".wav", ".%(ext)s"),
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise Exception(f"Не удалось скачать видео: {result.stderr}")

    return audio_file

def transcribe_audio_chunks(audio_file, chunk_duration_ms=60000):
    """Транскрибирует аудио по частям для больших файлов"""
    from pydub import AudioSegment
    import math

    print("Загружаем аудио файл...")
    try:
        audio = AudioSegment.from_wav(audio_file)
    except:
        # Если файл не wav, пробуем загрузить как есть
        audio = AudioSegment.from_file(audio_file)

    duration_ms = len(audio)
    chunks_count = math.ceil(duration_ms / chunk_duration_ms)

    print(f"Длительность аудио: {duration_ms/1000:.2f} секунд")
    print(f"Разбиваем на {chunks_count} частей...")

    recognizer = sr.Recognizer()
    full_transcription = []

    for i in range(chunks_count):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, duration_ms)

        print(f"\nОбработка части {i+1}/{chunks_count} ({start_ms/1000:.1f}s - {end_ms/1000:.1f}s)...")

        chunk = audio[start_ms:end_ms]
        chunk_file = os.path.join(TEMP_DIR, f"chunk_{i}.wav")
        chunk.export(chunk_file, format="wav")

        try:
            with sr.AudioFile(chunk_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                full_transcription.append(f"[{start_ms/1000:.1f}s - {end_ms/1000:.1f}s]\n{text}")
                print(f"✓ Распознано: {text[:100]}...")
        except sr.UnknownValueError:
            print("✗ Речь не распознана в этом фрагменте")
            full_transcription.append(f"[{start_ms/1000:.1f}s - {end_ms/1000:.1f}s]\n[Речь не распознана]")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            full_transcription.append(f"[{start_ms/1000:.1f}s - {end_ms/1000:.1f}s]\n[Ошибка: {e}]")

    return "\n\n".join(full_transcription)

def create_html(transcription, output_file, video_url):
    """Создает HTML файл с транскрибацией"""
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Транскрибация видео</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 30px auto;
            padding: 20px;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        .info a {{
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
        }}
        .info a:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .transcription {{
            background-color: #f8f9fa;
            padding: 25px;
            border-left: 5px solid #667eea;
            margin-top: 20px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 1.1em;
            line-height: 1.8;
        }}
        .segment {{
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .time-label {{
            color: #667eea;
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Транскрибация видео</h1>

        <div class="info">
            <p><strong>Источник:</strong> <a href="{video_url}" target="_blank">{video_url}</a></p>
            <p class="timestamp"><strong>Создано:</strong> {subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'], capture_output=True, text=True).stdout.strip()}</p>
        </div>

        <div class="transcription">
{transcription}
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✓ HTML файл создан: {output_file}")

def main():
    cookies_file = "/home/user/ads/cookies.txt"

    if len(sys.argv) < 2:
        print("Использование: python3 transcribe_with_cookies.py <URL>")
        print(f"\nПеред запуском поместите файл cookies.txt в: {cookies_file}")
        sys.exit(1)

    if not os.path.exists(cookies_file):
        print(f"❌ Файл cookies не найден: {cookies_file}")
        print("\nИнструкция по получению cookies:")
        print("1. Откройте видео в браузере")
        print("2. Установите расширение 'Get cookies.txt LOCALLY' или 'cookies.txt'")
        print("3. Экспортируйте cookies в файл cookies.txt")
        print(f"4. Поместите файл в: {cookies_file}")
        sys.exit(1)

    video_url = sys.argv[1]
    output_html = "/home/user/ads/transcription.html"

    try:
        # Скачиваем видео
        audio_file = download_video_with_cookies(video_url, cookies_file)
        print(f"✓ Аудио файл: {audio_file}")

        # Транскрибируем
        print("\n" + "="*60)
        print("Начинаем транскрибацию...")
        print("="*60)
        transcription = transcribe_audio_chunks(audio_file)

        # Создаем HTML
        create_html(transcription, output_html, video_url)

        print("\n" + "="*60)
        print("ТРАНСКРИБАЦИЯ ЗАВЕРШЕНА")
        print("="*60)
        print(transcription)
        print("="*60)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
