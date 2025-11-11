#!/usr/bin/env python3
"""Small helper to download a Kaggle dataset into the project using the Kaggle API.

Usage:
  python scripts/download_kaggle.py owner/dataset-name --dest data --file filename.csv

This will download and unzip the dataset to the `--dest` folder. If `--file` is provided,
the script will print the path to that file (useful for setting DATASET_CSV).

Security: The script expects Kaggle credentials to be available either via
  - environment variables KAGGLE_USERNAME and KAGGLE_KEY, or
  - an existing ~/.kaggle/kaggle.json file. You can create the file from the token
    you showed by placing {"username":"...","key":"..."} in ~/.kaggle/kaggle.json
    and setting `chmod 600 ~/.kaggle/kaggle.json`.
"""
import argparse
import os
import sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("dataset", help="Kaggle dataset identifier, e.g. zynicide/wine-reviews or owner/dataset-name")
    p.add_argument("--dest", default="data", help="Destination folder inside the project")
    p.add_argument("--file", default=None, help="If you only need a specific file name from the dataset, e.g. data.csv")
    args = p.parse_args()

    # try to import kaggle (will give a helpful error if missing)
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception as e:
        print("Missing 'kaggle' package. Install with: python -m pip install kaggle")
        sys.exit(2)

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as e:
        print("Failed to authenticate with Kaggle. Ensure ~/.kaggle/kaggle.json exists or set KAGGLE_USERNAME/KAGGLE_KEY env vars.")
        print(str(e))
        sys.exit(3)

    try:
        print(f"Downloading dataset {args.dataset} to {dest} ...")
        api.dataset_download_files(args.dataset, path=str(dest), unzip=True, quiet=False)
    except Exception as e:
        print("Download failed:", e)
        sys.exit(4)

    if args.file:
        candidate = dest / args.file
        if candidate.exists():
            print(candidate)
        else:
            print(f"Requested file {args.file} not found in {dest}")
            # list files
            files = list(dest.glob("**/*"))
            print("Files in dest:")
            for f in files:
                print(" -", f)

    print("Done.")

if __name__ == '__main__':
    main()
