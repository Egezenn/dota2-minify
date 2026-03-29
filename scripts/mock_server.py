"Mock server to emulate GitHub Releases API & serve setup"

import http.server
import json
import os
import socketserver

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MOCK_JSON_PATH = os.path.join(DIRECTORY, "releases_mock.json")


def find_latest_installer():
    files = [f for f in os.listdir(DIRECTORY) if f.startswith("Minify-Setup-") and f.endswith(".exe")]
    if not files:
        return None
    # Sort by modification time to get the latest
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DIRECTORY, x)), reverse=True)
    return files[0]


def get_mock_json():
    installer = find_latest_installer()
    version = "99.99.99"  # force
    return [
        {
            "tag_name": f"Minify-v{version}",
            "prerelease": True,
            "assets": [
                {
                    "name": f"Minify-v{version}-windows.exe",
                    "browser_download_url": f"http://localhost:{PORT}/{installer}",
                }
            ],
        }
    ]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/releases_mock.json":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_mock_json(), indent=2).encode())
        else:
            return super().do_GET()


if __name__ == "__main__":
    if not any(f.startswith("Minify-Setup-") for f in os.listdir(DIRECTORY)):
        dummy_exe = os.path.join(DIRECTORY, "Minify-Setup-1.0.exe")
        with open(dummy_exe, "wb") as f:
            f.write(b"This is a dummy installer for testing purposes.")

    print(f"Starting test server at http://localhost:{PORT}")
    print(f"Serving files from: {DIRECTORY}")
    print(f"Mocking releases at: http://localhost:{PORT}/releases_mock.json")

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
