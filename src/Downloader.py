from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from src.Manifest import IIIFManifest
from utils import create_dir
from utils.constants import MIN_SIZE, MAX_SIZE, IMG_PATH, DEBUG
from utils.logger import logger


class IIIFDownloader:
    """Manages the download of IIIF manifests and their images."""

    def __init__(
        self,
        max_dim: int = MAX_SIZE,
        min_dim: int = MIN_SIZE,
        img_path: Optional[Path] = IMG_PATH,
        allow_truncation: bool = False
    ):
        self.img_path = img_path
        self.max_dim = max_dim  # Pass to children classes
        self.min_dim = min_dim  # Pass to children classes
        self.allow_truncation = allow_truncation  # Pass to children classes

    def download_manifest(self, url: str, save_dir: Optional[Path] = None) -> bool:
        """Download a complete manifest and all its images."""
        url = unquote(url)
        manifest = IIIFManifest(url, img_dir=self.img_path, manifest_dir_name=save_dir)

        # Create directory and save metadata
        create_dir(manifest.manifest_dir)
        with open(manifest.manifest_dir / "info.txt", "w") as f:
            f.write(f"{manifest.url}\n")

        if not manifest.load():
            return False

        # Create directory and save metadata
        create_dir(manifest.manifest_dir)
        with open(manifest.manifest_dir / "info.txt", "a") as f:
            f.write(f"{manifest.license}\n")

        # Get and download images
        images = manifest.get_images()
        if not images:
            logger.warning(f"No images found in manifest {url}")
            return False

        for i, image in enumerate(logger.progress(images, desc=f"Downloading {url}"), start=1):
            if DEBUG and i == 6:
                break

            if not image.save():
                logger.error(f"Failed to download image #{image.idx} ({image.sized_url()})")
                continue

        return True