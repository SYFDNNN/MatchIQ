from __future__ import annotations

import argparse
import threading
import webbrowser

from matchiq.web import create_app


app = create_app()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jalankan MatchIQ secara lokal.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    parser.add_argument("--open-browser", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
    app.run(host=args.host, port=args.port, debug=False)
