from pathlib import Path
from typing import Generator, Optional
from requests import Response, request


DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

DEFAULT_DOWNLOAD_FILENAME = "archivo_descargado"


def custom_req(*args, **kwargs) -> Response:
    """
    Sends an HTTP request with a default User-Agent header.

    Args:
        *args: Positional arguments to pass to `requests.request`.
        **kwargs: Keyword arguments to pass to `requests.request`.

    Returns:
        Response object from the request.
    """
    headers = kwargs.pop("headers", {})
    headers["User-Agent"] = DEFAULT_USER_AGENT
    kwargs["headers"] = headers

    kwargs["stream"] = True

    return request(*args, **kwargs)


def custom_get(*args, **kwargs) -> Response:
    """
    Sends a GET request with the default User-Agent header.

    Args:
        *args: Positional arguments to pass to `custom_req`.
        **kwargs: Keyword arguments to pass to `custom_req`.

    Returns:
        Response object from the GET request.
    """
    return custom_req("GET", *args, **kwargs)


def download_archive(
    url: str,
    path: Optional[Path] = None,
    resume: bool = True,
) -> Generator[int, None, None]:
    """
    Downloads a file from the given URL, optionally resuming a partial download.

    Args:
        url: URL of the file to download.
        path: Local path where the file will be saved. If None, the filename
            is derived from the URL or defaults to a predefined name.
        resume: Whether to attempt resuming an incomplete download if the
            local file exists and the server supports HTTP Range.

    Yields:
        The total number of bytes written after each chunk is downloaded.

    Notes:
        - If the file already exists and the server provides `Content-Length`,
          the function checks whether the download is complete and returns immediately.
        - If the server supports HTTP Range, the function resumes incomplete downloads.
        - Data is written in chunks of 4096 bytes.
        - Servers that do not provide `Content-Length` or do not support Range
          will result in a full download from scratch.
    """
    if path is None:
        filename = Path(url.split("?")[0]).name or DEFAULT_DOWNLOAD_FILENAME
        path = Path(filename)

    headers = {}
    local_size = 0
    open_mode = "wb"

    if path.exists() and resume:
        local_size = path.stat().st_size
        total_size = custom_req(method="HEAD", url=url).headers.get("Content-Length")
        if total_size is not None:
            total_size = int(total_size)
            if local_size >= total_size:
                yield local_size
                return

            headers["Range"] = f"bytes={local_size}-"
            open_mode = "ab"
            yield local_size

    chunk_size = 4096

    with (
        open(path, open_mode) as f,
        custom_get(url=url, stream=True, headers=headers) as resp,
    ):
        resp.raise_for_status()
        for data in resp.iter_content(chunk_size=chunk_size):
            if data:
                f.write(data)
                local_size += len(data)
                yield local_size


def mkdirs(path: Path) -> Path:
    """
    Creates a directory and all its parent directories if they do not exist.

    Args:
        path: Path of the directory to create.

    Returns:
        The same `Path` object passed as argument.

    Notes:
        - If the directory already exists, no error is raised.
        - Equivalent to `mkdir -p` in Unix.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(text: str) -> str:
    """
    Removes characters that are invalid in filenames from a string.

    Args:
        text: Input string.

    Returns:
        A new string with the characters '<', '>', ':', '"', '/', '\\', '|', '?', '*' removed.

    Notes:
        - Useful for sanitizing strings to be used as filenames.
    """
    chars = r'<>:"/\|?*'
    return "".join([c for c in text if c not in chars])
