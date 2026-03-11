"""peasy-audio engine — pure functions for audio processing powered by pydub."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pydub import AudioSegment

AudioInput = bytes | Path | str
AudioFormat = Literal["mp3", "wav", "ogg", "flac", "aac", "m4a"]


@dataclass(frozen=True)
class AudioInfo:
    """Metadata about an audio file."""

    duration_ms: int
    duration_seconds: float
    channels: int
    sample_width: int  # bytes per sample
    frame_rate: int  # Hz
    frame_count: int
    bitrate: int  # bits per second (estimated)
    size_bytes: int


@dataclass(frozen=True)
class AudioResult:
    """Result of an audio processing operation."""

    data: bytes
    format: str
    duration_ms: int
    size_bytes: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load(source: AudioInput, fmt: str | None = None) -> AudioSegment:
    """Load audio from bytes, Path, or str path."""
    from pydub import AudioSegment

    if isinstance(source, bytes):
        return AudioSegment.from_file(io.BytesIO(source), format=fmt)
    path = Path(source) if isinstance(source, str) else source
    return AudioSegment.from_file(str(path), format=fmt or path.suffix.lstrip("."))


def _export(segment: AudioSegment, fmt: str = "mp3", **kwargs: object) -> AudioResult:
    """Export AudioSegment to bytes and wrap in AudioResult."""
    buf = io.BytesIO()
    segment.export(buf, format=fmt, **kwargs)
    data = buf.getvalue()
    return AudioResult(data=data, format=fmt, duration_ms=len(segment), size_bytes=len(data))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convert(
    source: AudioInput,
    *,
    target_format: AudioFormat = "mp3",
    bitrate: str = "192k",
) -> AudioResult:
    """Convert audio to a different format.

    Args:
        source: Audio input as bytes, Path, or string path.
        target_format: Output format (mp3, wav, ogg, flac, aac, m4a).
        bitrate: Output bitrate for lossy formats (e.g. "192k", "320k").

    Returns:
        AudioResult with converted audio data.
    """
    segment = _load(source)
    return _export(segment, fmt=target_format, bitrate=bitrate)


def trim(
    source: AudioInput,
    *,
    start_ms: int = 0,
    end_ms: int | None = None,
    fmt: str | None = None,
) -> AudioResult:
    """Trim audio to a specific time range.

    Args:
        source: Audio input.
        start_ms: Start position in milliseconds.
        end_ms: End position in milliseconds (None = end of audio).
        fmt: Input format hint (optional).

    Returns:
        AudioResult with trimmed audio.
    """
    segment = _load(source, fmt=fmt)
    trimmed = segment[start_ms:end_ms]
    output_fmt = fmt or "mp3"
    return _export(trimmed, fmt=output_fmt)


def merge(
    *sources: AudioInput,
    fmt: str | None = None,
    output_format: str = "mp3",
) -> AudioResult:
    """Concatenate multiple audio files into one.

    Args:
        *sources: Two or more audio inputs to merge sequentially.
        fmt: Input format hint (optional).
        output_format: Output format.

    Returns:
        AudioResult with merged audio.
    """
    from pydub import AudioSegment

    if len(sources) < 2:
        raise ValueError("merge() requires at least 2 audio sources")
    combined = AudioSegment.empty()
    for src in sources:
        combined += _load(src, fmt=fmt)
    return _export(combined, fmt=output_format)


def normalize(
    source: AudioInput,
    *,
    target_dbfs: float = -20.0,
    fmt: str | None = None,
) -> AudioResult:
    """Normalize audio volume to a target dBFS level.

    Args:
        source: Audio input.
        target_dbfs: Target loudness in dBFS (e.g. -20.0).
        fmt: Input format hint (optional).

    Returns:
        AudioResult with normalized audio.
    """
    segment = _load(source, fmt=fmt)
    change_in_dbfs = target_dbfs - segment.dBFS
    normalized = segment.apply_gain(change_in_dbfs)
    output_fmt = fmt or "mp3"
    return _export(normalized, fmt=output_fmt)


def change_volume(
    source: AudioInput,
    *,
    db: float,
    fmt: str | None = None,
) -> AudioResult:
    """Increase or decrease audio volume by a specified number of decibels.

    Args:
        source: Audio input.
        db: Volume change in decibels (positive = louder, negative = quieter).
        fmt: Input format hint (optional).

    Returns:
        AudioResult with adjusted volume.
    """
    segment = _load(source, fmt=fmt)
    adjusted = segment + db
    output_fmt = fmt or "mp3"
    return _export(adjusted, fmt=output_fmt)


def fade(
    source: AudioInput,
    *,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
    fmt: str | None = None,
) -> AudioResult:
    """Apply fade-in and/or fade-out effects.

    Args:
        source: Audio input.
        fade_in_ms: Duration of fade-in in milliseconds.
        fade_out_ms: Duration of fade-out in milliseconds.
        fmt: Input format hint (optional).

    Returns:
        AudioResult with fade effects applied.
    """
    segment = _load(source, fmt=fmt)
    if fade_in_ms > 0:
        segment = segment.fade_in(fade_in_ms)
    if fade_out_ms > 0:
        segment = segment.fade_out(fade_out_ms)
    output_fmt = fmt or "mp3"
    return _export(segment, fmt=output_fmt)


def speed(
    source: AudioInput,
    *,
    factor: float = 1.0,
    fmt: str | None = None,
) -> AudioResult:
    """Change playback speed of audio.

    A factor > 1.0 speeds up, < 1.0 slows down. This changes pitch as well
    (chipmunk effect for faster, deeper for slower).

    Args:
        source: Audio input.
        factor: Speed multiplier (e.g. 2.0 = double speed, 0.5 = half speed).
        fmt: Input format hint (optional).

    Returns:
        AudioResult with speed-adjusted audio.
    """
    if factor <= 0:
        raise ValueError("speed factor must be positive")
    segment = _load(source, fmt=fmt)
    # Change frame rate to alter speed, then convert back to original frame rate
    altered = segment._spawn(
        segment.raw_data,
        overrides={"frame_rate": int(segment.frame_rate * factor)},
    )
    altered = altered.set_frame_rate(segment.frame_rate)
    output_fmt = fmt or "mp3"
    return _export(altered, fmt=output_fmt)


def reverse_audio(
    source: AudioInput,
    *,
    fmt: str | None = None,
) -> AudioResult:
    """Reverse audio playback.

    Args:
        source: Audio input.
        fmt: Input format hint (optional).

    Returns:
        AudioResult with reversed audio.
    """
    segment = _load(source, fmt=fmt)
    reversed_seg = segment.reverse()
    output_fmt = fmt or "mp3"
    return _export(reversed_seg, fmt=output_fmt)


def silence(
    duration_ms: int = 1000,
    *,
    sample_rate: int = 44100,
) -> AudioResult:
    """Generate a silent audio segment.

    Args:
        duration_ms: Duration of silence in milliseconds.
        sample_rate: Sample rate in Hz.

    Returns:
        AudioResult with silent audio in WAV format.
    """
    from pydub import AudioSegment

    silent = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
    return _export(silent, fmt="wav")


def split_on_silence(
    source: AudioInput,
    *,
    min_silence_ms: int = 500,
    silence_thresh_db: int = -40,
    fmt: str | None = None,
) -> list[AudioResult]:
    """Split audio into chunks based on silence detection.

    Args:
        source: Audio input.
        min_silence_ms: Minimum length of silence to split on (milliseconds).
        silence_thresh_db: Silence threshold in dBFS.
        fmt: Input format hint (optional).

    Returns:
        List of AudioResult chunks.
    """
    from pydub.silence import split_on_silence as pydub_split

    segment = _load(source, fmt=fmt)
    chunks = pydub_split(
        segment,
        min_silence_len=min_silence_ms,
        silence_thresh=silence_thresh_db,
    )
    output_fmt = fmt or "mp3"
    return [_export(chunk, fmt=output_fmt) for chunk in chunks]


def info(
    source: AudioInput,
    *,
    fmt: str | None = None,
) -> AudioInfo:
    """Get audio file metadata.

    Args:
        source: Audio input.
        fmt: Input format hint (optional).

    Returns:
        AudioInfo with duration, channels, sample rate, bitrate, etc.
    """
    # Determine file size
    if isinstance(source, bytes):
        size_bytes = len(source)
    else:
        path = Path(source) if isinstance(source, str) else source
        size_bytes = path.stat().st_size

    segment = _load(source, fmt=fmt)
    duration_ms = len(segment)
    duration_seconds = duration_ms / 1000.0
    frame_count = int(segment.frame_count())
    bitrate = int((size_bytes * 8) / duration_seconds) if duration_seconds > 0 else 0

    return AudioInfo(
        duration_ms=duration_ms,
        duration_seconds=duration_seconds,
        channels=segment.channels,
        sample_width=segment.sample_width,
        frame_rate=segment.frame_rate,
        frame_count=frame_count,
        bitrate=bitrate,
        size_bytes=size_bytes,
    )


def overlay(
    base: AudioInput,
    overlay_source: AudioInput,
    *,
    position_ms: int = 0,
    fmt: str | None = None,
) -> AudioResult:
    """Overlay one audio on top of another.

    Args:
        base: Base audio input (background).
        overlay_source: Audio to overlay on top.
        position_ms: Position in milliseconds where overlay starts.
        fmt: Input format hint (optional).

    Returns:
        AudioResult with combined audio.
    """
    base_seg = _load(base, fmt=fmt)
    overlay_seg = _load(overlay_source, fmt=fmt)
    combined = base_seg.overlay(overlay_seg, position=position_ms)
    output_fmt = fmt or "mp3"
    return _export(combined, fmt=output_fmt)
