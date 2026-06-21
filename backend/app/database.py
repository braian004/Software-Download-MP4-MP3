import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import DATABASE_URL


def get_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def guardar_descarga(
    url,
    video_title,
    tipo,
    calidad,
    estado,
    file_size_mb,
    download_time_seconds
):

    conn = None

    try:

        conn = get_connection()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO downloads
            (
                url,
                video_title,
                tipo,
                calidad,
                estado,
                file_size_mb,
                download_time_seconds
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                url,
                video_title,
                tipo,
                calidad,
                estado,
                file_size_mb,
                download_time_seconds
            )
        )

        conn.commit()

        cur.close()

    except Exception as e:

        print(f"Error PostgreSQL: {e}")

    finally:

        if conn:
            conn.close()