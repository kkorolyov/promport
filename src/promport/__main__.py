import os
import subprocess
from argparse import ArgumentParser, RawTextHelpFormatter
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

import requests


def _parseArgs():
    parser = ArgumentParser(
        prog="promport",
        description="HTTP server exposing endpoints to bulk-upload Prometheus data",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Prometheus API URL to proxy",
        default="http://localhost:9090",
    )
    parser.add_argument("--data", type=str, help="TSDB data directory", required=True)
    parser.add_argument(
        "--maxBlockDuration",
        type=str,
        help="maximum block duration value to forward to promtool",
        default="87600h",
    )

    return parser.parse_args()


class Handler(BaseHTTPRequestHandler):
    _url: str
    _data: str
    _maxBlockDuration: str

    def __init__(
        self, url: str, data: str, maxBlockDuration: str, *args, **kwargs
    ) -> None:
        self._url = url
        self._data = data
        self._maxBlockDuration = maxBlockDuration

        super().__init__(*args, **kwargs)

    def do_POST(self):
        try:
            match self.path:
                case "/import":
                    self._handleImport()
                case "/delete":
                    self._handleDelete()
                case _:
                    self.send_error(404)

            self.send_response(200)
            self.end_headers()
        except Exception as e:
            self.send_error(500)
            raise e

    def _handleImport(self):
        length = self.headers["Content-Length"]
        if not length:
            self.send_error(400, "Missing Content-Length header")
            return

        self.log_message(f"importing data of length {length}...")

        importFile = f"{self._data}/import.om"
        with open(importFile, "wb") as f:
            f.write(self.rfile.read(int(length)))

        subprocess.check_call(
            [
                "promtool",
                "tsdb",
                "create-blocks-from",
                "openmetrics",
                "--max-block-duration",
                self._maxBlockDuration,
                importFile,
                self._data,
            ]
        )

        os.remove(importFile)

    def _handleDelete(self):
        length = self.headers["Content-Length"]
        if not length:
            self.send_error(400, "Missing Content-Length header")
            return

        requests.post(
            f"{self._url}/api/v1/admin/tsdb/delete_series",
            parse_qs(self.rfile.read(int(length)).decode()),
        ).raise_for_status()
        requests.post(
            f"{self._url}/api/v1/admin/tsdb/clean_tombstones"
        ).raise_for_status()


def main():
    args = _parseArgs()

    address = "0.0.0.0"
    port = 9191

    httpd = HTTPServer(
        (address, port), partial(Handler, args.url, args.data, args.maxBlockDuration)
    )
    print(f"started server at {address}:{port}, with args {args}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
