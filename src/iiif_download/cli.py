#!/usr/bin/env python3

import argparse

from .config import config
from .manifest import IIIFManifest
from .utils.logger import logger


def main():
    parser = argparse.ArgumentParser(description="Download IIIF manifest images")
    parser.add_argument("manifest_url", type=str, nargs="?", help="Single manifest URL to download")
    parser.add_argument("-f", "--file", type=str, help="File containing manifest URLs, one per line")
    parser.add_argument("-d", "--img_dir", type=str, help="Path where to save downloaded images")
    args = parser.parse_args()

    # Ensure at least one input is provided
    if not args.manifest_url and not args.file:
        logger.error("You must provide either a manifest URL or a file with URLs")
        parser.print_usage()
        return 1

    # Read manifests from the file if provided
    manifests = []
    if args.file:
        try:
            with open(args.file) as f:
                manifests.extend(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to read file {args.file}", exception=e)
            return 1

    # Add the single manifest URL if provided
    if args.manifest_url:
        manifests.append(args.manifest_url)

    if not manifests:
        logger.error("No valid manifest URLs found")
        return 1

    config.img_dir = args.img_dir

    logger.info(f"Downloading {len(manifests)} manifests inside {config.img_dir}")

    for url in logger.progress(manifests, desc="Processing manifests"):
        try:
            IIIFManifest(url, save_dir=None).download()
        except Exception as e:
            logger.error(f"Failed to process {url}", exception=e)

    return 0


if __name__ == "__main__":
    exit(main())
