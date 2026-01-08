from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
import time
import random

console = Console()


# Ejemplo de "cola" del usuario
queue = {
    1: [],
    2: [25, 26, 27, 28, 29, 33],
    3: [35, 36, 37],
    4: [],
}


# Simulación de API -> cada lección tiene 1 a 3 videos
def fetch_videos_for_lesson(lesson_id):
    n_videos = random.randint(1, 3)
    videos = []
    for i in range(1, n_videos + 1):
        size = random.randint(20, 100)  # MB simulados
        videos.append(
            {
                "name": f"video_{lesson_id}_{i}.mp4",
                "size": size,
            }
        )
    return videos


def show_summary():
    table = Table(title="Resumen de descargas")
    table.add_column("Sección", justify="center", style="cyan", no_wrap=True)
    table.add_column("Lecciones", style="magenta")

    for sec, lessons in queue.items():
        lessons_str = ", ".join(map(str, lessons)) if lessons else "-"
        table.add_row(str(sec), lessons_str)

    console.print(table)


def download_all():
    completed = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[green]{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
        transient=True,  # limpia al terminar
    ) as progress:
        for sec, lessons in queue.items():
            if not lessons:
                continue

            console.print(f"\n[bold yellow]▶ Sección {sec}[/bold yellow]")
            for lesson in lessons:
                console.print(f"  [cyan]Lección {lesson}[/cyan]")

                videos = fetch_videos_for_lesson(lesson)

                for video in videos:
                    size = video["size"]
                    task = progress.add_task(f"Descargando {video['name']}", total=size)

                    downloaded = 0
                    while downloaded < size:
                        # Simulación de descarga (1–5 MB por iteración)
                        chunk = random.randint(1, 5)
                        time.sleep(0.05)
                        downloaded += chunk
                        progress.update(task, advance=chunk)

                    progress.remove_task(task)
                    completed.append(video["name"])
                    console.print(f"    [green]✔ {video['name']} descargado[/green]")

    console.print("\n[bold green]✅ Todas las descargas completadas[/bold green]\n")

    # Mostrar lista de completados
    table = Table(title="Videos descargados", show_lines=True)
    table.add_column("Video", style="cyan")
    for v in completed:
        table.add_row(v)
    console.print(table)


def main():
    console.print("\n[bold cyan]JW-Downloader - CLI[/bold cyan]\n", justify="center")
    show_summary()
    download_all()


if __name__ == "__main__":
    main()
