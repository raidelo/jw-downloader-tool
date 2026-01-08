#!/usr/bin/env python3
from dataclasses import dataclass
from typing import List, Tuple, Optional, Generator
import argparse
import re

from types_ import VideoGroup


INVALID_TOKEN = "Token inválido: {token!r}"
ERR_INVALID_RANGE = "Rango inválido {start_n}-{end_n}: {start_n}>{end_n}"
ERR_OPEN_RANGE = "Rango '-' completamente abierto. Tanto `min_value` como `max_value` son obligatorios."
ERR_OPEN_WO_DELIM = (
    "Extremo {side} del rango abierto sin limites. `{field}` es obligatorio."
)
ERR_NON_MATCHING_SUFFIXES = "Rango inválido: los sufijos no coinciden: {suffix}"

DEFAULT_SUFFIX = VideoGroup.PRIMARY

TOKEN_RE = re.compile(
    r"^(\d+)([{suffixes}])?$".format(suffixes="".join([i.value for i in VideoGroup]))
)


type OptSuffix = Optional[VideoGroup]
type Range = Tuple[int, int, VideoGroup]  # (start, end, suffix)


@dataclass
class TokenPair[T]:
    n: int
    suffix: T


def parse_token(token: str) -> TokenPair[OptSuffix]:
    m = TOKEN_RE.match(token)
    if not m:
        raise ValueError(INVALID_TOKEN.format(token=token))
    num = int(m.group(1))
    suffix: Optional[str] = m.group(2)
    return TokenPair(num, VideoGroup(suffix) if suffix is not None else suffix)


def parse_spec_to_ranges(
    spec: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    default_suffix: VideoGroup = DEFAULT_SUFFIX,
) -> List[Range]:
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    ranges: List[Range] = []
    for p in parts:
        if "-" in p:
            l, r = p.split("-", 1)
            l, r = l.strip(), r.strip()

            if l == "" and not min_value and r == "" and not max_value:
                raise ValueError(ERR_OPEN_RANGE)

            if l == "":
                if not min_value:
                    raise ValueError(
                        ERR_OPEN_WO_DELIM.format(side="izquierdo", field="min_value")
                    )
                left = TokenPair[OptSuffix](min_value, None)
            else:
                left = parse_token(l)
            if r == "":
                if not max_value:
                    raise ValueError(
                        ERR_OPEN_WO_DELIM.format(side="derecho", field="max_value")
                    )
                right = TokenPair[OptSuffix](max_value, None)
            else:
                right = parse_token(r)

            if left.n > right.n:
                raise ValueError(
                    ERR_INVALID_RANGE.format(start_n=left.n, end_n=right.n)
                )

            if not left.suffix and right.suffix:
                left.suffix = right.suffix
            elif left.suffix and not right.suffix:
                right.suffix = left.suffix

            if left.suffix != right.suffix:
                raise ValueError(ERR_NON_MATCHING_SUFFIXES.format(suffix=p))

            ranges.append(
                (left.n, right.n, left.suffix or right.suffix or default_suffix)
            )
        else:
            tok = parse_token(p)
            ranges.append((tok.n, tok.n, tok.suffix or default_suffix))

    return ranges


def expand_ranges(ranges: List[Range]) -> Generator[TokenPair, None, None]:
    for start, end, suffix in ranges:
        if start > end:
            raise ValueError(ERR_INVALID_RANGE.format(start_n=start, end_n=end))

        for n in range(start, end + 1):
            yield TokenPair(n, suffix)


# ----------------------------
# Main CLI
# ----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Parseador estilo nmap con sufijos [a,m,e]."
    )
    parser.add_argument("spec", help='Ejemplo: "5a,7-9e,15,21m-"')
    parser.add_argument(
        "--min",
        type=int,
        default=None,
        dest="minv",
        help="Valor mínimo para extremos abiertos",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        dest="maxv",
        help="Valor máximo para extremos abiertos",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Máx. elementos a expandir"
    )
    parser.add_argument(
        "--expand", action="store_true", help="Expandir a lista de valores concretos"
    )
    args = parser.parse_args()

    try:
        ranges = parse_spec_to_ranges(
            args.spec,
            min_value=args.minv,
            max_value=args.maxv,
        )
    except ValueError as e:
        print("Error al parsear:", e)
        raise SystemExit(1)

    print("Rangos parseados:", ranges)

    if args.expand:
        try:
            expanded = list(expand_ranges(ranges))
        except ValueError as e:
            print("Error al expandir:", e)
            raise SystemExit(1)
        print(
            f"Expandido ({len(expanded)} elementos): {expanded if len(expanded) <= 200 else '... (demasiados)'}"
        )


if __name__ == "__main__":
    main()
