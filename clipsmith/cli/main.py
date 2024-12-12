"""
CLI entry point.
"""

import logging
from pathlib import Path

import rich.traceback
import typer
from rich.console import Console
from rich.logging import RichHandler

from ..clip import DurationParams, OperationParams, ResolutionParams
from ..context import Context

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
def forge(
    trim_start: float
    | None = typer.Option(None, help="Start offset (seconds) in input file(s)"),
    trim_end: float
    | None = typer.Option(None, help="End offset (seconds) in input file(s)"),
    dur_scale: float
    | None = typer.Option(None, help="Scale duration by scale factor"),
    dur_target: float
    | None = typer.Option(None, help="Scale duration to target"),
    res_scale: float
    | None = typer.Option(None, help="Scale resolution by scale factor"),
    res_target: str
    | None = typer.Option(
        None, help="Scale resolution to target as WIDTH:HEIGHT"
    ),
    audio: bool = typer.Option(
        False,
        help="Whether to pass through audio to output (not yet supported with time scaling)",
    ),
    inputs: list[Path] = typer.Argument(
        help="One or more paths to input video(s) or folder(s) of video(s)"
    ),
    output: Path = typer.Argument(help="Path to output video"),
):
    """
    Creates a new clip from one or more video files.
    """

    def convert_res(res: str) -> tuple[int, int]:
        split = res.split(":")
        if len(split) != 2:
            raise ValueError(f"Unable to parse resolution: {res}")
        return int(split[0]), int(split[1])

    # convert resolution target as typer assumes there can be multiple tuples
    res_target_ = None if res_target is None else convert_res(res_target)

    # setup context and operation
    context = Context()
    operation = OperationParams(
        duration_params=DurationParams(
            scale=dur_scale,
            target=dur_target,
            trim_start=trim_start,
            trim_end=trim_end,
        ),
        resolution_params=ResolutionParams(
            scale=res_scale,
            res_target=res_target_,
        ),
        audio=audio,
    )

    # setup forge task
    context.forge(output, inputs, operation=operation)

    # do it
    context.doit()


# TODO: after profiles implemented
# @app.command()
# def profiles():
#    """
#    Lists all available profiles.
#    """


def run():
    app()


if __name__ == "__main__":
    run()
