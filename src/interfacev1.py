from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import time

from constants import SECTIONS

console = Console()


def show_header():
    console.print("\n[b][cyan]📘 JW-Downloader - CLI[/cyan][/b]\n", justify="center")


def show_sections():
    table = Table(title="Secciones del Curso", show_lines=True)

    table.add_column("Sección", style="bold magenta", justify="center")
    table.add_column("Rango de lecciones", style="cyan", justify="center")

    table.add_row("1", "1 - 15")
    table.add_row("2", "16 - 33")
    table.add_row("3", "34 - 45")
    table.add_row("4", "46 - 60")

    console.print(table)


def download_lessons(lessons):
    console.print(
        f"\n[bold green]Iniciando descarga de {len(lessons)} lecciones...[/bold green]\n"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[green]{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Descargando", total=len(lessons))

        for lesson in lessons:
            # Simulación de descarga (tú pondrías aquí tu lógica real)
            time.sleep(0.05)
            progress.update(task, advance=1)

    console.print("\n[bold green]✅ Descarga finalizada con éxito[/bold green]\n")


def main():
    show_header()
    show_sections()

    # Simulación: usuario elige sección 2
    chosen = 2
    console.print(f"[yellow]Has elegido la sección {chosen}[/yellow]\n")

    # Generar lista de lecciones según sección
    lessons = list(range(*SECTIONS[chosen]))

    download_lessons(lessons)


if __name__ == "__main__":
    main()
