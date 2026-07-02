from __future__ import annotations

from pathlib import Path


IMAGE_OUTPUTS = ("jpg", "png", "webp")
PDF_OUTPUTS = ("jpg", "png", "webp")
VIDEO_OUTPUTS = ("mp4", "mov", "mp3")
AUDIO_OUTPUTS = ("mp3",)

EXTENSION_HINTS = {
    "jpg": ("image", "jpg", "JPG image"),
    "jpeg": ("image", "jpg", "JPG image"),
    "png": ("image", "png", "PNG image"),
    "webp": ("image", "webp", "WEBP image"),
    "bmp": ("image", "bmp", "BMP image"),
    "tif": ("image", "tiff", "TIFF image"),
    "tiff": ("image", "tiff", "TIFF image"),
    "gif": ("image", "gif", "GIF image"),
    "mp4": ("video", "mp4", "MP4 video"),
    "mov": ("video", "mov", "QuickTime video"),
    "webm": ("video", "webm", "WEBM video"),
    "mp3": ("audio", "mp3", "MP3 audio"),
    "m4a": ("audio", "m4a", "M4A audio"),
    "aac": ("audio", "aac", "AAC audio"),
    "wav": ("audio", "wav", "WAV audio"),
    "flac": ("audio", "flac", "FLAC audio"),
    "ogg": ("audio", "ogg", "OGG audio"),
    "pdf": ("document", "pdf", "PDF document"),
    "zip": ("archive", "zip", "ZIP archive"),
}


def detect_magic(header: bytes) -> tuple[str, str, str] | None:
    if header.startswith(b"\xff\xd8\xff"):
        return ("image", "jpg", "JPG image")
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ("image", "png", "PNG image")
    if header[:6] in (b"GIF87a", b"GIF89a"):
        return ("image", "gif", "GIF image")
    if header.startswith(b"BM"):
        return ("image", "bmp", "BMP image")
    if header.startswith((b"II*\x00", b"MM\x00*")):
        return ("image", "tiff", "TIFF image")
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ("image", "webp", "WEBP image")
    if header.startswith(b"%PDF-"):
        return ("document", "pdf", "PDF document")
    if header.startswith(b"PK\x03\x04"):
        return ("archive", "zip", "ZIP archive")
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12].lower()
        if brand in (b"m4a ", b"m4b "):
            return ("audio", "m4a", "M4A audio")
        if brand in (b"qt  ",):
            return ("video", "mov", "QuickTime video")
        return ("video", "mp4", "MP4 video")
    if header.startswith(b"ID3") or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ("audio", "mp3", "MP3 audio")
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return ("audio", "wav", "WAV audio")
    if header.startswith(b"fLaC"):
        return ("audio", "flac", "FLAC audio")
    if header.startswith(b"OggS"):
        return ("audio", "ogg", "OGG audio")

    return None


def outputs_for_format(kind: str, file_format: str) -> tuple[str, ...]:
    if kind == "image":
        return IMAGE_OUTPUTS
    if kind == "document" and file_format == "pdf":
        return PDF_OUTPUTS
    if kind == "video":
        return VIDEO_OUTPUTS
    if kind == "audio":
        return AUDIO_OUTPUTS
    return ()


def detect_file_info(filename: str, header: bytes) -> dict[str, object]:
    extension = Path(filename).suffix.lower().lstrip(".")
    extension_hint = EXTENSION_HINTS.get(extension)
    magic_hint = detect_magic(header)
    best_hint = magic_hint or extension_hint

    if best_hint is None:
        kind, file_format, label = ("unknown", extension or "unknown", "Unknown file")
    else:
        kind, file_format, label = best_hint

    return {
        "kind": kind,
        "format": file_format,
        "label": label,
        "extension": extension,
        "extension_label": extension_hint[2] if extension_hint else None,
        "magic_label": magic_hint[2] if magic_hint else None,
        "outputs": list(outputs_for_format(kind, file_format)),
    }
