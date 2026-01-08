from argparse import ArgumentTypeError
from re import compile


SIZE_LIMIT_RE = compile(r"^(\d{1,}(\.\d{1,})?)([bkmgBKMG])?")
DURATION_LIMIT_RE = compile(r"^(\d{1,}(\.\d{1,})?)([smhSMH])?")

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
DEFAULT_SIZE_MULT = "b"

DURATION_MULTIPLIERS = {
    "s": 60**0,
    "m": 60**1,
    "h": 60**2,
    "S": 60**0,
    "M": 60**1,
    "H": 60**2,
}
DEFAULT_DURATION_MULT = "s"

ERR_MSG = "Incorrect format for {} limit: {}"


type SizeLimitInSeconds = int
type DurationLimitInSeconds = int


def parse_size_limit(size: str) -> SizeLimitInSeconds:
    match = SIZE_LIMIT_RE.match(size)
    if match:
        ammount = match.group(1)
        multiplier = match.group(3) or DEFAULT_SIZE_MULT
        return int(float(ammount) * (SIZE_MULTIPLIERS[multiplier]))
    raise ArgumentTypeError(ERR_MSG.format("size", size))


def parse_duration_limit(duration: str) -> DurationLimitInSeconds:
    match = DURATION_LIMIT_RE.match(duration)
    if match:
        ammount = match.group(1)
        multiplier = match.group(3) or DEFAULT_DURATION_MULT
        return int(float(ammount) * (DURATION_MULTIPLIERS[multiplier]))
    raise ArgumentTypeError(ERR_MSG.format("duration", duration))
