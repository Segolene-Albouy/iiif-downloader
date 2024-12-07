from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from .manifest import IIIFManifest
from .config import config
from .utils import create_dir
from .utils.logger import logger


class IIIFDownloader:
    """Manages the download of IIIF manifests and their images."""

    def __init__(self, img_dir: Optional[Path | str] = None):
        self.img_dir = img_dir

    @staticmethod
    def add_to_log(log_file, msg: str, mode="a"):
        """Add a message to the log file."""
        with open(log_file, mode) as f:
            f.write(f"{msg}\n")

    def download_manifest(self, url: str, save_dir: Optional[Path | str] = None) -> bool | IIIFManifest:
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

        logger.info(f"Downloading {len(images)} images from {url} inside {manifest.manifest_dir}")
        for i, image in enumerate(logger.progress(images, desc=f"Downloading..."), start=1):
            if config.debug and i > 5:
                break

            if not image.save():
                logger.error(f"Failed to download image #{image.idx} ({image.sized_url()})")
                continue

        # TODO add image mapping
        # all_img_mapping = []
        # if manifest is not None:
        #     console(f"Processing {self.manifest_url}...")
        #     if not check_dir(self.manifest_dir_path) or True:
        #         i = 1
        #         for rsrc in get_iiif_resources(manifest):
        #             console(rsrc)
        #             is_downloaded, img_name, img_url = self.save_iiif_img(rsrc, i)
        #             i += 1
        #             if img_name is not None:
        #                 all_img_mapping.append((img_name, img_url))
        #             if is_downloaded:
        #                 # Gallica is not accepting more than 5 downloads of >1000px per min
        #                 time.sleep(12 if "gallica" in self.manifest_url else 0.25)
        #                 time.sleep(self.sleep)
        # return all_img_mapping

        return manifest
