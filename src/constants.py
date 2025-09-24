import re


SECTION_MULTIMEDIA_URL = "https://www.jw.org/es/biblioteca/libros/disfrute-vida-para-siempre/seccion-%s/multimedia/"
SECTIONS = {
    1: (0, 12),
    2: (13, 33),
    3: (34, 47),
    4: (48, 60),
}
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
LESSON_NUMBER_RE = re.compile(r"^(\d{1,2})\s+.*")
SIZE_LIMIT_RE = re.compile(r"^(\d{1,}(\.\d{1,})?)(b|k|m|g|B|K|M|G)?")
DURATION_LIMIT_RE = re.compile(r"^(\d{1,}(\.\d{1,})?)(s|m|h|S|M|H)?")
SECTION_ALL_RE = re.compile(r"^all([|.](a(ll)?|m(ain)?|e(xtra)?))?$")
DEFAULT_TO_DOWNLOAD = "main"
AMMOUNT_OF_SECTIONS = 4
