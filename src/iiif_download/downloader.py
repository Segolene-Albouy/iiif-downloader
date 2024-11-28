from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from .manifest import IIIFManifest
from .config import config
from .utils import create_dir
from .utils.logger import logger


class IIIFDownloader:
    """Manages the download of IIIF manifests and their images."""

    def __init__(self, img_path: Optional[Path] = None):
        self.img_path = img_path

    @staticmethod
    def add_to_log(log_file, msg: str, mode="a"):
        """Add a message to the log file."""
        with open(log_file, mode) as f:
            f.write(f"{msg}\n")

    # TODO allow downloading from json file
    def download_manifest(self, url: str, save_dir: Optional[Path] = None) -> bool | IIIFManifest:
        """Download a complete manifest and all its images."""
        url = unquote(url)
        manifest = IIIFManifest(url, img_dir=self.img_path, manifest_dir_name=save_dir)

        # Create directory and save metadata
        create_dir(manifest.manifest_dir)
        self.add_to_log(manifest.manifest_dir / "info.txt", manifest.url, "w")

        if not manifest.load():
            return False

        # Create directory and save metadata
        create_dir(manifest.manifest_dir)
        self.add_to_log(manifest.manifest_dir / "info.txt", manifest.license)

        # Get and download images
        images = manifest.get_images()
        if not images:
            logger.warning(f"No images found in manifest {url}")
            return manifest

        for i, image in enumerate(logger.progress(images, desc=f"Downloading {url}"), start=1):
            if config.debug and i > 5:
                break

            if not image.save():
                logger.error(f"Failed to download image #{image.idx} ({image.sized_url()})")
                continue

        return manifest
