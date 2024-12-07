import argparse

from .downloader import IIIFDownloader
from .utils.logger import logger


def main():
    parser = argparse.ArgumentParser(description='Download IIIF manifest images')
    parser.add_argument('-f', '--file', type=str, required=True, help='File containing manifest URLs')
    parser.add_argument('-o', '--output', type=str, required=False, help='Path where to save downloaded images')
    args = parser.parse_args()

    with open(args.file) as f:
        manifests = [line.strip() for line in f if line.strip()]

    if not manifests:
        logger.error("No manifests found in input file")
        return 1

    downloader = IIIFDownloader(img_path=args.output)

    for url in logger.progress(manifests, desc="Processing manifests"):
        try:
            downloader.download_manifest(url, save_dir=None)
        except Exception as e:
            logger.error(f"Failed to process {url}", exception=e)

    return 0


if __name__ == "__main__":
    exit(main())
