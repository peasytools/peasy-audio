"""peasy-audio — Audio processing made easy, powered by pydub."""

__version__ = "0.1.0"

from peasy_audio.engine import (
    AudioFormat,
    AudioInfo,
    AudioInput,
    AudioResult,
    change_volume,
    convert,
    fade,
    info,
    merge,
    normalize,
    overlay,
    reverse_audio,
    silence,
    speed,
    split_on_silence,
    trim,
)

__all__ = [
    "AudioFormat",
    "AudioInfo",
    "AudioInput",
    "AudioResult",
    "__version__",
    "change_volume",
    "convert",
    "fade",
    "info",
    "merge",
    "normalize",
    "overlay",
    "reverse_audio",
    "silence",
    "speed",
    "split_on_silence",
    "trim",
]
