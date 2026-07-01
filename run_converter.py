from __future__ import annotations

import os
import threading
import webbrowser

from app import app, choose_port, prepare_storage


def open_browser(url: str) -> None:
    webbrowser.open(url)


def main() -> None:
    prepare_storage()
    port_text = os.environ.get("FILE_CONVERTER_PORT", "").strip()
    port = int(port_text) if port_text else choose_port()
    url = f"http://127.0.0.1:{port}/"

    print(f"File Converter is starting at {url}")
    threading.Timer(1.0, open_browser, args=(url,)).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
