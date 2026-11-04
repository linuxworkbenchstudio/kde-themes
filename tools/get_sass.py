#!/usr/bin/env python3
"""Fetch Dart Sass 1.78.0 (the version the GTK themes are compiled with) into .cache/dart-sass/.

    python3 tools/get_sass.py

1.79 and later round colours differently, so the GTK stylesheets would no longer match the
releases. The engine finds it there; or set SASS to another 1.78.0 binary.
"""
import io
import platform
import sys
import tarfile
import urllib.request
from pathlib import Path

VERSION = "1.78.0"
ROOT = Path(__file__).resolve().parent.parent
ARCH = {"x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}


def main():
    arch = ARCH.get(platform.machine())
    if not arch or sys.platform != "linux":
        print(f"no Dart Sass download for {sys.platform} {platform.machine()}; set SASS instead")
        return 1
    url = f"https://github.com/sass/dart-sass/releases/download/{VERSION}/dart-sass-{VERSION}-linux-{arch}.tar.gz"
    dest = ROOT / ".cache"
    dest.mkdir(exist_ok=True)
    with urllib.request.urlopen(url) as r:
        tarfile.open(fileobj=io.BytesIO(r.read()), mode="r:gz").extractall(dest, filter="data")
    print(f"Dart Sass {VERSION} in {dest / 'dart-sass'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
