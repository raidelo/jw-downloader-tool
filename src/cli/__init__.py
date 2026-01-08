from argparse import ArgumentParser

from cli.parse import parse_duration_limit, parse_size_limit


def argument_parser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument(
        "--quality",
        default="720",
        dest="quality",
        help="desired quality to download",
    )
    parser.add_argument(
        "-s",
        "--size-limit",
        default=None,
        type=parse_size_limit,
        dest="size_limit",
        help="limit for the size of the video",
    )
    parser.add_argument(
        "-d",
        "--duration-limit",
        default=None,
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
