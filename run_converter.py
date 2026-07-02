from __future__ import annotations

import os
import threading
import webbrowser
from urllib.error import URLError
from urllib.request import urlopen

from app import app, choose_port, prepare_storage


def is_converter_running(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/", timeout=0.5) as response:
            html = response.read(4096).decode("utf-8", errors="ignore")
    except (OSError, URLError):
        return False

    return "FILE CONVERTER" in html


def find_running_converter(start_port: int = 5000, attempts: int = 20) -> int | None:
    for port in range(start_port, start_port + attempts):
        if is_converter_running(port):
            return port
    return None


def open_browser(url: str) -> None:
    webbrowser.open(url)


def main() -> None:
    prepare_storage()
    port_text = os.environ.get("FILE_CONVERTER_PORT", "").strip()
    if port_text:
        port = int(port_text)
    else:
        running_port = find_running_converter()
        if running_port is not None:
            url = f"http://127.0.0.1:{running_port}/"
            print(f"File Converter is already running at {url}")
            open_browser(url)
            return

        port = choose_port()

    url = f"http://127.0.0.1:{port}/"

    print(f"File Converter is starting at {url}")
    threading.Timer(1.0, open_browser, args=(url,)).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
