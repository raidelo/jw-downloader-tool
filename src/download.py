from pathlib import Path

from http_client_session import session


def download_archive(
    url: str,
    expected_size: int | None = None,
    path: Path | None = None,
    resume: bool = True,
):
    """
    Descarga un archivo desde una URL con capacidad de reanudar la rescarga
    """

    if path is None:
        filename = Path(url.split("?")[0]).name or "archivo_descargado"
        path = Path().joinpath(filename)

    headers = {}
    written = 0
    open_mode = "wb"

    if resume and path.exists():
        written = path.stat().st_size
        if written == expected_size:
            yield written
            return
        elif written > 0:
            open_mode = "ab"
            headers["Range"] = f"bytes={written}-"
            yield written

    with open(path, open_mode) as f:
        chunk = 4096

        with session.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=chunk):
                if chunk:
                    yield f.write(chunk)
