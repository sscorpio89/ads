#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для транскрибации локального видео/аудио файла

Использование:
python3 transcribe_local_file.py <путь_к_файлу>
"""

import os
import sys
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
import math

TEMP_DIR = "/tmp/video_transcribe"
os.makedirs(TEMP_DIR, exist_ok=True)

def convert_to_wav(input_file):
    """Конвертирует видео/аудио в WAV формат"""
    print(f"Конвертация файла: {input_file}")

    output_wav = os.path.join(TEMP_DIR, "converted_audio.wav")

    # Проверяем, является ли файл уже WAV
    if input_file.lower().endswith('.wav'):
        return input_file

    # Пытаемся конвертировать с помощью pydub
    try:
        print("Попытка конвертации с помощью pydub...")
        audio = AudioSegment.from_file(input_file)
        audio.export(output_wav, format="wav")
        print(f"✓ Конвертация завершена: {output_wav}")
        return output_wav
    except Exception as e:
        print(f"❌ Ошибка конвертации: {e}")
        raise Exception("Не удалось сконвертировать файл. Убедитесь, что файл является видео или аудио.")

def transcribe_audio_chunks(audio_file, chunk_duration_ms=60000):
    """Транскрибирует аудио по частям"""
    print("\n" + "="*60)
    print("Загружаем аудио файл...")
    print("="*60)

    try:
        audio = AudioSegment.from_wav(audio_file)
    except:
        audio = AudioSegment.from_file(audio_file)

    duration_ms = len(audio)
    duration_sec = duration_ms / 1000
    chunks_count = math.ceil(duration_ms / chunk_duration_ms)

    print(f"📊 Длительность аудио: {duration_sec:.2f} секунд ({duration_sec/60:.2f} минут)")
    print(f"📦 Разбиваем на {chunks_count} частей по {chunk_duration_ms/1000}s...")

    recognizer = sr.Recognizer()
    # Настройка для лучшего распознавания русской речи
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    full_transcription = []

    for i in range(chunks_count):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, duration_ms)

        progress = (i + 1) / chunks_count * 100
        print(f"\n[{progress:.1f}%] Обработка части {i+1}/{chunks_count} ({start_ms/1000:.1f}s - {end_ms/1000:.1f}s)...")

        chunk = audio[start_ms:end_ms]
        chunk_file = os.path.join(TEMP_DIR, f"chunk_{i}.wav")
        chunk.export(chunk_file, format="wav")

        try:
            with sr.AudioFile(chunk_file) as source:
                # Настройка на фоновый шум
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)

                # Используем Google Speech Recognition для русского языка
                print("   Распознавание речи...")
                text = recognizer.recognize_google(audio_data, language="ru-RU")

                full_transcription.append({
                    'start': start_ms/1000,
                    'end': end_ms/1000,
                    'text': text
                })
                print(f"   ✓ Распознано ({len(text)} символов): {text[:80]}...")

        except sr.UnknownValueError:
            print("   ✗ Речь не распознана (возможно, тишина или неразборчивая речь)")
            full_transcription.append({
                'start': start_ms/1000,
                'end': end_ms/1000,
                'text': '[Речь не распознана]'
            })
        except sr.RequestError as e:
            print(f"   ✗ Ошибка сервиса распознавания: {e}")
            full_transcription.append({
                'start': start_ms/1000,
                'end': end_ms/1000,
                'text': f'[Ошибка сервиса: {e}]'
            })
        except Exception as e:
            print(f"   ✗ Ошибка: {e}")
            full_transcription.append({
                'start': start_ms/1000,
                'end': end_ms/1000,
                'text': f'[Ошибка: {e}]'
            })

        # Очищаем временный файл
        try:
            os.remove(chunk_file)
        except:
            pass

    return full_transcription

def format_time(seconds):
    """Форматирует время в читаемый вид"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def create_html(transcription_data, output_file, source_file):
    """Создает красивый HTML файл с транскрибацией"""

    # Формируем HTML для сегментов
    segments_html = ""
    for segment in transcription_data:
        start_time = format_time(segment['start'])
        end_time = format_time(segment['end'])
        text = segment['text']

        segments_html += f"""
        <div class="segment">
            <div class="time-label">⏱ {start_time} - {end_time}</div>
            <div class="text">{text}</div>
        </div>
"""

    # Полный текст
    full_text = "\n\n".join([s['text'] for s in transcription_data])

    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Транскрибация видео</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}

        .info {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #667eea;
        }}

        .info p {{
            margin: 10px 0;
            color: #495057;
        }}

        .info strong {{
            color: #2c3e50;
        }}

        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}

        .tab {{
            padding: 15px 30px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.1em;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }}

        .tab:hover {{
            color: #667eea;
        }}

        .tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: bold;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .segment {{
            margin-bottom: 25px;
            padding: 20px;
            background: linear-gradient(to right, #f8f9fa 0%, #ffffff 100%);
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .segment:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
        }}

        .time-label {{
            color: #667eea;
            font-weight: bold;
            font-size: 0.95em;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }}

        .text {{
            color: #2c3e50;
            font-size: 1.1em;
            line-height: 1.8;
        }}

        .full-text {{
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            line-height: 2;
            font-size: 1.1em;
            color: #2c3e50;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Транскрибация видео</h1>

        <div class="info">
            <p><strong>📂 Источник:</strong> {os.path.basename(source_file)}</p>
            <p><strong>📍 Путь:</strong> {source_file}</p>
            <p><strong>🕐 Создано:</strong> {subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'], capture_output=True, text=True).stdout.strip()}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(transcription_data)}</div>
                <div class="stat-label">Сегментов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(full_text.split())}</div>
                <div class="stat-label">Слов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(full_text)}</div>
                <div class="stat-label">Символов</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('segments')">По времени</button>
            <button class="tab" onclick="showTab('full')">Полный текст</button>
        </div>

        <div id="segments-tab" class="tab-content active">
{segments_html}
        </div>

        <div id="full-tab" class="tab-content">
            <div class="full-text">{full_text}</div>
        </div>
    </div>

    <script>
        function showTab(tabName) {{
            // Скрываем все вкладки
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});

            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // Показываем выбранную вкладку
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✓ HTML файл создан: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("❌ Использование: python3 transcribe_local_file.py <путь_к_файлу>")
        print("\nПример:")
        print("  python3 transcribe_local_file.py /path/to/video.mp4")
        print("  python3 transcribe_local_file.py /path/to/audio.wav")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        sys.exit(1)

    output_html = "/home/user/ads/transcription.html"

    print("="*60)
    print("🎬 ТРАНСКРИБАЦИЯ ВИДЕО/АУДИО")
    print("="*60)
    print(f"Входной файл: {input_file}")
    print(f"Размер: {os.path.getsize(input_file) / (1024*1024):.2f} MB")
    print("="*60)

    try:
        # Конвертируем в WAV если нужно
        audio_file = convert_to_wav(input_file)

        # Транскрибируем
        transcription_data = transcribe_audio_chunks(audio_file)

        # Создаем HTML
        create_html(transcription_data, output_html, input_file)

        print("\n" + "="*60)
        print("✅ ТРАНСКРИБАЦИЯ ЗАВЕРШЕНА")
        print("="*60)
        print(f"Результат сохранен в: {output_html}")
        print("="*60)

        # Выводим краткий результат
        print("\n📄 КРАТКАЯ ВЕРСИЯ:\n")
        for segment in transcription_data[:5]:  # Первые 5 сегментов
            print(f"[{format_time(segment['start'])} - {format_time(segment['end'])}]")
            print(f"{segment['text']}\n")

        if len(transcription_data) > 5:
            print(f"... и еще {len(transcription_data) - 5} сегментов")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
