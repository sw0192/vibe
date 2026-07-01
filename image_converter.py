from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


FORMAT_ALIASES = {
    "jpg": ("JPEG", ".jpg"),
    "jpeg": ("JPEG", ".jpg"),
    "png": ("PNG", ".png"),
    "webp": ("WEBP", ".webp"),
    "bmp": ("BMP", ".bmp"),
    "tif": ("TIFF", ".tiff"),
    "tiff": ("TIFF", ".tiff"),
}


def normalize_format(target_format: str) -> tuple[str, str]:
    key = target_format.lower().lstrip(".")
    if key not in FORMAT_ALIASES:
        supported = ", ".join(sorted(FORMAT_ALIASES))
        raise ValueError(f"Unsupported target format: {target_format}. Supported: {supported}")
    return FORMAT_ALIASES[key]


def make_output_path(input_path: Path, extension: str) -> Path:
    output_path = input_path.with_suffix(extension)
    if output_path.resolve() == input_path.resolve():
        return input_path.with_name(f"{input_path.stem}_converted{extension}")
    return output_path


def flatten_transparency_to_white(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    background.alpha_composite(image)
    return background.convert("RGB")


def convert_image(
    input_file: str | Path,
    target_format: str,
    output_file: str | Path | None = None,
    quality: int = 95,
) -> Path:
    input_path = Path(input_file).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    save_format, extension = normalize_format(target_format)
    output_path = (
        Path(output_file).expanduser().resolve()
        if output_file is not None
        else make_output_path(input_path, extension)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as source:
        image = ImageOps.exif_transpose(source)

        if save_format == "JPEG":
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = flatten_transparency_to_white(image)
            else:
                image = image.convert("RGB")

        save_options: dict[str, int | bool] = {}
        if save_format == "JPEG":
            save_options = {"quality": quality, "optimize": True}
        elif save_format == "PNG":
            save_options = {"optimize": True}
        elif save_format == "WEBP":
            save_options = {"quality": quality}

        image.save(output_path, save_format, **save_options)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one image file to another format with Pillow."
    )
    parser.add_argument("input_file", help="Path to the source image file.")
    parser.add_argument("target_format", help="Target format, such as jpg, png, or webp.")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Optional output file path. Defaults to the input name with a new extension.",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=95,
        help="JPEG/WEBP quality from 1 to 100. Default: 95.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = convert_image(
        args.input_file,
        args.target_format,
        output_file=args.output_file,
        quality=args.quality,
    )
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
