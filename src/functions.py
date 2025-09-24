from constants import SIZE_LIMIT_RE, DURATION_LIMIT_RE
from pathlib import Path


def mkdirs(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def rm_wrong_chars(s: str) -> str:
    r"""Remves following chars from the string:
    < (less than)
    > (greater than)
    : (colon - sometimes works, but is actually NTFS Alternate Data Streams)
    " (double quote)
    / (forward slash)
    \ (backslash)
    | (vertical bar or pipe)
    ? (question mark)
    * (asterisk)
    """
    chars = r'<>:"/\|?*'
    return "".join([c for c in s if c not in chars])


def parse_size_limit(size: str) -> int:
    match = SIZE_LIMIT_RE.match(size)
    multipliers = {
        "b": 10**0,
        "k": 10**3,
        "m": 10**6,
        "g": 10**9,
        "B": 10**0,
        "K": 10**3,
        "M": 10**6,
        "G": 10**9,
    }
    if match:
        ammount = match.group(1)
        multiplier = match.group(3)
        return int(float(ammount) * (multipliers[multiplier] if multiplier else 1))
    else:
        raise ValueError("Incorrect format for size limit")


def parse_duration_limit(size: str) -> int:
    match = DURATION_LIMIT_RE.match(size)
    multipliers = {
        "s": 60**0,
        "m": 60**1,
        "h": 60**2,
        "S": 60**0,
        "M": 60**1,
        "H": 60**2,
    }
    if match:
        ammount = match.group(1)
        multiplier = match.group(3)
        return int(float(ammount) * (multipliers[multiplier] if multiplier else 1))
    else:
        raise ValueError("Incorrect format for duration limit")
