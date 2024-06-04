# from pytube import YouTube
# import os

# def get_stream_options(video_url):
#     yt = YouTube(video_url)
#     # Filtrar streams progresivos que contienen tanto video como audio
#     streams = yt.streams.filter(progressive=True, file_extension='mp4')
#     options = [{'index': i, 'resolution': stream.resolution, 'mime_type': stream.mime_type} for i, stream in enumerate(streams)]
#     return options

# def download_video(video_url, selection):
#     yt = YouTube(video_url)
#     # Filtrar streams progresivos que contienen tanto video como audio
#     streams = yt.streams.filter(progressive=True, file_extension='mp4')
#     selected_stream = streams[selection]

#     download_path = 'Downloads/'  # Asegúrate de que esta carpeta exista
#     if not os.path.exists(download_path):
#         os.makedirs(download_path)

#     # Descargar el stream progresivo seleccionado
#     print("Descargando...")
#     out_file = selected_stream.download(output_path=download_path)

#     file_name = selected_stream.default_filename

#     print(f"Video descargado en: {os.path.join(download_path, file_name)}")
#     return os.path.join(download_path, file_name)

#codigo optimisado para mas velocidad
import os
from pytube import YouTube
import aiohttp
import asyncio
import functools

def get_stream_options(video_url):
    yt = YouTube(video_url)
    streams = yt.streams.filter(progressive=True, file_extension='mp4')
    options = [{'index': i, 'resolution': stream.resolution, 'mime_type': stream.mime_type} for i, stream in enumerate(streams)]
    return options

async def download_stream(session, url, output_path):
    async with session.get(url) as response:
        with open(output_path, 'wb') as file:
            file.write(await response.read())

async def download_video(video_url, selection):
    yt = YouTube(video_url)
    streams = yt.streams.filter(progressive=True, file_extension='mp4')
    selected_stream = streams[selection]

    download_path = 'Downloads/'
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    stream_url = selected_stream.url
    output_file = os.path.join(download_path, selected_stream.default_filename)

    async with aiohttp.ClientSession() as session:
        await download_stream(session, stream_url, output_file)

    print(f"Video descargado en: {output_file}")
    return output_file

def run_download_video(video_url, selection):
    asyncio.run(download_video(video_url, selection))
