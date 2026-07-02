from __future__ import annotations

from pathlib import Path

from video_converter import find_ffmpeg, run_ffmpeg


MP3_BITRATES = ("128k", "192k", "320k")


class AudioConversionError(RuntimeError):
    pass


def normalize_mp3_bitrate(bitrate: str | None) -> str:
    normalized = (bitrate or "192k").lower().strip()
    if normalized not in MP3_BITRATES:
        supported = ", ".join(MP3_BITRATES)
        raise ValueError(f"Unsupported MP3 bitrate: {bitrate}. Supported: {supported}")
    return normalized


def make_audio_output_path(input_path: Path) -> Path:
    output_path = input_path.with_suffix(".mp3")
    if output_path.resolve() == input_path.resolve():
        return input_path.with_name(f"{input_path.stem}_converted.mp3")
    return output_path


def convert_to_mp3(
    input_file: str | Path,
    output_file: str | Path | None = None,
    bitrate: str | None = None,
) -> Path:
    input_path = Path(input_file).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    mp3_bitrate = normalize_mp3_bitrate(bitrate)
    output_path = (
        Path(output_file).expanduser().resolve()
        if output_file is not None
        else make_audio_output_path(input_path)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        find_ffmpeg(),
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0:a:0",
        "-vn",
        "-c:a",
        "libmp3lame",
        "-b:a",
        mp3_bitrate,
        str(output_path),
    ]

    result = run_ffmpeg(command)
    if result.returncode != 0:
        detail = result.stderr.strip() or "Unknown FFmpeg audio error"
        raise AudioConversionError(detail[-1200:])

    return output_path
