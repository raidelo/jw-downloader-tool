import re


SECTION_MULTIMEDIA_URL = "https://www.jw.org/es/biblioteca/libros/disfrute-vida-para-siempre/seccion-%s/multimedia/"
SECTIONS = {
    1: (0, 12),
    2: (13, 33),
    3: (34, 47),
    4: (48, 60),
}
SUB_SECTIONS = {
    "all": "a",
    "main": "m",
    "extra": "e",
    "a": "a",
    "m": "m",
    "e": "e",
}
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
LESSON_NUMBER_RE = re.compile(r"^(\d{1,2})\s+.*")
SIZE_LIMIT_RE = re.compile(r"^(\d{1,}(\.\d{1,})?)([bkmgBKMG])?")
DURATION_LIMIT_RE = re.compile(r"^(\d{1,}(\.\d{1,})?)([smhSMH])?")
ALL_SECTIONS_RE = re.compile(r"^all([|.](a(ll)?|m(ain)?|e(xtra)?))?$")
DEFAULT_TO_DOWNLOAD = "main"
AMMOUNT_OF_SECTIONS = 4
BOOK_TITLE = "Disfrute de la vida para siempre!"
EXTRA_SUB_SECTION = "Descubra algo más"
