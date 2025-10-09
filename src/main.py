from signal import signal, SIGINT, SIGTERM

from cli import parse_args
from constants import ALL_SECTIONS_RE, DEFAULT_TO_DOWNLOAD, AMMOUNT_OF_SECTIONS
from console import console
from functions import parse_size_limit, parse_duration_limit
from jw_downloader import JWDownloader
from parsing import parse_spec_to_ranges, expand_ranges
from signal_handler import signal_handler


signal(SIGINT, signal_handler)
signal(SIGTERM, signal_handler)


def main():
    parser, args = parse_args()

    if args.size_limit != -1:
        try:
            args.size_limit = parse_size_limit(args.size_limit)
        except ValueError:
            console.print(
                f"[bold][red]error:[/red] [white]Formato incorrecto para el límite de tamaño: {args.size_limit}[/]"
            )
            exit(1)
    if args.duration_limit != -1:
        try:
            args.duration_limit = parse_duration_limit(args.duration_limit)
        except ValueError:
            console.print(
                f"[bold][red]error:[/red] [white]Formato incorrecto para el límite de duración: {args.duration_limit}[/]"
            )
            exit(1)

    jw_downloader = JWDownloader(
        quality=args.quality, max_size=args.size_limit, max_duration=args.duration_limit
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
                exit(1)
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
            exit(1)
        jw_downloader.add_lessons_to_queue(lessons)
    else:
        parser.print_help()
        exit(1)

    console.print("\n[bold cyan]JW-Downloader - CLI[/bold cyan]\n", justify="center")

    jw_downloader.exec()

    summary_table = jw_downloader.summary_table()
    console.print(summary_table)

    jw_downloader.start_download()

    console.print("\n[bold green]\u2705 Todas las descargas completadas[/bold green]\n")

    completed_table = jw_downloader.completed_table()
    if completed_table:
        console.print(completed_table)


if __name__ == "__main__":
    main()
