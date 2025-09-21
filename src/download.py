from requests import get
from pathlib import Path


def download_archive(url, path: Path | None = None, resume: bool = True):
    """
    Descarga un archivo desde una URL con capacidad de reanudar la rescarga
    """

    # Si no se pasa nombre, lo toma del final de la URL
    if path is None:
        filename = Path(url.split("?")[0]).name or "archivo_descargado"
        path = Path().joinpath(filename)

    headers = {}
    written = 0
    open_mode = "wb"

    if resume and path.exists():
        written = path.stat().st_size
        if written != 0:
            open_mode = "ab"
            headers = {"Range": f"bytes={written + 1}-"}

    with open(path, open_mode) as f:
        chunk = 4096  # tamaño del bloque de descarga

        with get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=chunk):
                if chunk:
                    yield f.write(chunk)
