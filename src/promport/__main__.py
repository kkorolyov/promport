import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import environ
from typing import BinaryIO

data = environ["DATA"]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(f"handling request to {self.path} from {self.client_address}")

        match self.path:
            case "/import":
                self._handleImport()
            case _:
                raise RuntimeError(f"unknown path: {self.path}")

    def _handleImport(self):
        try:
            importFile = self._writeFile(self.rfile)
            self._tsdbImport(importFile)

            self.send_response(200)
            self.end_headers()
        except RuntimeError as e:
            print(f"error handling request: {e}")
            self.send_response(500, str(e))

    def _writeFile(self, b: BinaryIO):
        importFile = "import.om"
        with open(importFile, "wb") as f:
            print(f"writing request data to {importFile}...")
            f.writelines(b)
            print(f"done writing")

        return importFile

    def _tsdbImport(self, path: str):
        print(f"importing TSDB data at {path} to {data}...")
        subprocess.check_call(
            [
                "promtool",
                "tsdb",
                "create-blocks-from",
                "openmetrics",
                "--max-block-duration",
                "87600",
                path,
                data,
            ]
        )
        print("done importing")


def checkArgs():
    if not data:
        print("missing DATA env var")
        exit(1)


def main():
    address = "0.0.0.0"
    port = 9191

    httpd = HTTPServer((address, port), Handler)
    print(f"started server at {address}:{port}, with config (data={data})")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
