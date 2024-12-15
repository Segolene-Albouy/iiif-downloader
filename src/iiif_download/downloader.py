import asyncio
import json
from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote

from .config import config
from .manifest import IIIFManifest
from .utils import create_dir
from .utils.logger import logger


class IIIFDownloader:
    """Manages the download of IIIF manifests and their images."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(config, key, value)

        self._manifest_info = {}

    def add_to_log(self, log_file, mode="w"):
        """Add a message to the log file."""
        with open(log_file, mode) as f:
            json.dump(self._manifest_info, f)

    def download_manifest(
        self, url: str, save_dir: Optional[Union[Path, str]] = None
    ) -> Union[bool, IIIFManifest]:
        """Download a complete manifest and all its images."""

        async def _async_download_manifest():
            manifest = IIIFManifest(unquote(url), manifest_dir_name=save_dir)

            # Create directory and save metadata
            create_dir(manifest.manifest_dir)

            if not manifest.load():
                return False

            if config.is_logged:
                self._manifest_info = {"url": manifest.url, "license": manifest.license, "images": {}}

            images = manifest.get_images()
            if not images:
                logger.warning(f"No images found in manifest {url}")
                return manifest

            logger.info(f"Downloading {len(images)} images from {url} inside {manifest.manifest_dir}")
            for i, image in enumerate(logger.progress(images, desc="Downloading..."), start=1):
                if config.debug and i > 5:
                    break

                success = await image.save()
                if not success:
                    logger.error(f"Failed to download image #{image.idx} ({image.sized_url()})")
                    continue

                if config.is_logged:
                    self._manifest_info["images"][image.img_name] = image.sized_url()

            if config.is_logged:
                self.add_to_log(manifest.manifest_dir / "info.json")

            return manifest

        return asyncio.run(_async_download_manifest())
