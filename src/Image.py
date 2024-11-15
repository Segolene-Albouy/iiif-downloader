import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image as PILImage
import requests

from utils import MAX_SIZE, save_img, get_height, get_width, sanitize_url
from utils.constants import MIN_SIZE
from utils.logger import logger


class IIIFImage:
    """Represents a single IIIF image with its properties and download capabilities."""

    def __init__(
        self,
        idx: int,
        img_id: str,
        resource: Dict[str, Any],
        save_dir: Path,
        max_dim: int = MAX_SIZE,
        min_dim: int = MIN_SIZE,
        allow_truncated: bool = False
    ):
        self.idx = idx
        self.url = sanitize_url(img_id.replace("full/full/0/default.jpg", ""))
        self.size = None
        self.resource = resource
        self.save_dir = save_dir
        self.max_dim = max_dim
        self.min_dim = min_dim
        self.allow_truncated = allow_truncated
        self._image: Optional[PILImage.Image] = None
        self.sleep = 12 if "gallica" in self.url else 0.25

    @property
    def height(self) -> Optional[int]:
        return get_height(self.resource)

    @property
    def width(self) -> Optional[int]:
        return get_width(self.resource)

    def sized_url(self) -> str:
        return f"{self.url}/full/{self.size}/0/default.jpg"

    def save(self, re_download: bool = False) -> bool:
        """Download and save the image."""
        img_name = f"{self.idx:04d}.jpg"

        # Check if already downloaded
        if not re_download and self.check(img_name):
            return True

        self.size = self.get_size()
        return self.download(self.sized_url(), img_name)

    def download(self, url, img_name) -> bool:
        time.sleep(self.sleep)
        with open(self.save_dir / "info.txt", "a") as f:
            f.write(f"{self.idx} - {self.sized_url()}\n")
        try:
            with requests.get(url, stream=True) as response:
                response.raw.decode_content = True
                return self.process_response(response, img_name)
        except Exception as e:
            logger.error(f"Failed to download {url}", exception=e)
            return False

    def get_size(self) -> str:
        """Calculate appropriate size for IIIF request."""
        if self.max_dim is None:
            return "full"

        if self.height is None or self.width is None:
            return "full"

        if self.height > self.width:
            h = self.max_dim if self.height > self.max_dim else self.height
            return f",{h}"
        w = self.max_dim if self.width > self.max_dim else self.width
        return f"{w},"

    def get_reduced_size(self):
        if self.height is None or self.width is None:
            return str(self.min_dim)

        larger_side = self.height if self.height > self.width else self.width

        if larger_side < self.min_dim:
            return ""
        if larger_side > self.min_dim * 2:
            return str(int(larger_side / 2))
        return str(self.min_dim)

    def check(self, filename: str) -> bool:
        """Check if image exists with correct size."""
        if not os.path.exists(self.save_dir / filename):
            return False

        img = PILImage.open(self.save_dir / filename)
        if self.max_dim is None:
            return int(img.height) == self.height
        # TODO manage the fact that sometimes the image original full dimension is bellow max_dim
        return img.height == self.max_dim or img.width == self.max_dim

    def process_response(self, response, filename: str) -> bool:
        """Process and save image response."""
        try:
            img = PILImage.open(response.raw)
            try:
                return save_img(img, filename, self.save_dir)
            except OSError as e:
                if not self.allow_truncated:
                    logger.error(f"Image was truncated {self.sized_url()}", exception=e)
                    return False

                try:
                    missing_bytes = int(str(e))
                    if 0 < missing_bytes < 3:
                        logger.warning(f"Image truncated by {missing_bytes} bytes - saving anyway")
                        return save_img(img, filename, self.save_dir, load_truncated=True)
                except ValueError:
                    pass

                logger.error(f"Failed to handle truncated image {self.sized_url()}", exception=e)
                return False

        except (PILImage.UnidentifiedImageError, SyntaxError, IOError, OSError) as e:
            if self.size in ["full", f"{self.max_dim},", f",{self.max_dim}"]:
                self.size = self.get_reduced_size()
                return self.download(self.sized_url(), filename)

            logger.error(f"Failed to process image {self.sized_url()}", exception=e)
            return False
