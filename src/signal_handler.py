from console import console


def signal_handler(signal, frame):
    console.print("\n[bold red]Interruption Received. Exitting ...[/]")

    exit(1)
