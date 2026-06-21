import os
import time

DOWNLOAD_FOLDER = "app/downloads"

def limpiar_descargas(horas=1):

    ahora = time.time()

    if not os.path.exists(DOWNLOAD_FOLDER):
        return

    for archivo in os.listdir(DOWNLOAD_FOLDER):

        ruta = os.path.join(DOWNLOAD_FOLDER, archivo)

        if os.path.isfile(ruta):

            antiguedad = ahora - os.path.getmtime(ruta)

            if antiguedad > horas * 3600:

                try:
                    os.remove(ruta)
                    print(f"🗑️ Eliminado: {archivo}")

                except Exception as e:
                    print(f"❌ Error eliminando {archivo}: {e}")