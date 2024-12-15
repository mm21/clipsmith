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