import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote

from .config import Config, config
from .image import IIIFImage
from .utils import (
    create_dir,
    get_id,
    get_json,
    get_license_url,
    get_meta_value,
    mono_val,
    sanitize_str,
)
from .utils.logger import logger

LICENSE = [
    "license",
    "licence",
    "lizenz",
    "rights",
    "droits",
    "access",
    "copyright",
    "rechteinformationen",
    "conditions",
]


class IIIFManifest:
    """Represents a IIIF manifest with its metadata and image list."""

    def __init__(
        self, url: str, save_dir: Optional[Union[Path, str]] = None, conf: Config = config, **kwargs
    ):
        self.config = conf

        if kwargs:
            self.config = conf.copy()
            for key, value in kwargs.items():
                # override any config value
                setattr(self.config, key, value)

        self.url = unquote(url)
        self.content: Optional[Dict[str, Any]] = None
        self._save_dir: Path = self.config.set_path(save_dir, self.config.img_dir)
        self._manifest_info: Dict = {}

    @property
    def save_dir(self) -> Path:
        """Directory where images will be saved."""
        return self._save_dir

    @save_dir.setter
    def save_dir(self, path):
        self._save_dir = self.config.set_path(path, self.config.img_dir)

    @property
    def uid(self) -> str:
        """Generate a directory name from manifest URL."""
        return sanitize_str(self.url).replace("manifest", "").replace("json", "")

    def load(self, reload=False) -> bool:
        """Load manifest content from URL."""
        if bool(self.content) and not reload:
            return True

        try:
            self.content = get_json(self.url)
            if self.config.save_manifest:
                with open(self.save_dir / "manifest.json", "w") as f:
                    f.write(str(self.content))
            return bool(self.content)
        except Exception as e:
            logger.error(f"Failed to load manifest from {self.url}", exception=e)
            return False

    def get_meta(self, label: str) -> Optional[str]:
        """Get value from manifest metadata"""
        if not self.content:
            return None

        if "metadata" not in self.content:
            return None

        for meta in self.content.get("metadata", []):
            if value := get_meta_value(meta, label):
                return value

        return None

    @property
    def license(self) -> str:
        """Get license information from manifest."""
        if not self.content:
            return "No manifest loaded"

        for label in ["license", "rights"]:
            if label in self.content:
                lic = self.content.get(label)
                return get_license_url(mono_val(lic))

        if "metadata" in self.content:
            for label in LICENSE:
                for meta in self.content.get("metadata", []):
                    if label in str(meta.get("label", "")).lower():
                        return get_license_url(meta.get("value", ""))

                    if value := get_meta_value(meta, label):
                        return get_license_url(value)

        attribution = self.content.get("attribution", "")
        return get_license_url(mono_val(attribution))

    def get_resources(self) -> List:
        """Extract all image resources from manifest."""
        resources = []
        if not self.content:
            return resources

        try:
            # Try sequences/canvases path
            sequences = self.content["sequences"]
            if len(sequences) < 1:
                return resources
            canvases = self.content["sequences"][0]["canvases"]
            for canvas in canvases:
                for image in canvas["images"]:
                    if resource := self.get_image_resource(image):
                        resources.append(resource)
        except KeyError:
            try:
                # Try items path
                items = self.content["items"]
                for item in items:
                    for sub_item in item["items"][0]["items"]:
                        if resource := self.get_image_resource(sub_item):
                            resources.append(resource)
            except KeyError as e:
                logger.error("Failed to extract images from manifest", exception=e)

        return resources

    def get_images(self) -> List[IIIFImage]:
        """Get all images from manifest."""
        images = []
        for i, resource in enumerate(self.get_resources()):
            images.append(
                IIIFImage(
                    idx=i + 1,
                    img_id=get_id(resource["service"]),
                    resource=resource,
                    save_dir=self.save_dir,
                )
            )
        return images

    @staticmethod
    def get_image_resource(image_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract image resource from image data."""
        try:
            return image_data.get("resource") or image_data.get("body")
        except KeyError:
            return None

    def save_log(self):
        if self.config.is_logged:
            logger.add_to_json(self.save_dir / "info.json", self._manifest_info)

    def download(self, save_dir: Optional[Union[Path, str]] = None) -> Union[bool, "IIIFManifest"]:
        if save_dir:
            self.save_dir = save_dir
        if not self.save_dir.exists():
            create_dir(self.save_dir)

        async def _async_download_manifest():
            if self.config.is_logged:
                self._manifest_info = {"url": self.url, "license": "", "images": {}}

            if not self.load():
                logger.warning(f"Unable to load json content of {self.url}")
                self.save_log()
                return self

            if self.config.is_logged:
                self._manifest_info["license"] = self.license

            images = self.get_images()
            if not images:
                logger.warning(f"No images found in manifest {self.url}")
                self.save_log()
                return self

            logger.info(f"Downloading {len(images)} images from {self.url} inside {self.save_dir}")
            for i, image in enumerate(logger.progress(images, desc="Downloading..."), start=1):
                if self.config.debug and i > 6:
                    break

                success = await image.save()
                if not success:
                    logger.error(f"Failed to download image #{image.idx} ({image.sized_url()})")
                    continue

                if self.config.is_logged:
                    self._manifest_info["images"][image.img_name] = image.sized_url()

            self.save_log()
            return self

        return asyncio.run(_async_download_manifest())
