import os
import yt_dlp
import time  # ⏱️ Importación necesaria para medir las métricas de tiempo

def download_media(video_url: str, download_type: str, quality_option: str) -> dict:
    """
    Descarga contenido multimedia de YouTube limpiando nombres conflictivos de forma nativa en Windows.
    Devuelve un diccionario con las métricas completas para la base de datos (PostgreSQL).
    """
    download_path = 'app/downloads'
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    quality = "mejor" if quality_option in ["4", "mejor"] else quality_option

    if download_type == "1":
        # CONFIGURACIÓN AUDIO MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{download_path}/%(title)s.%(ext)s',
            'restrictfilenames': True,  # Limpia emojis y caracteres inválidos en Windows
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
    else:
        # CONFIGURACIÓN VIDEO MP4
        if quality == "mejor":
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                'outtmpl': f'{download_path}/%(title)s.%(ext)s',
                'restrictfilenames': True,
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'postprocessor_args': {
                    'merger': ['-c:v', 'libx264', '-c:a', 'aac']
                }
            }
        else:
            ydl_opts = {
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={quality}]+bestaudio/best',
                'outtmpl': f'{download_path}/%(title)s.%(ext)s',
                'restrictfilenames': True,
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'postprocessor_args': {
                    'merger': ['-c:v', 'libx264', '-c:a', 'aac']
                }
            }

    # ⏱️ Capturar el inicio exacto del cronómetro antes de yt-dlp
    inicio = time.time()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        
        if download_type == "1":
            file_path = os.path.splitext(file_path)[0] + '.mp3'
        else:
            file_path = os.path.splitext(file_path)[0] + '.mp4'

    # ⏱️ Detener el cronómetro y calcular métricas finales
    fin = time.time()
    file_size_mb = 0.0

    if os.path.exists(file_path):
        # Obtener el peso real del archivo y convertirlo a MB redondeado a 2 decimales
        file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

    # Retornar el diccionario con los datos estructurados para main.py y database.py
    return {
        "file_path": file_path,
        "title": info_dict.get("title", "Sin título"),
        "file_size_mb": file_size_mb,
        "download_time_seconds": round(fin - inicio, 2)
    }


def get_available_formats(video_url: str) -> dict:
    """
    Extrae las calidades disponibles de un video o Short de YouTube de forma segura.
    """
    ydl_opts = {
        'noplaylist': True,
        'extract_flat': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            
            available_heights = set()
            for f in formats:
                height = f.get('height')
                if height and height in [144, 240, 360, 480, 720, 1080, 1440, 2160]:
                    available_heights.add(str(height))
            
            return {
                "status": "success",
                "title": info.get('title', 'Video'),
                "available_video_qualities": sorted(list(available_heights), reverse=True)
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}