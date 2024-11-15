import argparse
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image, UnidentifiedImageError
import requests
from urllib.parse import urlparse

from utils import (
    MAX_SIZE, IMG_PATH, sanitize_str, get_json, save_img,
    create_dir, get_height, get_width, get_id, sanitize_url, get_meta_value
)
from utils.constants import MIN_SIZE, DEBUG
from utils.logger import logger


class Downloader:
    """Download all image resources from a IIIF manifest.

    Args:
        manifest_url (str): URL of the IIIF manifest
        max_dim (int, optional): Maximum dimension for downloaded images. Defaults to MAX_SIZE.
        min_dim (int, optional): Minimum dimension for downloaded images. Defaults to 1500.
        allow_truncation (bool, optional): Whether to allow truncated images. Defaults to False.

    Attributes:
        manifest_url (str): URL of the current manifest
        manifest_dir_path (Path): Path where images will be saved
        max_dim (int): Maximum dimension for images
        min_dim (int): Minimum dimension for images
        allow_truncation (bool): Whether to allow truncated images
    """

    def __init__(
        self,
        manifest_url: str,
        dir_name: Optional[str] = None,
        max_dim: int = MAX_SIZE,
        min_dim: int = MIN_SIZE,
        allow_truncation: bool = False,
    ):
        self.manifest_url = manifest_url
        self.manifest_json: Optional[Dict[str, Any]] = None
        self.manifest_dir_path = IMG_PATH / dir_name if dir_name else None
        self.current_url = ""
        self.max_dim = max_dim
        self.min_dim = min_dim
        self.allow_truncation = allow_truncation

    @property
    def manifest_id(self):
        # TODO get better identifier for the manifest
        manifest_id = get_id(self.manifest_json)
        if manifest_id is None:
            return self.get_dir_name()
        if "manifest" in manifest_id:
            try:
                manifest_id = Path(urlparse(manifest_id).path).parent.name
                if "manifest" in manifest_id:
                    return self.get_dir_name()
                return sanitize_str(manifest_id)
            except Exception:
                return self.get_dir_name()
        return sanitize_str(manifest_id.split("/")[-1])

    @property
    def licence(self) -> str:
        """Extract license information from manifest."""
        manifest = self.manifest_json
        if "license" in manifest:
            return manifest["license"]

        if "metadata" not in manifest:
            if "attribution" in manifest:
                return manifest["attribution"]

        labels = [
            "license",
            "license",
            "lizenz",
            "rights",
            "droits",
            "access",
            "copyright",
            "rechteinformationen",
            "conditions",
        ]
        for label in labels:
            for item in manifest["metadata"]:
                if label in str(item.get("label", "")).lower():
                    return item.get("value", "")

        for label in labels:
            for metadatum in manifest["metadata"]:
                if value := get_meta_value(metadatum, label):
                    return value
        if "attribution" in manifest:
            return manifest["attribution"]
        return "No license information found"

    def run(self) -> bool:
        """Process the manifest and download all images"""
        if not self.get_manifest_json():
            logger.error(f"Failed to get manifest json content from {self.manifest_url}")
            return False

        logger.info(f"Processing {self.manifest_url}...")

        if not self.get_manifest_metadata():
            logger.error(f"Failed to get metadata from {self.manifest_url}")
            return False

        resources = self.get_iiif_resources()

        if not resources:
            logger.warning(f"No resources found in manifest {self.manifest_url}")
            return False

        for i, rsrc in enumerate(logger.progress(resources, desc=f"Downloading {self.manifest_url}..."), 1):
            if DEBUG and i == 4:
                break
            if not self.save_iiif_img(rsrc, i):
                logger.error(f"Failed to save {self.current_url}")
                continue

        return True

    def get_manifest_json(self):
        try:
            self.manifest_json = get_json(self.manifest_url)
        except Exception as e:
            logger.error(f"Failed to get json manifest from {self.manifest_url}", exception=e)
            return False
        return self.manifest_json

    def get_manifest_metadata(self):
        if not self.manifest_dir_path:
            self.manifest_dir_path = create_dir(IMG_PATH / self.manifest_id)

        with open(self.manifest_dir_path / "info.txt", "w") as file:
            file.write(self.licence)

    def save_iiif_img(
        self,
        img_rsrc: Dict[str, Any],
        i: int, size: Optional[str] = None,
        re_download: bool = False
    ) -> bool:
        """Save a single IIIF image.

        Args:
            img_rsrc: Resource object from manifest
            i: Image number
            size: Size specification for image
            re_download: Whether to force re-download

        Returns:
            bool: True if successful, False otherwise
        """
        img_name = f"{i:04d}.jpg"  # TODO change image name
        f_size = size if size is not None else self.get_size(img_rsrc)

        # Check if already downloaded with correct size
        if not re_download and os.path.exists(self.manifest_dir_path / img_name):
            img = Image.open(self.manifest_dir_path / img_name)
            if self.check_size(img, img_rsrc):
                return True

        img_url = get_id(img_rsrc["service"])
        if img_url.endswith("full/full/0/default.jpg"):
            self.current_url = sanitize_url(img_url)
        else:
            self.current_url = sanitize_url(f"{img_url}/full/{f_size}/0/default.jpg")
        # TODO try with different variations sanitization of the url

        # Handle rate limiting for specific servers
        sleep = 12 if "gallica" in self.manifest_url else 0.25
        time.sleep(sleep)

        try:
            # logger.info(f"Downloading image {i} from {self.current_url}")
            with requests.get(self.current_url, stream=True) as response:
                response.raw.decode_content = True
                return self._process_image_response(response, img_name, img_rsrc, i, size)
        except Exception as e:
            logger.error(f"Failed to download image from {self.current_url} (#{i})", exception=e)
            return False

    def _process_image_response(
        self, response,
        img_name: str,
        img_rsrc: Dict[str, Any],
        i: int,
        size: Optional[str]
    ) -> bool:
        """Process the image download response."""
        try:
            img = Image.open(response.raw)
        except (UnidentifiedImageError, SyntaxError) as e:
            if size == self.get_size(img_rsrc):
                reduced_size = self.get_reduced_size(img_rsrc)
                return self.save_iiif_img(
                    img_rsrc, i, self.get_formatted_size(reduced_size)
                )
            logger.error(f"Invalid image file for image {self.current_url})", exception=e)
            return False
        except (IOError, OSError) as e:
            if size == "full":
                reduced_size = self.get_reduced_size(img_rsrc)
                return self.save_iiif_img(
                    img_rsrc, i, self.get_formatted_size(reduced_size)
                )
            logger.error(f"Truncated or corrupted image {self.current_url}", exception=e)
            return False

        try:
            return save_img(img, img_name, self.manifest_dir_path)
        except OSError as e:
            if not self.allow_truncation:
                logger.error(f"Image was truncated {self.current_url}", exception=e)
                return False

            try:
                missing_bytes = int(str(e))
                if 0 < missing_bytes < 3:
                    logger.warning(f"Image {self.current_url} truncated by {missing_bytes} bytes - saving anyway")
                    return save_img(img, img_name, self.manifest_dir_path, load_truncated=True)
            except ValueError:
                logger.error(f"Failed to process truncated image {self.current_url}", exception=e)
            return False

    @staticmethod
    def get_first_canvas(manifest_line):
        if len(manifest_line.split(" ")) != 2:
            return manifest_line, 0

        url = manifest_line.split(" ")[0]
        try:
            first_canvas = int(manifest_line.split(" ")[1])
        except (ValueError, IndexError) as e:
            logger.warning(f"[get_first_canvas] Could not retrieve canvas from {manifest_line}: {e}")
            first_canvas = 0

        return url, first_canvas

    @staticmethod
    def get_img_rsrc(iiif_img):
        try:
            img_rsrc = iiif_img["resource"]
        except KeyError:
            try:
                img_rsrc = iiif_img["body"]
            except KeyError:
                return None
        return img_rsrc

    def get_iiif_resources(self):
        manifest = self.manifest_json
        try:
            # Usually images URL are contained in the "canvases" field
            img_list = [
                canvas["images"] for canvas in manifest["sequences"][0]["canvases"]
            ]
            img_info = [self.get_img_rsrc(img) for imgs in img_list for img in imgs]
        except KeyError:
            # But sometimes in the "items" field
            try:
                img_list = [
                    item
                    for items in manifest["items"]
                    for item in items["items"][0]["items"]
                ]
                img_info = [self.get_img_rsrc(img) for img in img_list]
            except KeyError as e:
                logger.error(
                    f"[get_iiif_resources] Unable to retrieve resources from manifest {self.manifest_url}", exception=e
                )
                return []

        return img_info

    def get_size(self, img_rsrc):
        if self.max_dim is None:
            return "full"
        h, w = get_height(img_rsrc), get_width(img_rsrc)

        if h is None or w is None:
            return "full"

        if h > w:
            h = self.max_dim if h > self.max_dim else h
            return self.get_formatted_size("", str(h))
        w = self.max_dim if w > self.max_dim else w
        return self.get_formatted_size(str(w), "")

    def check_size(self, img, img_rsrc):
        """
        Checks if an already downloaded image has the correct dimensions
        """
        # TODO manage the fact that sometimes the image original full dimension is bellow max_dim
        if self.max_dim is None:
            if int(img.height) == get_height(img_rsrc):  # for full size
                return True

        if int(img.height) == self.max_dim or int(img.width) == self.max_dim:
            # if either the height or the width corresponds to max dimension
            # if it is too big, re-download again
            return True

        return False  # Download again

    def get_formatted_size(self, width="", height=""):
        if not hasattr(self, "max_dim"):
            self.max_dim = None

        if not width and not height:
            if self.max_dim is not None:
                return f",{self.max_dim}"
            return "full"

        if width and self.max_dim and int(width) > self.max_dim:
            width = f"{self.max_dim}"
        if height and self.max_dim and int(height) > self.max_dim:
            height = f"{self.max_dim}"

        return f"{width or ''},{height or ''}"

    def get_reduced_size(self, img_rsrc):
        h, w = get_height(img_rsrc), get_width(img_rsrc)
        if h is None or w is None:
            return str(self.min_dim)

        larger_side = h if h > w else w

        if larger_side < self.min_dim:
            return ""
        if larger_side > self.min_dim * 2:
            return str(int(larger_side / 2))
        return str(self.min_dim)

    def get_dir_name(self):
        return sanitize_str(self.manifest_url).replace("manifest", "").replace("json", "")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all image resources from a list of manifest urls')
    parser.add_argument('-f', '--file', nargs='?', type=str, required=True, help='File containing manifest urls')
    parser.add_argument('-max', '--max_dim', nargs='?', type=int, default=MAX_SIZE, help='Maximal size in pixel')
    parser.add_argument('-min', '--min_dim', nargs='?', type=int, default=MIN_SIZE, help='Minimal size in pixel')
    args = parser.parse_args()

    with open(args.file, mode='r') as f:
        manifests = [line.strip() for line in f if line.strip()]

    if not manifests:
        logger.error("No manifests found in the input file")
        exit(1)

    logger.info(f"Found {len(manifests)} manifests to process")

    for manifest in logger.progress(manifests, desc="Processing manifests"):
        try:
            downloader = Downloader(manifest, max_dim=args.max_dim, min_dim=args.min_dim)
            downloader.run()
        except Exception as e:
            logger.error(f"Failed to process manifest {manifest}", exception=e)
            continue
