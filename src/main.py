from signal import signal, SIGINT, SIGTERM

from rich.progress import Progress
from rich.table import Table

from cli import parse_args
from constants import SECTION_ALL_RE, DEFAULT_TO_DOWNLOAD, AMMOUNT_OF_SECTIONS
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
            print(f"error: Incorrect format for size limit: {args.size_limit}")
            exit(1)
    if args.duration_limit != -1:
        try:
            args.duration_limit = parse_duration_limit(args.duration_limit)
        except ValueError:
            print(f"error: Incorrect format for duration limit: {args.duration_limit}")
            exit(1)

    jw_downloader = JWDownloader(
        quality=args.quality, max_size=args.size_limit, max_duration=args.duration_limit
    )

    if hasattr(args, "section"):
        try:
            match = SECTION_ALL_RE.match(args.section)
            if match:
                content_to_download = match.group(2) or DEFAULT_TO_DOWNLOAD
                sections = [
                    (section, content_to_download)
                    for section in range(1, AMMOUNT_OF_SECTIONS + 1)
                ]
            else:
                sections = list(
                    expand_ranges(
                        parse_spec_to_ranges(args.section), min_value=1, max_value=4
                    )
                )
            jw_downloader.add_sections_to_queue(sections)
        except ValueError:
            parser.print_help()
            exit(1)
    elif hasattr(args, "lesson"):
        lessons = list(
            expand_ranges(parse_spec_to_ranges(args.lesson), min_value=0, max_value=60)
        )
        jw_downloader.add_lessons_to_queue(lessons)
    else:
        parser.print_help()
        exit(1)

    console.print("\n[bold cyan]JW-Downloader - CLI[/bold cyan]\n", justify="center")

    jw_downloader.exec(console)

    completed = jw_downloader.start_download(console)

    console.print("\n[bold green]✅ Todas las descargas completadas[/bold green]\n")

    # Mostrar lista de completados
    table = Table(title="Videos descargados", show_lines=True)
    table.add_column("Video", style="cyan")
    for v in completed:
        table.add_row(v)
    console.print(table)


if __name__ == "__main__":
    main()
