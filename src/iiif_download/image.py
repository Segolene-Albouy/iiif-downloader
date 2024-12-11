import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image as PILgrimage

from .config import config
from .utils import get_size, get_url_response, sanitize_url, save_img
from .utils.logger import logger


class IIIFImage:
    """Represents a single IIIF image with its properties and download capabilities."""

    def __init__(
        self,
        idx: int,
        img_id: str,
        resource: Dict[str, Any],
        save_dir: Path,
        max_dim: Optional[int] = None,
        min_dim: Optional[int] = None,
    ):
        self.idx = idx
        self.url = sanitize_url(img_id.replace("full/full/0/default.jpg", ""))

        self.resource = resource
        self.img_name = f"{self.idx:04d}.jpg"
        self.save_dir = save_dir

        # Use provided dimensions or fall back to config values
        self.max_dim = max_dim if max_dim is not None else config.max_size
        self.min_dim = min_dim if min_dim is not None else config.min_size
        self.size = None
        self.height = self.get_height()
        self.width = self.get_width()

        self.allow_truncation = config.allow_truncation
        self.sleep = config.get_sleep_time(self.url)

    def get_height(self) -> Optional[int]:
        return get_size(self.resource, "height")

    def get_width(self) -> Optional[int]:
        return get_size(self.resource, "width")

    def sized_url(self) -> str:
        return f"{self.url}/full/{self.size}/0/default.jpg"

    def save(self, re_download: bool = False) -> bool:
        """Download and save the image."""
        # Check if already downloaded
        if not re_download:
            if self.check():
                return True

        self.size = self.get_max_size()
        return self.download()

    def download(self) -> bool:
        url = self.sized_url()
        time.sleep(self.sleep)
        with open(self.save_dir / "info.txt", "a") as f:
            f.write(f"{self.idx} {url}\n")

        try:
            with get_url_response(url) as response:
                response.raw.decode_content = True
                return self.process_response(response)
        except Exception as e:
            logger.error(f"Failed to download {url}", exception=e)
            return False

    def get_max_size(self) -> str:
        if self.max_dim is None:
            return "full"

        if self.height is None or self.width is None:
            return f"{self.max_dim},"

        if self.height > self.width:
            h = self.max_dim if self.height > self.max_dim else self.height
            return f",{h}"
        w = self.max_dim if self.width > self.max_dim else self.width
        return f"{w},"

    def get_min_size(self):
        if not (self.min_dim or self.height or self.width):
            return "full"

        if self.min_dim and not (self.height or self.width):
            return f"{self.min_dim},"

        if not self.min_dim:
            if self.height and self.width:
                larger = max(self.height, self.width, default=0)
                return f"{larger // 2}," if self.width >= self.height else f",{larger // 2}"
            return f"{self.width // 2}," if self.width else f",{self.height // 2}"

        h = self.height
        w = self.width
        min_dim = self.min_dim

        if h > w:
            h = h // 2 if h > min_dim * 2 else (h if h < min_dim else min_dim)
            return f",{h}"

        w = w // 2 if w > min_dim * 2 else (w if w < min_dim else min_dim)
        return f"{w},"

    def check(self) -> bool:
        """
        Check if the image is already downloaded and has the correct dimensions.
        Returns:
            True if the image exists and has the correct dimensions, False otherwise
        """
        img_path = self.save_dir / self.img_name

        if not os.path.exists(img_path):
            return False

        img = PILgrimage.open(img_path)
        img_height, img_width = img.height, img.width

        if self.max_dim is None:
            return (self.height is None or img_height == self.height) and (
                self.width is None or img_width == self.width
            )

        if max(img_height, img_width) > self.max_dim:
            return False

        return self.min_dim is None or min(img_height, img_width) >= self.min_dim

    def process_response(self, response) -> bool:
        """Process and save image response."""
        if "image" not in response.headers.get("Content-Type", ""):
            logger.warning(
                f"Incorrect MIME type ({response.headers.get('Content-Type', '')}) for {self.sized_url()}"
            )
            try:
                with open(self.save_dir / f"{self.img_name}.txt", "w") as f:
                    f.write(response.text)
            except Exception as e:
                logger.error(
                    f"Failed to save response content for {self.sized_url()}",
                    exception=e,
                )

        try:
            img = PILgrimage.open(BytesIO(response.content))
            try:
                return save_img(img, self.img_name, self.save_dir)
            except OSError as e:
                if not self.allow_truncation:
                    self.download_fail(f"⛔️ Image was truncated {self.sized_url()}", e)
                    return False

                try:
                    missing_bytes = int(str(e))
                    if 0 < missing_bytes < 3:
                        logger.warning(f"Image truncated by {missing_bytes} bytes - saving anyway")
                        return save_img(img, self.img_name, self.save_dir, load_truncated=True)
                except ValueError:
                    pass

                self.download_fail(f"⛔️ Failed to handle truncated image {self.sized_url()}", e)
                return False

        except (PILgrimage.UnidentifiedImageError, SyntaxError, IOError, OSError) as e:
            if self.size in ["full", f"{self.max_dim},", f",{self.max_dim}"]:
                self.size = self.get_min_size()
                return self.download()

            self.download_fail(f"⛔️ Failed to process image {self.sized_url()}", e)
            return False

    def download_fail(self, msg: Optional[str] = None, exc: Optional[Exception] = None) -> None:
        if not msg:
            msg = f"⛔️ Failed to download {self.idx} {self.sized_url()}"

        # Log to info.txt error message
        with open(self.save_dir / "info.txt", "a") as f:
            f.write(f"\n{msg}\n")
            if exc:
                f.write(f"\n{logger.format_exception(exc)}\n\n\n")

        # Log to console the error
        logger.error(msg, exception=exc)

        # Append to failed downloads the image
        logger.log_failed_download(self.save_dir / self.img_name, self.sized_url())
