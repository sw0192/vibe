from __future__ import annotations

import socket
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from file_detector import IMAGE_OUTPUTS, VIDEO_OUTPUTS, detect_file_info
from image_converter import convert_image, normalize_format
from video_converter import FFmpegNotFoundError, VideoConversionError, convert_video, normalize_video_format


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
OUTPUT_DIR = BASE_DIR / "storage" / "outputs"
TARGET_FORMATS = IMAGE_OUTPUTS + VIDEO_OUTPUTS
MAX_UPLOAD_MB = 1024
APP_VERSION = "2026-07-02-ffmpeg-video"


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


class ConversionInputError(ValueError):
    pass


class ConversionNotReady(RuntimeError):
    def __init__(self, message: str, file_info: dict[str, object]):
        super().__init__(message)
        self.file_info = file_info


def prepare_storage() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def choose_port(start_port: int = 5000, attempts: int = 20) -> int:
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port

    raise RuntimeError("사용 가능한 로컬 포트를 찾지 못했어요.")


def get_target_format() -> str:
    target_format = request.form.get("target_format", "jpg").lower()
    if target_format not in TARGET_FORMATS:
        raise ConversionInputError("지원하지 않는 변환 형식이에요.")
    return target_format


def convert_uploaded_file(uploaded_file, target_format: str) -> dict[str, str]:
    if uploaded_file is None or uploaded_file.filename == "":
        raise ConversionInputError("변환할 파일을 먼저 선택해 주세요.")

    original_name = uploaded_file.filename
    header = uploaded_file.stream.read(64)
    uploaded_file.stream.seek(0)
    file_info = detect_file_info(original_name, header)

    if target_format not in file_info["outputs"]:
        if file_info["outputs"]:
            outputs = ", ".join(str(output).upper() for output in file_info["outputs"])
            message = f"이 파일은 {outputs} 형식으로 변환할 수 있어요."
        else:
            message = f"{file_info['label']}은 아직 변환 지원 예정이에요."
        raise ConversionNotReady(message, file_info)

    prepare_storage()

    job_id = uuid4().hex
    source_extension = Path(original_name).suffix.lower()
    source_path = UPLOAD_DIR / f"{job_id}{source_extension}"
    uploaded_file.save(source_path)

    if file_info["kind"] == "image":
        _, output_extension = normalize_format(target_format)
    elif file_info["kind"] == "video":
        normalized_format = normalize_video_format(target_format)
        output_extension = f".{normalized_format}"
    else:
        label = file_info["label"]
        outputs = ", ".join(str(output).upper() for output in file_info["outputs"])
        output_text = f"추천 출력: {outputs}." if outputs else "추천 출력은 준비 중이에요."
        raise ConversionNotReady(
            f"{label}로 인식했어요. {output_text} 변환 엔진은 다음 단계에서 연결할게요.",
            file_info,
        )

    original_stem = Path(original_name).stem or "image"
    display_output_name = f"{original_stem}{output_extension}"
    safe_output_stem = secure_filename(original_stem) or "image"
    output_path = OUTPUT_DIR / f"{job_id}_{safe_output_stem}{output_extension}"

    try:
        if file_info["kind"] == "image":
            converted_path = convert_image(source_path, target_format, output_file=output_path)
        else:
            converted_path = convert_video(source_path, target_format, output_file=output_path)
    except FFmpegNotFoundError as exc:
        raise ConversionInputError(str(exc)) from exc
    except VideoConversionError as exc:
        raise ConversionInputError(f"영상 변환에 실패했어요. FFmpeg 메시지: {exc}") from exc
    except Exception as exc:
        raise ConversionInputError(f"변환하지 못했어요. 파일을 확인해 주세요. ({exc})") from exc

    return {
        "status": "completed",
        "original_name": original_name,
        "output_name": display_output_name,
        "download_file": converted_path.name,
        "download_url": url_for(
            "download",
            filename=converted_path.name,
            name=display_output_name,
        ),
        "detected_kind": str(file_info["kind"]),
        "detected_format": str(file_info["format"]),
        "recommended_outputs": file_info["outputs"],
    }


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    message = f"파일 용량이 너무 커요. {MAX_UPLOAD_MB}MB 이하 파일로 다시 시도해 주세요."
    if request.path.startswith("/api/"):
        return jsonify({"status": "failed", "message": message}), 413

    return (
        render_template(
            "index.html",
            target_formats=TARGET_FORMATS,
            selected_format="jpg",
            error=message,
            app_version=APP_VERSION,
        ),
        413,
    )


@app.get("/")
def index():
    return render_template(
        "index.html",
        target_formats=TARGET_FORMATS,
        selected_format="jpg",
        app_version=APP_VERSION,
    )


@app.get("/convert")
def convert_get():
    return redirect(url_for("index"))


@app.post("/api/convert")
def convert_api():
    try:
        target_format = get_target_format()
        result = convert_uploaded_file(request.files.get("image"), target_format)
    except ConversionNotReady as exc:
        return jsonify(
            {
                "status": "not_ready",
                "message": str(exc),
                "detected_kind": str(exc.file_info["kind"]),
                "detected_format": str(exc.file_info["format"]),
                "recommended_outputs": exc.file_info["outputs"],
            }
        )
    except ConversionInputError as exc:
        return jsonify({"status": "failed", "message": str(exc)}), 400

    return jsonify(result)


@app.post("/convert")
def convert():
    try:
        target_format = get_target_format()
        result = convert_uploaded_file(request.files.get("image"), target_format)
    except ConversionNotReady as exc:
        return render_template(
            "index.html",
            target_formats=TARGET_FORMATS,
            selected_format=request.form.get("target_format", "jpg"),
            error=str(exc),
            app_version=APP_VERSION,
        )
    except ConversionInputError as exc:
        return render_template(
            "index.html",
            target_formats=TARGET_FORMATS,
            selected_format=request.form.get("target_format", "jpg"),
            error=str(exc),
            app_version=APP_VERSION,
        )

    return render_template(
        "index.html",
        target_formats=TARGET_FORMATS,
        selected_format=target_format,
        original_name=result["original_name"],
        output_name=result["output_name"],
        download_file=result["download_file"],
        success="변환이 끝났어요.",
        app_version=APP_VERSION,
    )


@app.get("/downloads/<filename>")
def download(filename: str):
    download_name = request.args.get("name") or filename
    return send_from_directory(
        OUTPUT_DIR,
        filename,
        as_attachment=True,
        download_name=download_name,
    )


if __name__ == "__main__":
    prepare_storage()
    app.run(host="127.0.0.1", port=choose_port(), debug=True, use_reloader=False, threaded=True)
