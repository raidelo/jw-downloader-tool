#!/usr/bin/env python3
from typing import List, Tuple, Optional, Generator
import argparse
import re

# ----------------------------
# Tipos
# ----------------------------
Endpoint = Optional[Tuple[int, str]]  # (numero, sufijo) o None (abierto)
Range = Tuple[Endpoint, Endpoint]

# sufijos válidos
VALID_SUFFIXES = {"a", "m", "e"}
DEFAULT_SUFFIX = "m"

# regex: numero + sufijo opcional (1 letra de a/m/e)
TOKEN_RE = re.compile(r"^(\d+)([ame]?)$")


# ----------------------------
# Parseo
# ----------------------------
def parse_token(token: str) -> Tuple[int, str]:
    """Convierte un token como '5a', '21m', '15' en (numero, sufijo)."""
    m = TOKEN_RE.match(token)
    if not m:
        raise ValueError(f"Token inválido: '{token}'")
    num = int(m.group(1))
    suffix = m.group(2) or DEFAULT_SUFFIX
    if suffix not in VALID_SUFFIXES:
        raise ValueError(f"Sufijo inválido en token '{token}' (solo {VALID_SUFFIXES})")
    return (num, suffix)


def parse_spec_to_ranges(spec: str) -> List[Range]:
    """
    Parsea un spec estilo nmap pero con sufijos opcionales [a,m,e].
    Ejemplos:
      '5a,7-9e,15,21m-' ->
      [((5,'a'),(5,'a')), ((7,'a'),(9,'e')), ((15,'a'),(15,'a')), ((21,'m'), None)]
    """
    if spec is None:
        return []
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    ranges: List[Range] = []
    for p in parts:
        if "-" in p:
            left, right = p.split("-", 1)
            left, right = left.strip(), right.strip()
            if left == "" and right == "":
                raise ValueError(f"Rango inválido: '{p}'")
            start: Endpoint = None if left == "" else parse_token(left)
            end: Endpoint = None if right == "" else parse_token(right)
            if start and end and start[0] > end[0]:
                raise ValueError(f"Rango inválido inicio > fin en '{p}'")
            ranges.append((start, end))
        else:
            tok = parse_token(p)
            ranges.append((tok, tok))
    return ranges


# ----------------------------
# Expansión
# ----------------------------
def expand_ranges(
    ranges: List[Range],
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    limit: Optional[int] = None,
) -> Generator[Tuple[int, str], None, None]:
    """
    Expande los ranges en una secuencia de (int, sufijo).
    Si un extremo es None, requiere min_value o max_value.
    Si ambos extremos son None -> error.
    limit: corta después de generar 'limit' elementos.
    """
    produced = 0
    for start, end in ranges:
        if start is None and end is None:
            raise ValueError(
                "Rango '-' completamente abierto no es expandible sin límites."
            )

        # resolver extremos abiertos
        if start is None:
            if min_value is None:
                raise ValueError(f"Extremo izquierdo abierto requiere min_value.")
            start = (min_value, end[1])
        if end is None:
            if max_value is None:
                raise ValueError(f"Extremo derecho abierto requiere max_value.")
            end = (max_value, start[1])

        s_num, s_suf = start
        e_num, e_suf = end

        if s_num > e_num:
            raise ValueError(f"Rango inválido: {s_num}>{e_num}")

        # generamos todos los enteros con sufijo
        for n in range(s_num, e_num + 1):
            # si estamos justo en el límite derecho y tenía un sufijo especial -> usarlo
            if n == e_num:
                suf = e_suf or DEFAULT_SUFFIX
            else:
                suf = s_suf or DEFAULT_SUFFIX
            yield (n, suf)
            produced += 1
            if limit is not None and produced >= limit:
                return


# ----------------------------
# Compactar
# ----------------------------
def compress_ranges(ranges: List[Range]) -> str:
    """Convierte los ranges de vuelta a string."""
    parts = []
    for a, b in ranges:
        if a is None and b is None:
            parts.append("-")
        elif a is None:
            parts.append(f"-{b[0]}{b[1]}")
        elif b is None:
            parts.append(f"{a[0]}{a[1]}-")
        elif a == b:
            parts.append(f"{a[0]}{a[1]}")
        else:
            parts.append(f"{a[0]}{a[1]}-{b[0]}{b[1]}")
    return ",".join(parts)


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
        ranges = parse_spec_to_ranges(args.spec)
    except ValueError as e:
        print("Error al parsear:", e)
        raise SystemExit(1)

    print("Rangos parseados:", ranges)
    print("Compacto:", compress_ranges(ranges))

    if args.expand:
        try:
            expanded = list(
                expand_ranges(
                    ranges, min_value=args.minv, max_value=args.maxv, limit=args.limit
                )
            )
        except ValueError as e:
            print("Error al expandir:", e)
            raise SystemExit(1)
        print(
            f"Expandido ({len(expanded)} elementos): {expanded if len(expanded) <= 200 else '... (demasiados)'}"
        )


if __name__ == "__main__":
    main()
