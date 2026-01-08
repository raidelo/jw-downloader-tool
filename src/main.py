from cli import argument_parser
from console import console
from downloader import JWDownloader
from subcmd_handling.lesson import handler_lesson_subcmd
from subcmd_handling.section import handler_section_subcmd


def main() -> None:
    args = argument_parser().parse_args()

    jw_downloader = JWDownloader(
        quality=args.quality,
        max_size=args.size_limit,
        max_duration=args.duration_limit,
    )

    if hasattr(args, "section"):
        handler_section_subcmd(args=args, jw_downloader=jw_downloader)
    elif hasattr(args, "lesson"):
        handler_lesson_subcmd(args=args, jw_downloader=jw_downloader)
    else:
        raise ValueError("unreachable")  # first subcommand is required

    console.print("\n[bold cyan]JW-Downloader - CLI[/bold cyan]\n", justify="center")

    jw_downloader.exec(console=console)

    summary_table = jw_downloader.summary_table()
    console.print(summary_table)

    jw_downloader.start_download(console)

    console.print("\n[bold green]✅ Todas las descargas completadas[/bold green]\n")

    completed_table = jw_downloader.completed_table()
    console.print(completed_table)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Interruption Received. Exitting ...[/]")
        exit(1)
