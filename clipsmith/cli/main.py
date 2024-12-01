"""
CLI entry point.
"""

import logging

import rich.traceback
import typer
from rich.console import Console
from rich.logging import RichHandler

rich.traceback.install(show_locals=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            console=Console(),
            show_level=True,
            show_time=True,
            show_path=False,
            markup=True,
        )
    ],
)

app = typer.Typer(
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def profiles():
    """
    Lists all available profiles.
    """


@app.command()
def forge():
    """
    Creates a new clip from one or more video files.
    """


def run():
    app()


if __name__ == "__main__":
    run()
