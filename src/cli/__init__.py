from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Optional

from cli.parse import parse_duration_limit, parse_size_limit

DEFAULT_QUALITY = 720
DEFAULT_SIZE_LIMIT = None
DEFAULT_DURATION_LIMIT = None


@dataclass
class DesiredProps:
    quality: int = DEFAULT_QUALITY
    size_limit: Optional[int] = DEFAULT_SIZE_LIMIT
    duration_limit: Optional[int] = DEFAULT_DURATION_LIMIT


def argument_parser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument(
        "--quality",
        default=DEFAULT_QUALITY,
        dest="quality",
        help="desired quality to download",
    )
    parser.add_argument(
        "-s",
        "--size-limit",
        default=DEFAULT_SIZE_LIMIT,
        type=parse_size_limit,
        dest="size_limit",
        help="limit for the size of the video",
    )
    parser.add_argument(
        "-d",
        "--duration-limit",
        default=DEFAULT_DURATION_LIMIT,
        type=parse_duration_limit,
        dest="duration_limit",
        help="limit for the duration of the video",
    )

    sub = parser.add_subparsers(title="subcommand", required=True)

    p_section = sub.add_parser("section")
    p_section.add_argument("section")

    p_lesson = sub.add_parser("lesson")
    p_lesson.add_argument("lesson")

    return parser
