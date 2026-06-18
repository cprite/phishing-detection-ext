"""
build_cws.py — produce the Chrome Web Store build from this open-source repo.

The repository itself is the OPEN-SOURCE build (config.js sets IS_OSS_BUILD=true):
it ships the in-browser self-learning loop (the popup's "Mark as phishing" button
and "Proceed" both add KNN feedback points).

This script emits the STORE build, which strips that:
  * copies only the files the extension loads,
  * rewrites extension/config.js so IS_OSS_BUILD=false (hides the feedback
    button; "Proceed" no longer adds points; the store build never collects
    feedback),
  * excludes the Python/training files, the dataset and the docs site,
  * zips the result for upload.

Output:
    dist/cws/                 unpacked store build (load this to verify)
    dist/no-phishing-cws.zip  upload this to the Chrome Web Store

Usage:
    python build_cws.py
"""

import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "dist", "cws")
ZIP = os.path.join(ROOT, "dist", "no-phishing-cws.zip")

# Exactly the files Chrome loads. Everything else (Python, dataset, docs, tests,
# git) is intentionally left out of the store package.
INCLUDE = [
    "manifest.json",
    "extension",
    "images",
    "saved_models",
    "LICENSE.md",
]


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    for item in INCLUDE:
        src = os.path.join(ROOT, item)
        dst = os.path.join(OUT, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            print(f"  warning: {item} not found, skipping")

    # Flip the build flag off so all OSS-only feedback UI/logic is disabled.
    cfg = os.path.join(OUT, "extension", "config.js")
    with open(cfg) as f:
        text = f.read()
    new_text = re.sub(r"var IS_OSS_BUILD = true;", "var IS_OSS_BUILD = false;", text)
    if new_text == text:
        raise SystemExit("build_cws.py: could not flip IS_OSS_BUILD in config.js")
    with open(cfg, "w") as f:
        f.write(new_text)

    # Zip it for upload.
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, _, files in os.walk(OUT):
            for name in files:
                path = os.path.join(folder, name)
                z.write(path, os.path.relpath(path, OUT))

    print(f"Store build written to {OUT}")
    print(f"Upload package:        {ZIP}")
    print("IS_OSS_BUILD=false — the feedback button is hidden and no feedback "
          "points are collected in this build.")


if __name__ == "__main__":
    main()
