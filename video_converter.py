from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


VIDEO_FORMAT_ALIASES = {
    "mp4": ".mp4",
    "mov": ".mov",
}


class FFmpegNotFoundError(RuntimeError):
    pass


class VideoConversionError(RuntimeError):
    pass


def normalize_video_format(target_format: str) -> str:
    key = target_format.lower().lstrip(".")
    if key not in VIDEO_FORMAT_ALIASES:
        supported = ", ".join(sorted(VIDEO_FORMAT_ALIASES))
        raise ValueError(f"Unsupported video format: {target_format}. Supported: {supported}")
    return key


def find_ffmpeg() -> str:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise FFmpegNotFoundError(
            "FFmpeg를 찾지 못했어요. 런처를 다시 실행해 라이브러리를 설치하거나, "
            "Windows에서는 'winget install Gyan.FFmpeg', macOS에서는 'brew install ffmpeg'를 실행해 주세요."
        ) from exc

    return imageio_ffmpeg.get_ffmpeg_exe()


def make_video_output_path(input_path: Path, extension: str) -> Path:
    output_path = input_path.with_suffix(extension)
    if output_path.resolve() == input_path.resolve():
        return input_path.with_name(f"{input_path.stem}_converted{extension}")
    return output_path


def run_ffmpeg(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def convert_video(
    input_file: str | Path,
    target_format: str,
    output_file: str | Path | None = None,
) -> Path:
    input_path = Path(input_file).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    normalized_format = normalize_video_format(target_format)
    extension = VIDEO_FORMAT_ALIASES[normalized_format]
    output_path = (
        Path(output_file).expanduser().resolve()
        if output_file is not None
        else make_video_output_path(input_path, extension)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()
    copy_command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0",
        "-c",
        "copy",
    ]
    if normalized_format == "mp4":
        copy_command.extend(["-movflags", "+faststart"])
    copy_command.append(str(output_path))

    result = run_ffmpeg(copy_command)
    if result.returncode == 0:
        return output_path

    fallback_command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0:v:0?",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
    ]
    if normalized_format == "mp4":
        fallback_command.extend(["-movflags", "+faststart"])
    fallback_command.append(str(output_path))

    fallback_result = run_ffmpeg(fallback_command)
    if fallback_result.returncode != 0:
        detail = fallback_result.stderr.strip() or result.stderr.strip() or "Unknown FFmpeg error"
        raise VideoConversionError(detail[-1200:])

    return output_path
