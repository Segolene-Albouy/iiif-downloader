from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote

from .config import config
from .manifest import IIIFManifest
from .utils import create_dir
from .utils.logger import logger


class IIIFDownloader:
    """Manages the download of IIIF manifests and their images."""

    def __init__(self, img_dir: Optional[Union[Path, str]] = None):
        self.img_dir = img_dir

    @staticmethod
    def add_to_log(log_file, msg: str, mode="a"):
        """Add a message to the log file."""
        with open(log_file, mode) as f:
            f.write(f"{msg}\n")

    def download_manifest(
        self, url: str, save_dir: Optional[Union[Path, str]] = None
    ) -> Union[bool, IIIFManifest]:
        """Download a complete manifest and all its images."""
        url = unquote(url)
        manifest = IIIFManifest(url, img_dir=self.img_dir, manifest_dir_name=save_dir)

        # Create directory and save metadata
        create_dir(manifest.manifest_dir)
        self.add_to_log(manifest.manifest_dir / "info.txt", manifest.url, "w")

        if not manifest.load():
            return False

        self.add_to_log(manifest.manifest_dir / "info.txt", manifest.license)

        # Get and download images
        images = manifest.get_images()
        if not images:
            logger.warning(f"No images found in manifest {url}")
            return manifest

        img_mapping = {}

        logger.info(f"Downloading {len(images)} images from {url} inside {manifest.manifest_dir}")
        for i, image in enumerate(logger.progress(images, desc="Downloading..."), start=1):
            if config.debug and i > 5:
                break

            if not image.save():
                logger.error(f"Failed to download image #{image.idx} ({image.sized_url()})")
                continue

            img_mapping[image.img_name] = image.sized_url()

        manifest.img_mapping = img_mapping

        return manifest
