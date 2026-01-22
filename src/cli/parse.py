from argparse import ArgumentTypeError
from re import compile

SIZE_MULTIPLIERS = {
    "b": 10**0,
    "k": 10**3,
    "m": 10**6,
    "g": 10**9,
    "B": 10**0,
    "K": 10**3,
    "M": 10**6,
    "G": 10**9,
}
DURATION_MULTIPLIERS = {
    "s": 60**0,
    "m": 60**1,
    "h": 60**2,
    "S": 60**0,
    "M": 60**1,
    "H": 60**2,
}

DEFAULT_SIZE_MULT = "b"
DEFAULT_DURATION_MULT = "s"

COMMON_RE = r"(\d{1,}(\.\d{1,})?)"  # Any int or float number (the float must use dot notation, e.g.: 45.6, not 45,6)
SL_CHARS = "".join(SIZE_MULTIPLIERS.keys())
DL_CHARS = "".join(DURATION_MULTIPLIERS.keys())
SIZE_LIMIT_RE = compile(rf"{COMMON_RE}([{SL_CHARS}])?")
DURATION_LIMIT_RE = compile(rf"{COMMON_RE}([{DL_CHARS}])?")

ERR_MSG = "Incorrect format for {} limit: {}"


type SizeLimit = int  # in seconds
type DurationLimit = int  # in seconds


def parse_size_limit(size: str) -> SizeLimit:
    match = SIZE_LIMIT_RE.match(size)
    if match:
        ammount = match.group(1)
        multiplier = match.group(3) or DEFAULT_SIZE_MULT
        return int(float(ammount) * (SIZE_MULTIPLIERS[multiplier]))
    raise ArgumentTypeError(ERR_MSG.format("size", size))


def parse_duration_limit(duration: str) -> DurationLimit:
    match = DURATION_LIMIT_RE.match(duration)
    if match:
        ammount = match.group(1)
        multiplier = match.group(3) or DEFAULT_DURATION_MULT
        return int(float(ammount) * (DURATION_MULTIPLIERS[multiplier]))
    raise ArgumentTypeError(ERR_MSG.format("duration", duration))
