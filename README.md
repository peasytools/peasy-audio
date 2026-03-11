# peasy-audio

[![PyPI](https://img.shields.io/pypi/v/peasy-audio)](https://pypi.org/project/peasy-audio/)
[![Python](https://img.shields.io/pypi/pyversions/peasy-audio)](https://pypi.org/project/peasy-audio/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Python audio processing toolkit with 12 operations for everyday audio tasks. Convert between 6 formats (MP3, WAV, OGG, FLAC, AAC, M4A), trim and split audio segments, merge multiple files, normalize volume to target dBFS levels, apply fade effects, change playback speed, reverse audio, overlay tracks, and generate silence -- all through a clean, consistent API. Every function accepts `bytes`, `Path`, or `str` and returns a frozen `AudioResult` dataclass, making it easy to chain operations or integrate into web services. Powered by [pydub](https://github.com/jiaaro/pydub) with [FFmpeg](https://ffmpeg.org/) for codec support.

Built for [PeasyAudio](https://peasyaudio.com), a free online audio toolkit with 10 browser-based tools for converting, trimming, merging, normalizing, and analyzing audio files. The site processes files using FFmpeg WASM for privacy, while the Python package brings the same capabilities to scripts, pipelines, and AI assistants.

> **Try the interactive tools at [peasyaudio.com](https://peasyaudio.com)** -- audio conversion, trimming, merging, normalization, and analysis.

<p align="center">
  <img src="demo.gif" alt="peasy-audio demo — audio format conversion, silence generation, and volume normalization in Python REPL" width="800">
</p>

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [What You Can Do](#what-you-can-do)
  - [Format Conversion](#format-conversion)
  - [Trimming & Splitting](#trimming--splitting)
  - [Volume & Normalization](#volume--normalization)
  - [Audio Effects](#audio-effects)
  - [Audio Analysis](#audio-analysis)
- [Command-Line Interface](#command-line-interface)
- [API Reference](#api-reference)
  - [Processing Functions](#processing-functions)
  - [Analysis Functions](#analysis-functions)
  - [Types](#types)
- [Learn More About Audio Processing](#learn-more-about-audio-processing)
- [Peasy Developer Tools](#peasy-developer-tools)
- [License](#license)

## Install

```bash
pip install peasy-audio            # Core engine (pydub)
pip install "peasy-audio[cli]"     # + Command-line interface (typer)
```

Or run instantly without installing:

```bash
uvx --from "peasy-audio[cli]" peasy-audio info song.mp3
```

### FFmpeg Prerequisite

peasy-audio uses pydub which requires [FFmpeg](https://ffmpeg.org/) for non-WAV formats (MP3, OGG, FLAC, AAC, M4A). WAV processing works without FFmpeg.

FFmpeg is a complete, cross-platform solution for recording, converting, and streaming audio and video. It supports virtually every audio codec in existence, from legacy formats like PCM and ADPCM to modern codecs like Opus, Vorbis, and AAC-HE. When peasy-audio calls a conversion or processing function, pydub delegates the actual codec work to FFmpeg's `libavcodec` library, which handles encoding, decoding, sample rate conversion, and channel remixing transparently.

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

**Verify installation:**
```bash
ffmpeg -version
# ffmpeg version 7.x ... built with gcc/clang
```

## Quick Start

```python
from peasy_audio import convert, trim, merge, info, normalize

# Get audio file metadata — duration, channels, sample rate, bit depth
metadata = info("podcast.mp3")
print(f"Duration: {metadata.duration_seconds:.1f}s, {metadata.channels}ch, {metadata.frame_rate}Hz")

# Convert MP3 to WAV (lossless PCM)
result = convert("podcast.mp3", target_format="wav")
with open("podcast.wav", "wb") as f:
    f.write(result.data)

# Trim to first 30 seconds for a preview clip
clip = trim("podcast.mp3", start_ms=0, end_ms=30000)

# Normalize volume to broadcast standard -16 dBFS
normalized = normalize("podcast.mp3", target_dbfs=-16.0)

# Merge intro + main content + outro into a single file
final = merge("intro.mp3", "main.mp3", "outro.mp3")
```

## What You Can Do

### Format Conversion

Digital audio comes in two fundamental categories: **lossless** formats that preserve every sample of the original recording, and **lossy** formats that use psychoacoustic models to discard sounds the human ear is unlikely to notice. The choice between them is a trade-off between file size and audio fidelity.

**Lossy codecs** like MP3 (MPEG Layer 3) and AAC (Advanced Audio Coding) use perceptual coding -- they analyze audio in frequency bands and remove data below the masking threshold. At 320 kbps, MP3 is considered "transparent" (indistinguishable from the original) by most listeners. AAC achieves similar quality at lower bitrates due to more advanced transform coding, making it the default for Apple Music and YouTube.

**Lossless codecs** like FLAC (Free Lossless Audio Codec) use prediction-based compression -- they predict each sample from previous samples and store only the prediction error, achieving 50-60% compression with bit-perfect reconstruction. WAV stores raw PCM (Pulse Code Modulation) samples with no compression at all.

| Format | Extension | Codec | Type | Typical Bitrate | Best For |
|--------|-----------|-------|------|-----------------|----------|
| MP3 | `.mp3` | MPEG Layer 3 | Lossy | 128-320 kbps | Universal compatibility, streaming |
| WAV | `.wav` | PCM (uncompressed) | Lossless | ~1,411 kbps (CD) | Editing, mastering, no FFmpeg needed |
| OGG | `.ogg` | Vorbis | Lossy | 96-500 kbps | Open-source projects, web audio |
| FLAC | `.flac` | FLAC | Lossless | 600-1,200 kbps | Archival, audiophile playback |
| AAC | `.aac` | Advanced Audio Coding | Lossy | 96-256 kbps | Apple ecosystem, mobile streaming |
| M4A | `.m4a` | AAC in MP4 container | Lossy | 128-256 kbps | iTunes, Apple Music, podcasts |

```python
from peasy_audio import convert

# Convert WAV to MP3 at broadcast quality (320 kbps)
result = convert("recording.wav", target_format="mp3", bitrate="320k")
with open("recording.mp3", "wb") as f:
    f.write(result.data)

# Convert MP3 to FLAC for lossless archival
result = convert("song.mp3", target_format="flac")

# Convert to OGG Vorbis for open-source web applications
result = convert("track.wav", target_format="ogg", bitrate="192k")

# Convert to AAC for Apple ecosystem compatibility
result = convert("podcast.wav", target_format="aac", bitrate="256k")
```

Learn more: [PeasyAudio](https://peasyaudio.com) · [Developer Docs](https://peasyaudio.com/developers/)

### Trimming & Splitting

Audio trimming extracts a specific time range from a file, while splitting uses **silence detection** to automatically segment audio into logical chunks. Silence detection works by scanning the audio waveform for regions where the signal level drops below a threshold (measured in dBFS -- decibels relative to full scale, where 0 dBFS is the maximum possible amplitude and silence is around -80 to -96 dBFS depending on bit depth).

This is particularly useful for podcast post-production, where you might need to extract a highlight clip from a 2-hour episode, or automatically segment a lecture recording into individual topics based on the speaker's natural pauses.

```python
from peasy_audio import trim, split_on_silence

# Extract a 10-second clip starting at the 1-minute mark
clip = trim("interview.mp3", start_ms=60_000, end_ms=70_000)

# Trim from 5 minutes to end of file (omit end_ms for remainder)
second_half = trim("podcast.mp3", start_ms=300_000)

# Auto-split a podcast into segments based on silence gaps
# min_silence_ms=1000 means a 1-second pause triggers a split
# silence_thresh_db=-40 is a good threshold for speech recordings
chunks = split_on_silence(
    "podcast.mp3",
    min_silence_ms=1000,      # 1 second of silence to trigger split
    silence_thresh_db=-40,    # silence threshold in dBFS
)
for i, chunk in enumerate(chunks):
    with open(f"segment_{i:03d}.mp3", "wb") as f:
        f.write(chunk.data)
    print(f"Segment {i}: {chunk.duration_ms / 1000:.1f}s")
```

Learn more: [PeasyAudio](https://peasyaudio.com) · [Audio Glossary](https://peasyaudio.com/glossary/)

### Volume & Normalization

**Normalization** adjusts the overall gain of an audio file so that its average loudness (measured in dBFS) reaches a target level. This is essential for podcast production, where episodes recorded on different microphones or in different environments can vary wildly in perceived volume. Without normalization, listeners constantly reach for the volume knob.

The dBFS scale works logarithmically, matching how human hearing perceives loudness:

| dBFS Level | Use Case | Perceived Loudness |
|------------|----------|-------------------|
| 0 dBFS | Maximum digital amplitude | Clipping threshold |
| -3 dBFS | Peak headroom target | Very loud, near clipping |
| -14 dBFS | Spotify loudness target (LUFS) | Streaming-optimized |
| -16 dBFS | Broadcast standard (EBU R128) | Podcast / radio standard |
| -20 dBFS | Conservative mastering | Comfortable listening |
| -40 dBFS | Quiet ambient noise | Barely audible |
| -96 dBFS | 16-bit noise floor | Silence for 16-bit audio |

peasy-audio uses a simple peak normalization algorithm: it measures the current average dBFS of the file, calculates the difference to the target, and applies uniform gain across the entire file. This preserves the dynamic range of the recording while bringing the overall level to the desired target.

```python
from peasy_audio import normalize, change_volume

# Normalize a podcast episode to broadcast standard -16 dBFS
normalized = normalize("episode.mp3", target_dbfs=-16.0)

# Normalize to Spotify's loudness target for music
normalized = normalize("song.wav", target_dbfs=-14.0)

# Boost quiet audio by 6 dB (perceived as roughly doubling volume)
louder = change_volume("quiet_recording.mp3", db=6.0)

# Reduce volume by 3 dB (half the perceived loudness)
quieter = change_volume("loud_track.mp3", db=-3.0)
```

Learn more: [PeasyAudio](https://peasyaudio.com) · [OpenAPI Spec](https://peasyaudio.com/api/openapi.json)

### Audio Effects

Beyond volume control, peasy-audio provides several audio manipulation operations: fade effects for professional transitions, speed adjustment for time-stretching, audio reversal, track overlaying for mixing, and silence generation for padding.

**Fade effects** apply a gradual volume ramp at the start (fade-in) or end (fade-out) of an audio file. Professionally produced audio almost always uses fades to avoid the jarring "click" of an abrupt start or stop, which occurs when the waveform is cut at a non-zero amplitude.

**Sample rate** determines how many times per second the analog audio signal is measured. The Nyquist-Shannon theorem states that a sample rate must be at least twice the highest frequency to be reproduced. Since human hearing caps at approximately 20 kHz, CD-quality audio uses 44,100 Hz (44.1 kHz), providing headroom above the audible range.

| Sample Rate | Use Case | Frequency Range |
|-------------|----------|-----------------|
| 8,000 Hz | Telephone, VoIP | Up to 4 kHz |
| 22,050 Hz | AM radio quality | Up to 11 kHz |
| 44,100 Hz | CD quality (Red Book standard) | Up to 22.05 kHz |
| 48,000 Hz | Professional video/film audio | Up to 24 kHz |
| 96,000 Hz | Hi-res audio, mastering | Up to 48 kHz |

**Bit depth** determines the dynamic range -- the difference between the quietest and loudest representable sound. Each bit adds approximately 6 dB of dynamic range: 16-bit audio provides 96 dB (CD standard), while 24-bit provides 144 dB (used in professional recording to capture extremely quiet details without raising the noise floor).

```python
from peasy_audio import fade, speed, reverse_audio, overlay, silence, merge

# Add professional fade-in (2s) and fade-out (3s) to a track
polished = fade("track.mp3", fade_in_ms=2000, fade_out_ms=3000)

# Speed up a lecture to 1.5x (note: this changes pitch)
faster = speed("lecture.mp3", factor=1.5)

# Slow down to half speed for analysis
slow = speed("sample.mp3", factor=0.5)

# Reverse audio for creative sound design
backwards = reverse_audio("sample.mp3")

# Overlay background music under narration
mixed = overlay("narration.mp3", "background_music.mp3", position_ms=0)

# Generate 2 seconds of silence at CD quality (44.1 kHz)
gap = silence(duration_ms=2000, sample_rate=44100)

# Build a complete podcast: intro + 1s gap + content + 1s gap + outro
gap_1s = silence(duration_ms=1000, sample_rate=44100)
with open("gap.wav", "wb") as f:
    f.write(gap_1s.data)
final = merge("intro.mp3", "gap.wav", "content.mp3", "gap.wav", "outro.mp3")
```

Learn more: [PeasyAudio](https://peasyaudio.com) · [Developer Docs](https://peasyaudio.com/developers/)

### Audio Analysis

Inspect audio file metadata without loading the entire file into memory for processing. The `info()` function returns a frozen `AudioInfo` dataclass with all key properties: duration, channel count (mono/stereo), sample width (bit depth), sample rate, estimated bitrate, and file size.

Understanding these properties helps you make informed decisions about format conversion. For example, converting a 16-bit/44.1 kHz WAV to 320 kbps MP3 reduces file size by roughly 4.4x while maintaining near-transparent quality. Converting the same file to 128 kbps MP3 saves 11x the space but introduces audible artifacts on high-frequency content like cymbals and sibilance.

| Property | Description | Typical Values |
|----------|-------------|----------------|
| `duration_ms` | Length in milliseconds | 180,000 (3 min song) |
| `channels` | 1 = mono, 2 = stereo | 2 (stereo) |
| `sample_width` | Bytes per sample | 2 (16-bit), 3 (24-bit) |
| `frame_rate` | Samples per second (Hz) | 44,100 (CD quality) |
| `frame_count` | Total number of frames | 7,938,000 (3 min @ 44.1k) |
| `bitrate` | Bits per second (estimated) | 320,000 (320 kbps MP3) |
| `size_bytes` | File size in bytes | 7,200,000 (3 min @ 320k) |

```python
from peasy_audio import info

# Get complete audio metadata
metadata = info("song.mp3")
print(f"Duration:    {metadata.duration_seconds:.2f}s ({metadata.duration_ms}ms)")
print(f"Channels:    {metadata.channels} ({'stereo' if metadata.channels == 2 else 'mono'})")
print(f"Sample Rate: {metadata.frame_rate:,} Hz")
print(f"Bit Depth:   {metadata.sample_width * 8}-bit")
print(f"Bitrate:     {metadata.bitrate // 1000}k")
print(f"File Size:   {metadata.size_bytes:,} bytes ({metadata.size_bytes / 1024 / 1024:.1f} MB)")

# Compare file sizes across formats
for fmt in ["mp3", "wav", "ogg", "flac"]:
    from peasy_audio import convert
    result = convert("song.wav", target_format=fmt)
    ratio = result.size_bytes / metadata.size_bytes
    print(f"{fmt.upper():>4}: {result.size_bytes:>10,} bytes ({ratio:.1%} of original)")
```

Learn more: [PeasyAudio](https://peasyaudio.com) · [Audio Glossary](https://peasyaudio.com/glossary/)

## Command-Line Interface

Install with CLI extras: `pip install "peasy-audio[cli]"`

```bash
# Show audio file metadata
peasy-audio info song.mp3
# Duration:      3:24.50 (204500ms)
# Channels:      2
# Sample Rate:   44100 Hz
# Bit Depth:     16-bit
# Bitrate:       320k
# File Size:     8,180,000 bytes

# Convert format (WAV to MP3 at 320 kbps)
peasy-audio convert-cmd song.wav --format mp3 --bitrate 320k -o song.mp3

# Trim audio (extract first 30 seconds)
peasy-audio trim-cmd podcast.mp3 --start 0 --end 30000 -o intro.mp3

# Merge multiple files into one
peasy-audio merge-cmd intro.mp3 main.mp3 outro.mp3 -o final.mp3

# Normalize volume to broadcast standard
peasy-audio normalize-cmd episode.mp3 --target-dbfs -16 -o normalized.mp3

# Adjust volume (+6 dB boost)
peasy-audio volume-cmd quiet.mp3 --db 6.0 -o louder.mp3

# Add fade effects (2s fade-in, 3s fade-out)
peasy-audio fade-cmd track.mp3 --fade-in 2000 --fade-out 3000 -o faded.mp3

# Change playback speed (1.5x)
peasy-audio speed-cmd lecture.mp3 --factor 1.5 -o faster.mp3

# Reverse audio
peasy-audio reverse-cmd sample.mp3 -o reversed.mp3
```

## API Reference

### Processing Functions

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `convert(source, *, target_format, bitrate)` | `target_format: AudioFormat = "mp3"`, `bitrate: str = "192k"` | `AudioResult` | Convert between 6 audio formats (MP3, WAV, OGG, FLAC, AAC, M4A) |
| `trim(source, *, start_ms, end_ms, fmt)` | `start_ms: int = 0`, `end_ms: int \| None = None` | `AudioResult` | Extract a time range from an audio file |
| `merge(*sources, fmt, output_format)` | `output_format: str = "mp3"` | `AudioResult` | Concatenate 2 or more audio files sequentially |
| `normalize(source, *, target_dbfs, fmt)` | `target_dbfs: float = -20.0` | `AudioResult` | Normalize volume to a target dBFS level |
| `change_volume(source, *, db, fmt)` | `db: float` (positive = louder) | `AudioResult` | Adjust volume by a specified number of decibels |
| `fade(source, *, fade_in_ms, fade_out_ms, fmt)` | `fade_in_ms: int = 0`, `fade_out_ms: int = 0` | `AudioResult` | Apply gradual fade-in and/or fade-out effects |
| `speed(source, *, factor, fmt)` | `factor: float = 1.0` (>1 faster, <1 slower) | `AudioResult` | Change playback speed (affects pitch) |
| `reverse_audio(source, *, fmt)` | -- | `AudioResult` | Reverse audio playback direction |
| `silence(duration_ms, *, sample_rate)` | `duration_ms: int = 1000`, `sample_rate: int = 44100` | `AudioResult` | Generate a silent audio segment (WAV) |
| `split_on_silence(source, *, min_silence_ms, silence_thresh_db, fmt)` | `min_silence_ms: int = 500`, `silence_thresh_db: int = -40` | `list[AudioResult]` | Split audio into chunks at silence boundaries |
| `overlay(base, overlay_source, *, position_ms, fmt)` | `position_ms: int = 0` | `AudioResult` | Mix one audio track on top of another |

### Analysis Functions

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `info(source, *, fmt)` | -- | `AudioInfo` | Get audio metadata (duration, channels, sample rate, bitrate) |

### Types

| Type | Description |
|------|-------------|
| `AudioInput` | `bytes \| Path \| str` -- flexible input accepts raw bytes, pathlib Path, or string file path |
| `AudioFormat` | `Literal["mp3", "wav", "ogg", "flac", "aac", "m4a"]` -- 6 supported audio formats |
| `AudioResult` | Frozen dataclass: `data: bytes`, `format: str`, `duration_ms: int`, `size_bytes: int` |
| `AudioInfo` | Frozen dataclass: `duration_ms`, `duration_seconds`, `channels`, `sample_width`, `frame_rate`, `frame_count`, `bitrate`, `size_bytes` |

## Learn More About Audio Processing

- **Home**: [PeasyAudio](https://peasyaudio.com)
- **Reference**: [Audio Glossary](https://peasyaudio.com/glossary/)
- **API**: [Developer Docs](https://peasyaudio.com/developers/) · [OpenAPI Spec](https://peasyaudio.com/api/openapi.json)

## Peasy Developer Tools

Part of the [Peasy](https://peasytools.com) open-source developer tools ecosystem.

| Package | PyPI | npm | Description |
|---------|------|-----|-------------|
| peasy-pdf | [PyPI](https://pypi.org/project/peasy-pdf/) | [npm](https://www.npmjs.com/package/peasy-pdf) | PDF merge, split, compress, 21 operations -- [peasypdf.com](https://peasypdf.com) |
| peasy-image | [PyPI](https://pypi.org/project/peasy-image/) | [npm](https://www.npmjs.com/package/peasy-image) | Image resize, crop, convert, compress, 20 operations -- [peasyimage.com](https://peasyimage.com) |
| peasy-css | [PyPI](https://pypi.org/project/peasy-css/) | [npm](https://www.npmjs.com/package/peasy-css) | CSS gradients, shadows, flexbox, grid generators -- [peasycss.com](https://peasycss.com) |
| peasy-compress | [PyPI](https://pypi.org/project/peasy-compress/) | [npm](https://www.npmjs.com/package/peasy-compress) | ZIP, TAR, gzip, brotli archive operations -- [peasytools.com](https://peasytools.com) |
| peasy-document | [PyPI](https://pypi.org/project/peasy-document/) | [npm](https://www.npmjs.com/package/peasy-document) | Markdown, HTML, CSV, JSON, YAML conversions -- [peasytools.com](https://peasytools.com) |
| **peasy-audio** | [PyPI](https://pypi.org/project/peasy-audio/) | -- | Audio convert, trim, merge, normalize, 12 operations -- [peasyaudio.com](https://peasyaudio.com) |
| peasy-video | [PyPI](https://pypi.org/project/peasy-video/) | -- | Video trim, resize, GIF conversion -- [peasyvideo.com](https://peasyvideo.com) |
| peasytext | [PyPI](https://pypi.org/project/peasytext/) | [npm](https://www.npmjs.com/package/peasytext) | Text processing and transformation -- [peasytext.com](https://peasytext.com) |
| peasy-convert | [PyPI](https://pypi.org/project/peasy-convert/) | -- | Unified CLI for all Peasy tools -- [peasytools.com](https://peasytools.com) |
| peasy-mcp | [PyPI](https://pypi.org/project/peasy-mcp/) | -- | Unified MCP server for AI assistants -- [peasytools.com](https://peasytools.com) |

## License

MIT
