"""Tests for peasy-audio engine.

WAV format is used for all tests because it doesn't require ffmpeg.
A helper generates simple sine wave WAV data using only stdlib modules.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from pathlib import Path

import pytest

from peasy_audio.engine import (
    AudioInfo,
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

# ---------------------------------------------------------------------------
# Helper: generate WAV data with a sine wave (no ffmpeg needed)
# ---------------------------------------------------------------------------


def _make_wav(
    duration_ms: int = 1000,
    sample_rate: int = 44100,
    channels: int = 1,
    frequency: float = 440.0,
) -> bytes:
    """Generate a simple WAV file with a sine wave."""
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            frame = struct.pack("<h", value) * channels
            wf.writeframes(frame)
    return buf.getvalue()


def _make_silent_wav(duration_ms: int = 1000, sample_rate: int = 44100) -> bytes:
    """Generate a silent WAV file."""
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests: info()
# ---------------------------------------------------------------------------


class TestInfo:
    def test_info_duration(self) -> None:
        wav_data = _make_wav(duration_ms=2000)
        result = info(wav_data, fmt="wav")
        assert isinstance(result, AudioInfo)
        # Allow some tolerance for WAV encoding
        assert abs(result.duration_ms - 2000) < 50

    def test_info_channels_mono(self) -> None:
        wav_data = _make_wav(channels=1)
        result = info(wav_data, fmt="wav")
        assert result.channels == 1

    def test_info_channels_stereo(self) -> None:
        wav_data = _make_wav(channels=2)
        result = info(wav_data, fmt="wav")
        assert result.channels == 2

    def test_info_sample_rate(self) -> None:
        wav_data = _make_wav(sample_rate=22050)
        result = info(wav_data, fmt="wav")
        assert result.frame_rate == 22050

    def test_info_sample_width(self) -> None:
        wav_data = _make_wav()
        result = info(wav_data, fmt="wav")
        assert result.sample_width == 2  # 16-bit

    def test_info_size_bytes(self) -> None:
        wav_data = _make_wav()
        result = info(wav_data, fmt="wav")
        assert result.size_bytes == len(wav_data)

    def test_info_bitrate_positive(self) -> None:
        wav_data = _make_wav()
        result = info(wav_data, fmt="wav")
        assert result.bitrate > 0

    def test_info_from_path(self, tmp_path: Path) -> None:
        wav_data = _make_wav()
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(wav_data)
        result = info(wav_file)
        assert result.duration_ms > 0
        assert result.size_bytes == len(wav_data)


# ---------------------------------------------------------------------------
# Tests: trim()
# ---------------------------------------------------------------------------


class TestTrim:
    def test_trim_start(self) -> None:
        wav_data = _make_wav(duration_ms=2000)
        result = trim(wav_data, start_ms=500, fmt="wav")
        assert isinstance(result, AudioResult)
        # Trimmed audio should be ~1500ms
        assert result.duration_ms < 2000
        assert result.duration_ms >= 1400

    def test_trim_end(self) -> None:
        wav_data = _make_wav(duration_ms=2000)
        result = trim(wav_data, end_ms=1000, fmt="wav")
        assert result.duration_ms <= 1050

    def test_trim_start_and_end(self) -> None:
        wav_data = _make_wav(duration_ms=3000)
        result = trim(wav_data, start_ms=500, end_ms=2000, fmt="wav")
        assert abs(result.duration_ms - 1500) < 50


# ---------------------------------------------------------------------------
# Tests: merge()
# ---------------------------------------------------------------------------


class TestMerge:
    def test_merge_two_files(self) -> None:
        wav1 = _make_wav(duration_ms=1000)
        wav2 = _make_wav(duration_ms=1000)
        result = merge(wav1, wav2, fmt="wav", output_format="wav")
        assert isinstance(result, AudioResult)
        # Merged should be ~2000ms
        assert result.duration_ms >= 1900

    def test_merge_three_files(self) -> None:
        wav1 = _make_wav(duration_ms=500)
        wav2 = _make_wav(duration_ms=500)
        wav3 = _make_wav(duration_ms=500)
        result = merge(wav1, wav2, wav3, fmt="wav", output_format="wav")
        assert result.duration_ms >= 1400

    def test_merge_requires_two_sources(self) -> None:
        wav = _make_wav()
        with pytest.raises(ValueError, match="at least 2"):
            merge(wav, fmt="wav")


# ---------------------------------------------------------------------------
# Tests: normalize()
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_normalize_returns_result(self) -> None:
        wav_data = _make_wav()
        result = normalize(wav_data, target_dbfs=-20.0, fmt="wav")
        assert isinstance(result, AudioResult)
        assert result.size_bytes > 0

    def test_normalize_preserves_duration(self) -> None:
        wav_data = _make_wav(duration_ms=1000)
        result = normalize(wav_data, fmt="wav")
        assert abs(result.duration_ms - 1000) < 50


# ---------------------------------------------------------------------------
# Tests: change_volume()
# ---------------------------------------------------------------------------


class TestChangeVolume:
    def test_increase_volume(self) -> None:
        wav_data = _make_wav()
        result = change_volume(wav_data, db=5.0, fmt="wav")
        assert isinstance(result, AudioResult)
        assert result.size_bytes > 0

    def test_decrease_volume(self) -> None:
        wav_data = _make_wav()
        result = change_volume(wav_data, db=-10.0, fmt="wav")
        assert isinstance(result, AudioResult)
        assert result.size_bytes > 0


# ---------------------------------------------------------------------------
# Tests: fade()
# ---------------------------------------------------------------------------


class TestFade:
    def test_fade_in(self) -> None:
        wav_data = _make_wav(duration_ms=2000)
        result = fade(wav_data, fade_in_ms=500, fmt="wav")
        assert isinstance(result, AudioResult)
        assert abs(result.duration_ms - 2000) < 50

    def test_fade_out(self) -> None:
        wav_data = _make_wav(duration_ms=2000)
        result = fade(wav_data, fade_out_ms=500, fmt="wav")
        assert isinstance(result, AudioResult)

    def test_fade_in_and_out(self) -> None:
        wav_data = _make_wav(duration_ms=3000)
        result = fade(wav_data, fade_in_ms=500, fade_out_ms=500, fmt="wav")
        assert isinstance(result, AudioResult)
        assert abs(result.duration_ms - 3000) < 50


# ---------------------------------------------------------------------------
# Tests: reverse_audio()
# ---------------------------------------------------------------------------


class TestReverse:
    def test_reverse_same_duration(self) -> None:
        wav_data = _make_wav(duration_ms=1000)
        result = reverse_audio(wav_data, fmt="wav")
        assert isinstance(result, AudioResult)
        assert abs(result.duration_ms - 1000) < 50

    def test_reverse_returns_data(self) -> None:
        wav_data = _make_wav()
        result = reverse_audio(wav_data, fmt="wav")
        assert result.size_bytes > 0


# ---------------------------------------------------------------------------
# Tests: silence()
# ---------------------------------------------------------------------------


class TestSilence:
    def test_silence_duration(self) -> None:
        result = silence(duration_ms=2000)
        assert isinstance(result, AudioResult)
        assert abs(result.duration_ms - 2000) < 50

    def test_silence_default_duration(self) -> None:
        result = silence()
        assert abs(result.duration_ms - 1000) < 50

    def test_silence_format(self) -> None:
        result = silence()
        assert result.format == "wav"


# ---------------------------------------------------------------------------
# Tests: speed()
# ---------------------------------------------------------------------------


class TestSpeed:
    def test_speed_double(self) -> None:
        wav_data = _make_wav(duration_ms=2000)
        result = speed(wav_data, factor=2.0, fmt="wav")
        assert isinstance(result, AudioResult)
        # 2x speed = ~half duration
        assert result.duration_ms < 1200

    def test_speed_half(self) -> None:
        wav_data = _make_wav(duration_ms=1000)
        result = speed(wav_data, factor=0.5, fmt="wav")
        # 0.5x speed = ~double duration
        assert result.duration_ms > 1800

    def test_speed_invalid_factor(self) -> None:
        wav_data = _make_wav()
        with pytest.raises(ValueError, match="positive"):
            speed(wav_data, factor=0.0, fmt="wav")

    def test_speed_negative_factor(self) -> None:
        wav_data = _make_wav()
        with pytest.raises(ValueError, match="positive"):
            speed(wav_data, factor=-1.0, fmt="wav")


# ---------------------------------------------------------------------------
# Tests: convert() — WAV to WAV roundtrip (no ffmpeg needed)
# ---------------------------------------------------------------------------


class TestConvert:
    def test_wav_to_wav(self) -> None:
        wav_data = _make_wav()
        result = convert(wav_data, target_format="wav")
        assert isinstance(result, AudioResult)
        assert result.format == "wav"
        assert result.size_bytes > 0

    def test_convert_from_path(self, tmp_path: Path) -> None:
        wav_data = _make_wav()
        wav_file = tmp_path / "input.wav"
        wav_file.write_bytes(wav_data)
        result = convert(wav_file, target_format="wav")
        assert result.size_bytes > 0


# ---------------------------------------------------------------------------
# Tests: overlay()
# ---------------------------------------------------------------------------


class TestOverlay:
    def test_overlay_same_length(self) -> None:
        wav1 = _make_wav(duration_ms=1000, frequency=440.0)
        wav2 = _make_wav(duration_ms=1000, frequency=880.0)
        result = overlay(wav1, wav2, fmt="wav")
        assert isinstance(result, AudioResult)
        assert abs(result.duration_ms - 1000) < 50

    def test_overlay_with_position(self) -> None:
        wav1 = _make_wav(duration_ms=2000, frequency=440.0)
        wav2 = _make_wav(duration_ms=500, frequency=880.0)
        result = overlay(wav1, wav2, position_ms=500, fmt="wav")
        assert abs(result.duration_ms - 2000) < 50


# ---------------------------------------------------------------------------
# Tests: split_on_silence()
# ---------------------------------------------------------------------------


class TestSplitOnSilence:
    def test_split_continuous_audio(self) -> None:
        # A continuous sine wave should not split (no silence)
        wav_data = _make_wav(duration_ms=1000)
        result = split_on_silence(wav_data, min_silence_ms=200, silence_thresh_db=-50, fmt="wav")
        # Should return 1 chunk (no silence to split on) or possibly 0 if entire audio
        # is below threshold
        assert isinstance(result, list)

    def test_split_returns_audio_results(self) -> None:
        wav_data = _make_wav(duration_ms=500)
        result = split_on_silence(wav_data, min_silence_ms=100, silence_thresh_db=-60, fmt="wav")
        for chunk in result:
            assert isinstance(chunk, AudioResult)


# ---------------------------------------------------------------------------
# Tests: file path handling
# ---------------------------------------------------------------------------


class TestFilePathHandling:
    def test_load_from_string_path(self, tmp_path: Path) -> None:
        wav_data = _make_wav()
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(wav_data)
        result = info(str(wav_file))
        assert result.duration_ms > 0

    def test_load_from_path_object(self, tmp_path: Path) -> None:
        wav_data = _make_wav()
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(wav_data)
        result = info(wav_file)
        assert result.duration_ms > 0

    def test_load_from_bytes(self) -> None:
        wav_data = _make_wav()
        result = info(wav_data, fmt="wav")
        assert result.duration_ms > 0
