<!-- TODO: logo using glyphsynth -->

# ClipSmith
Utility to work with video clips, especially suited for dashcam footage

[![Python versions](https://img.shields.io/pypi/pyversions/clipsmith.svg)](https://pypi.org/project/clipsmith)
[![PyPI](https://img.shields.io/pypi/v/clipsmith?color=%2334D058&label=pypi%20package)](https://pypi.org/project/clipsmith)
[![Tests](./badges/tests.svg?dummy=8484744)]()
[![Coverage](./badges/cov.svg?dummy=8484744)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

- [ClipSmith](#clipsmith)
  - [Overview](#overview)
  - [Getting started](#getting-started)
  - [CLI](#cli)
    - [Forging clips](#forging-clips)
      - [Concatenating](#concatenating)
      - [Trimming](#trimming)
      - [Rescaling](#rescaling)
    - [Input folder caching](#input-folder-caching)
  - [API](#api)
    - [Context](#context)
    - [Clips](#clips)

## Overview

This project leverages [FFmpeg](https://ffmpeg.org/) and [doit](https://pydoit.org/) to provide a user-friendly utility for working with video clips and orchestrating pipelines of video editing operations. Clips can be readily concatenated, trimmed, and/or rescaled in a single command. This is especially useful for working with dashcam footage wherein there are many short video files to manage.

## Getting started

First, ensure you have ffmpeg installed:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

Then install using pip:

```bash
pip install clipsmith
```

## CLI

### Forging clips

The command `clipsmith forge` is the entry point for creating new clips. Operations for concatenation, duration trimming, duration scaling, resolution scaling, and audio can be specified together in one command.

<!-- include doc/cli/forge.md -->
```
Usage: clipsmith forge [OPTIONS] INPUTS... OUTPUT                                                                                                            
                                                                                                                                                              
 Create a video from one or more videos with specified operations applied                                                                                     
                                                                                                                                                              
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    inputs      INPUTS...  One or more paths to input video(s) or folder(s) of videos [default: None] [required]                                          │
│ *    output      PATH       Path to output video [default: None] [required]                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --trim-start                  FLOAT  Start offset (seconds) in input file(s) [default: None]                                                               │
│ --trim-end                    FLOAT  End offset (seconds) in input file(s) [default: None]                                                                 │
│ --dur-scale                   FLOAT  Scale duration by scale factor [default: None]                                                                        │
│ --dur-target                  FLOAT  Scale duration to target (seconds) [default: None]                                                                    │
│ --res-scale                   FLOAT  Scale resolution by scale factor [default: None]                                                                      │
│ --res-target                  TEXT   Scale resolution to target as WIDTH:HEIGHT [default: None]                                                            │
│ --audio         --no-audio           Whether to pass through audio to output (not yet supported with time scaling) [default: audio]                        │
│ --cache         --no-cache           Whether to store a cache of video metadata in input folders [default: no-cache]                                       │
│ --log-level                   TEXT   Log level passed to ffmpeg [default: info]                                                                            │
│ --help                               Show this message and exit.                                                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

<!-- include end -->

#### Concatenating

Concatenate multiple clips into a single one:

```bash
# Combine specific files
clipsmith forge clip1.mp4 clip2.mp4 combined.mp4

# Combine all clips from a folder
clipsmith forge input_folder/ combined.mp4
```

For any folders passed as inputs, their contents are recursively scanned depth-first to aggregate input videos.

#### Trimming

Trim clips using start and end time offsets:

```bash
# Trim to specific time range
clipsmith forge --trim-start 1.0 --trim-end 5.0 input.mp4 output.mp4

# Trim just the start
clipsmith forge --trim-start 1.0 input.mp4 output.mp4

# Trim just the end
clipsmith forge --trim-end 5.0 input.mp4 output.mp4
```

#### Rescaling

Rescale video duration and resolution:

```bash
# Speed up by factor (e.g. 2x faster)
clipsmith forge --dur-scale 2.0 --no-audio input.mp4 output.mp4

# Slow down by factor (e.g. 2x slower)
clipsmith forge --dur-scale 0.5 --no-audio input.mp4 output.mp4

# Rescale duration to specific value in seconds
clipsmith forge --dur-target 60.0 --no-audio input.mp4 output.mp4

# Rescale resolution by factor
clipsmith forge --res-scale 0.5 input.mp4 output.mp4

# Rescale resolution to specific value as WIDTH:HEIGHT
clipsmith forge --res-target 480:270 input.mp4 output.mp4
```

<!-- TODO:
### Clip playbooks
-->

### Input folder caching

For input folders with many videos, the process of scanning and validating input files can be time-consuming. In such cases, pass `--cache` to cache video metadata per folder. In case of multiple or interrupted invocations, ClipSmith will use this cache to quickly begin its work.

## API

### Context

The `Context` class provides the main interface for working with clips. It implements a task orchestration pattern using `doit`:

```python
from pathlib import Path
from clipsmith import Context

# Create a context
context = Context()

# Forge a new clip from input files
context.forge("output.mp4", [Path("input1.mp4"), Path("input2.mp4")])

# Execute all pending operations
context.doit()
```

### Clips

Clips can be manipulated using operation parameters for duration and resolution. A clip can be "reforged" into another clip, with `doit` managing orchestration of `ffmpeg` invocations.

```python
from clipsmith import (
    Context, 
    OperationParams,
    DurationParams,
    ResolutionParams
)

context = Context()
inputs = [Path("input1.mp4"), Path("input2.mp4")]

# Trimming
clip1 = context.forge(
    "output1.mp4",
    inputs,
    OperationParams(
        duration_params=DurationParams(
            trim_start=1.0,  # Start at 1 second
            trim_end=5.0,  # End at 5 seconds
        ),
    )
)

# Time scaling
clip2 = context.forge(
    "output2.mp4",
    inputs,
    OperationParams(
        duration_params=DurationParams(
            scale=2.0,  # Speed up by 2x
        ),
        audio=False
    )
)

# Resolution scaling
clip3 = context.forge(
    "output3.mp4", 
    inputs,
    OperationParams(
        resolution_params=ResolutionParams(
            target=(480, 270)  # Scale to specific resolution
        )
    )
)

# Chain operations by reforging trimmed clip
clip4 = clip1.reforge(
    "output4.mp4",
    OperationParams(
        resolution_params=ResolutionParams(
            scale=0.5  # Scale resolution by factor
        )
    )
)

# Execute all operations
context.doit()
```
