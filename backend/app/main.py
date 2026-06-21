import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.cleanup import limpiar_descargas
from app.database import guardar_descarga
from app.downloader import download_media, get_available_formats

app = FastAPI(title="Media Downloader API", version="1.0.0")

# Configuración de CORS exponiendo cabeceras para la barra de progreso
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"]
)

# ---- MODELOS DE DATOS (PYDANTIC) ----

class FormatRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    download_type: str  
    quality: str        

# ---- FUNCIONES AUXILIARES ----

def eliminar_archivo(file_path: str):
    """Elimina de forma segura el archivo del servidor local"""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"🗑️ Archivo eliminado con éxito: {file_path}")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar el archivo: {e}")

# ---- ENDPOINTS / RUTAS DE LA API ----

@app.post("/api/formats")
async def api_get_formats(request: FormatRequest):
    resultado = get_available_formats(request.url)
    if resultado["status"] == "error":
        raise HTTPException(status_code=400, detail=resultado["message"])
    return resultado

@app.post("/api/download")
async def api_download(request: DownloadRequest, req_raw: Request, background_tasks: BackgroundTasks):
    try:
        # 1. Descargar el archivo localmente y obtener el diccionario de datos
        download_info = download_media(
            video_url=request.url,
            download_type=request.download_type,
            quality_option=request.quality
        )
        
        file_path = download_info["file_path"]
        
        # 2. Verificar si el archivo se creó correctamente (Caso Fallido)
        if not file_path or not os.path.exists(file_path):
            guardar_descarga(
                url=request.url,
                video_title="Error en descarga",
                tipo=request.download_type,
                calidad=request.quality,
                estado="FAILED",
                file_size_mb=0.0,
                download_time_seconds=0.0
            )
            raise HTTPException(status_code=400, detail="El archivo no pudo ser descargado o no existe.")

        # 3. Registrar éxito completo en PostgreSQL pasándole los 7 parámetros correctos
        guardar_descarga(
            url=request.url,
            video_title=download_info["title"],
            tipo=request.download_type,
            calidad=request.quality,
            estado="SUCCESS",
            file_size_mb=download_info["file_size_mb"],
            download_time_seconds=download_info["download_time_seconds"]
        )

        # Generador dinámico cooperativo para transmitir y escuchar cancelaciones
        async def iterfile_live():
            try:
                with open(file_path, mode="rb") as file_like:
                    while True:
                        if await req_raw.is_disconnected():
                            print("🚨 El usuario canceló la descarga desde el Frontend. Deteniendo transmisión.")
                            break
                        
                        chunk = file_like.read(1024 * 64)  # Bloques de 64KB
                        if not chunk:
                            break
                        yield chunk
                        await asyncio.sleep(0.001)
            finally:
                eliminar_archivo(file_path)

        return StreamingResponse(
            iterfile_live(),
            media_type='application/octet-stream',
            headers={
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
            }
        )

    except Exception as e:
        # Registramos el fallo también en caso de una excepción crítica del sistema
        guardar_descarga(
            url=request.url,
            video_title="Error crítico de excepción",
            tipo=request.download_type,
            calidad=request.quality,
            estado="FAILED",
            file_size_mb=0.0,
            download_time_seconds=0.0
        )
        raise HTTPException(status_code=400, detail=str(e))