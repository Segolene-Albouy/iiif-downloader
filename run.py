import argparse

from src.Downloader import IIIFDownloader
from utils.constants import MIN_SIZE, MAX_SIZE, IMG_PATH
from utils.logger import logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download IIIF manifest images')
    parser.add_argument('-f', '--file', type=str, required=True, help='File containing manifest URLs')
    parser.add_argument('-max', '--max_dim', type=int, default=MAX_SIZE, help='Maximum image dimension')
    parser.add_argument('-min', '--min_dim', type=int, default=MIN_SIZE, help='Minimum image dimension')
    args = parser.parse_args()

    with open(args.file) as f:
        manifests = [line.strip() for line in f if line.strip()]

    if not manifests:
        logger.error("No manifests found in input file")
        exit(1)

    downloader = IIIFDownloader(
        max_dim=args.max_dim,
        min_dim=args.min_dim,
        img_path=IMG_PATH
    )

    for url in logger.progress(manifests, desc="Processing manifests"):
        try:
            downloader.download_manifest(url, save_dir=None)
        except Exception as e:
            logger.error(f"Failed to process {url}", exception=e)