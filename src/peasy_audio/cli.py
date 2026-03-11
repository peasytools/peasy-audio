"""peasy-audio CLI — audio processing from the command line."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from peasy_audio.engine import (
    AudioFormat,
    change_volume,
    convert,
    fade,
    info,
    merge,
    normalize,
    reverse_audio,
    speed,
    trim,
)

app = typer.Typer(
    name="audio",
    help="Audio tools — convert, trim, merge, normalize, fade.",
    no_args_is_help=True,
)


def _write_output(data: bytes, output: Path) -> None:
    """Write bytes to output file."""
    output.write_bytes(data)
    typer.echo(f"Written to {output} ({len(data):,} bytes)")


@app.command()
def convert_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    format: Annotated[AudioFormat, typer.Option("--format", "-f", help="Target format")] = "mp3",
    bitrate: Annotated[str, typer.Option("--bitrate", "-b", help="Output bitrate")] = "192k",
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Convert audio to a different format."""
    result = convert(input_path, target_format=format, bitrate=bitrate)
    out = output or input_path.with_suffix(f".{format}")
    _write_output(result.data, out)


@app.command()
def trim_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    start: Annotated[int, typer.Option("--start", "-s", help="Start time in ms")] = 0,
    end: Annotated[int | None, typer.Option("--end", "-e", help="End time in ms")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Trim audio to a specific time range."""
    result = trim(input_path, start_ms=start, end_ms=end)
    out = output or input_path.with_stem(f"{input_path.stem}_trimmed")
    _write_output(result.data, out)


@app.command()
def merge_cmd(
    input_paths: Annotated[list[Path], typer.Argument(help="Input audio files to merge")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file")] = Path(
        "merged.mp3"
    ),
) -> None:
    """Merge multiple audio files into one."""
    result = merge(*input_paths, output_format=output.suffix.lstrip(".") or "mp3")
    _write_output(result.data, output)


@app.command()
def normalize_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    target_dbfs: Annotated[
        float, typer.Option("--target-dbfs", "-t", help="Target dBFS level")
    ] = -20.0,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Normalize audio volume to a target dBFS level."""
    result = normalize(input_path, target_dbfs=target_dbfs)
    out = output or input_path.with_stem(f"{input_path.stem}_normalized")
    _write_output(result.data, out)


@app.command()
def volume_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    db: Annotated[float, typer.Option("--db", help="Volume change in dB")] = 0.0,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Adjust audio volume by a specified number of decibels."""
    result = change_volume(input_path, db=db)
    out = output or input_path.with_stem(f"{input_path.stem}_volume")
    _write_output(result.data, out)


@app.command()
def fade_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    fade_in: Annotated[int, typer.Option("--fade-in", help="Fade-in duration in ms")] = 0,
    fade_out: Annotated[int, typer.Option("--fade-out", help="Fade-out duration in ms")] = 0,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Apply fade-in and/or fade-out effects."""
    result = fade(input_path, fade_in_ms=fade_in, fade_out_ms=fade_out)
    out = output or input_path.with_stem(f"{input_path.stem}_faded")
    _write_output(result.data, out)


@app.command()
def info_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
) -> None:
    """Show audio file information."""
    result = info(input_path)
    typer.echo(f"Duration:      {result.duration_seconds:.2f}s ({result.duration_ms}ms)")
    typer.echo(f"Channels:      {result.channels}")
    typer.echo(f"Sample Width:  {result.sample_width} bytes ({result.sample_width * 8}-bit)")
    typer.echo(f"Sample Rate:   {result.frame_rate} Hz")
    typer.echo(f"Frame Count:   {result.frame_count:,}")
    typer.echo(f"Bitrate:       {result.bitrate:,} bps ({result.bitrate // 1000}k)")
    typer.echo(f"File Size:     {result.size_bytes:,} bytes")


@app.command()
def reverse_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Reverse audio playback."""
    result = reverse_audio(input_path)
    out = output or input_path.with_stem(f"{input_path.stem}_reversed")
    _write_output(result.data, out)


@app.command()
def speed_cmd(
    input_path: Annotated[Path, typer.Argument(help="Input audio file")],
    factor: Annotated[float, typer.Option("--factor", "-f", help="Speed multiplier")] = 1.0,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Change audio playback speed."""
    result = speed(input_path, factor=factor)
    out = output or input_path.with_stem(f"{input_path.stem}_speed")
    _write_output(result.data, out)
