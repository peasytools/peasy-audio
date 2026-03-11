# peasy-audio

[![PyPI](https://img.shields.io/pypi/v/peasy-audio)](https://pypi.org/project/peasy-audio/)
[![Python](https://img.shields.io/pypi/pyversions/peasy-audio)](https://pypi.org/project/peasy-audio/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Audio processing made easy. Convert, trim, merge, normalize, and analyze audio files with a clean Python API and command-line interface. Built on top of [pydub](https://github.com/jiaaro/pydub), which uses ffmpeg under the hood for broad format support.

> **Requires ffmpeg** installed on your system for MP3, OGG, FLAC, AAC, and M4A support. WAV processing works without ffmpeg.

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [What You Can Do](#what-you-can-do)
  - [Format Conversion](#format-conversion)
  - [Trimming & Splitting](#trimming--splitting)
  - [Volume & Effects](#volume--effects)
  - [Audio Analysis](#audio-analysis)
- [Command-Line Interface](#command-line-interface)
- [API Reference](#api-reference)
- [Peasy Developer Tools](#peasy-developer-tools)
- [License](#license)

## Install

```bash
pip install peasy-audio
```

With CLI support:

```bash
pip install "peasy-audio[cli]"
```

### ffmpeg Installation

peasy-audio uses pydub which requires ffmpeg for non-WAV formats:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu / Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
```bash
choco install ffmpeg
```

## Quick Start

```python
from peasy_audio import convert, trim, merge, info, normalize

# Get audio file information
metadata = info("podcast.mp3")
print(f"Duration: {metadata.duration_seconds:.1f}s, {metadata.channels}ch, {metadata.frame_rate}Hz")

# Convert MP3 to WAV
result = convert("podcast.mp3", target_format="wav")
with open("podcast.wav", "wb") as f:
    f.write(result.data)

# Trim to first 30 seconds
clip = trim("podcast.mp3", start_ms=0, end_ms=30000)

# Normalize volume to -20 dBFS
normalized = normalize("podcast.mp3", target_dbfs=-20.0)

# Merge intro + main + outro
final = merge("intro.mp3", "main.mp3", "outro.mp3")
```

## What You Can Do

### Format Conversion

Convert between all major audio formats. pydub and ffmpeg handle the codec details so you can focus on your workflow.

| Format | Extension | Codec | Notes |
|--------|-----------|-------|-------|
| MP3 | `.mp3` | MPEG Layer 3 | Most common lossy format |
| WAV | `.wav` | PCM | Uncompressed, no ffmpeg needed |
| OGG | `.ogg` | Vorbis | Open-source lossy format |
| FLAC | `.flac` | FLAC | Lossless compression |
| AAC | `.aac` | AAC | Apple ecosystem |
| M4A | `.m4a` | AAC in MP4 | iTunes / Apple Music |

```python
from peasy_audio import convert

# Convert WAV to MP3 at 320kbps
result = convert("recording.wav", target_format="mp3", bitrate="320k")

# Convert to FLAC (lossless)
result = convert("song.mp3", target_format="flac")
```

### Trimming & Splitting

Extract specific segments from audio files or split on silence for automatic chapter detection.

```python
from peasy_audio import trim, split_on_silence

# Extract a 10-second clip starting at 1 minute
clip = trim("interview.mp3", start_ms=60000, end_ms=70000)

# Auto-split a podcast into segments based on silence
chunks = split_on_silence(
    "podcast.mp3",
    min_silence_ms=1000,     # 1 second of silence to split
    silence_thresh_db=-40,   # silence threshold in dBFS
)
for i, chunk in enumerate(chunks):
    with open(f"segment_{i}.mp3", "wb") as f:
        f.write(chunk.data)
```

### Volume & Effects

Normalize volume across episodes, add fade effects, change playback speed, or reverse audio.

```python
from peasy_audio import normalize, change_volume, fade, speed, reverse_audio, overlay, silence

# Normalize a batch of podcast episodes to consistent volume
normalized = normalize("episode.mp3", target_dbfs=-16.0)

# Boost quiet audio by 6 dB
louder = change_volume("quiet_recording.mp3", db=6.0)

# Add professional fade-in and fade-out
polished = fade("track.mp3", fade_in_ms=2000, fade_out_ms=3000)

# Speed up a lecture (1.5x)
faster = speed("lecture.mp3", factor=1.5)

# Reverse audio
backwards = reverse_audio("sample.mp3")

# Overlay background music under narration
mixed = overlay("narration.mp3", "background_music.mp3", position_ms=0)

# Generate 2 seconds of silence
gap = silence(duration_ms=2000, sample_rate=44100)
```

### Audio Analysis

Inspect audio file metadata without processing.

```python
from peasy_audio import info

# Get complete metadata
metadata = info("song.mp3")
print(f"Duration:    {metadata.duration_seconds:.2f}s ({metadata.duration_ms}ms)")
print(f"Channels:    {metadata.channels}")
print(f"Sample Rate: {metadata.frame_rate} Hz")
print(f"Bit Depth:   {metadata.sample_width * 8}-bit")
print(f"Bitrate:     {metadata.bitrate // 1000}k")
print(f"File Size:   {metadata.size_bytes:,} bytes")
```

## Command-Line Interface

Install with CLI extras: `pip install "peasy-audio[cli]"`

```bash
# Show audio file info
peasy-audio info song.mp3

# Convert format
peasy-audio convert-cmd song.wav --format mp3 --bitrate 320k -o song.mp3

# Trim audio (first 30 seconds)
peasy-audio trim-cmd podcast.mp3 --start 0 --end 30000 -o intro.mp3

# Merge multiple files
peasy-audio merge-cmd intro.mp3 main.mp3 outro.mp3 -o final.mp3

# Normalize volume
peasy-audio normalize-cmd episode.mp3 --target-dbfs -16 -o normalized.mp3

# Adjust volume
peasy-audio volume-cmd quiet.mp3 --db 6.0 -o louder.mp3

# Add fades
peasy-audio fade-cmd track.mp3 --fade-in 2000 --fade-out 3000 -o faded.mp3

# Change speed
peasy-audio speed-cmd lecture.mp3 --factor 1.5 -o faster.mp3

# Reverse audio
peasy-audio reverse-cmd sample.mp3 -o reversed.mp3
```

## API Reference

### Processing Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `convert(source, *, target_format, bitrate)` | Convert between audio formats | `AudioResult` |
| `trim(source, *, start_ms, end_ms, fmt)` | Trim audio to a time range | `AudioResult` |
| `merge(*sources, fmt, output_format)` | Concatenate multiple audio files | `AudioResult` |
| `normalize(source, *, target_dbfs, fmt)` | Normalize volume to target dBFS | `AudioResult` |
| `change_volume(source, *, db, fmt)` | Adjust volume by decibels | `AudioResult` |
| `fade(source, *, fade_in_ms, fade_out_ms, fmt)` | Apply fade-in/fade-out effects | `AudioResult` |
| `speed(source, *, factor, fmt)` | Change playback speed | `AudioResult` |
| `reverse_audio(source, *, fmt)` | Reverse audio playback | `AudioResult` |
| `silence(duration_ms, *, sample_rate)` | Generate silent audio | `AudioResult` |
| `split_on_silence(source, *, min_silence_ms, silence_thresh_db, fmt)` | Split audio on silence | `list[AudioResult]` |
| `overlay(base, overlay_source, *, position_ms, fmt)` | Overlay audio on another | `AudioResult` |

### Analysis Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `info(source, *, fmt)` | Get audio metadata | `AudioInfo` |

### Types

| Type | Description |
|------|-------------|
| `AudioInput` | `bytes \| Path \| str` — flexible input type |
| `AudioFormat` | `Literal["mp3", "wav", "ogg", "flac", "aac", "m4a"]` |
| `AudioResult` | Frozen dataclass: `data`, `format`, `duration_ms`, `size_bytes` |
| `AudioInfo` | Frozen dataclass: `duration_ms`, `duration_seconds`, `channels`, `sample_width`, `frame_rate`, `frame_count`, `bitrate`, `size_bytes` |

## Peasy Developer Tools

Part of the [Peasy Tools](https://peasytools.com) ecosystem.

| Package | PyPI | Description |
|---------|------|-------------|
| **peasy-audio** | [PyPI](https://pypi.org/project/peasy-audio/) | Audio processing — convert, trim, merge, normalize |
| peasy-pdf | [PyPI](https://pypi.org/project/peasy-pdf/) | PDF manipulation and conversion |
| peasy-image | [PyPI](https://pypi.org/project/peasy-image/) | Image processing and optimization |
| peasy-compress | [PyPI](https://pypi.org/project/peasy-compress/) | File compression utilities |
| peasy-css | [PyPI](https://pypi.org/project/peasy-css/) | CSS processing and optimization |
| peasytext | [PyPI](https://pypi.org/project/peasytext/) | Text processing and transformation |
| peasy-document | [PyPI](https://pypi.org/project/peasy-document/) | Document format conversion |
| peasy-convert | [PyPI](https://pypi.org/project/peasy-convert/) | Unified CLI for all Peasy tools |

## License

MIT
