from signal import SIGINT, SIGTERM, signal

from cli import argument_parser
from console import console
from constants import ALL_SECTIONS_RE, AMMOUNT_OF_SECTIONS, DEFAULT_TO_DOWNLOAD
from jw_downloader import JWDownloader
from parsing import expand_ranges, parse_spec_to_ranges
from signal_handler import signal_handler
from utils import parse_duration_limit, parse_size_limit

signal(SIGINT, signal_handler)
signal(SIGTERM, signal_handler)

INVALID_FORMAT = (
    "[bold][red]error:[/red] [white]Formato incorrecto para el límite de {}: {}[/]"
)


def main() -> int:
    parser = argument_parser()
    args = parser.parse_args()

    if args.size_limit is not None:
        try:
            args.size_limit = parse_size_limit(args.size_limit)
        except ValueError:
            console.print(INVALID_FORMAT.format("tamaño", args.size_limit))
            return 1
    if args.duration_limit is not None:
        try:
            args.duration_limit = parse_duration_limit(args.duration_limit)
        except ValueError:
            console.print(INVALID_FORMAT.format("duración", args.duration_limit))
            return 1

    jw_downloader = JWDownloader(
        quality=args.quality,
        size_limit=args.size_limit,
        duration_limit=args.duration_limit,
    )

    if hasattr(args, "section"):
        match = ALL_SECTIONS_RE.match(args.section)
        if match:
            sub_section = match.group(2) or DEFAULT_TO_DOWNLOAD
            sections = [
                (section, sub_section) for section in range(1, AMMOUNT_OF_SECTIONS + 1)
            ]
        else:
            try:
                sections = list(
                    expand_ranges(
                        parse_spec_to_ranges(args.section), min_value=1, max_value=4
                    )
                )
            except ValueError as e:
                console.print(f"[bold][red]error:[/red] [white]{''.join(e.args)}[/]")
                return 1
        jw_downloader.add_sections_to_queue(sections)
    elif hasattr(args, "lesson"):
        try:
            lessons = list(
                expand_ranges(
                    parse_spec_to_ranges(args.lesson), min_value=0, max_value=60
                )
            )
        except ValueError as e:
            console.print(f"[bold][red]error:[/red] [white]{''.join(e.args)}[/]")
            return 1
        jw_downloader.add_lessons_to_queue(lessons)
    else:
        parser.print_help()
        return 1

    console.print("\n[bold cyan]JW-Downloader - CLI[/bold cyan]\n", justify="center")

    jw_downloader.exec()

    summary_table = jw_downloader.summary_table()
    console.print(summary_table)

    jw_downloader.start_download()

    console.print("\n[bold green]\u2705 Todas las descargas completadas[/bold green]\n")

    completed_table = jw_downloader.completed_table()
    if completed_table:
        console.print(completed_table)

    return 0


if __name__ == "__main__":
    exit(main())
