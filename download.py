import requests
import sys
from pathlib import Path


def descargar_archivo(url, nombre_archivo=None):
    """
    Descarga un archivo desde una URL mostrando una barra de progreso animada.
    """

    # Si no se pasa nombre, lo toma del final de la URL
    if nombre_archivo is None:
        nombre_archivo = Path(url.split("?")[0]).name or "archivo_descargado"

    # Hace la petición HTTP con streaming
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        descargado = 0
        bloque = 8192  # tamaño del bloque de descarga

        with open(nombre_archivo, "wb") as f:
            for chunk in r.iter_content(chunk_size=bloque):
                if chunk:
                    f.write(chunk)
                    descargado += len(chunk)

                    # Calcula el progreso
                    if total > 0:
                        porcentaje = descargado / total
                        barra = "#" * int(porcentaje * 40)
                        espacios = " " * (40 - len(barra))
                        sys.stdout.write(
                            f"\rDescargando: [{barra}{espacios}] {porcentaje:.1%}"
                        )
                        sys.stdout.flush()
