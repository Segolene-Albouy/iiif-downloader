from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import config
from .image import IIIFImage
from .utils import (
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

    def __init__(self, url: str, manifest_dir_name: Optional[Union[Path, str]] = None):
        self.url = url
        self.content: Optional[Dict[str, Any]] = None
        self.manifest_dir: Path = self._manifest_dir(manifest_dir_name)

    @staticmethod
    def _manifest_dir(manifest_dir_name: Optional[Union[Path, str]] = None) -> Path:
        if manifest_dir_name:
            manifest_dir_name = Path(manifest_dir_name)
            return (
                manifest_dir_name if manifest_dir_name.is_absolute() else config.img_dir / manifest_dir_name
            )
        return config.img_dir

    @property
    def uid(self) -> str:
        """Generate a directory name from manifest URL."""
        return sanitize_str(self.url).replace("manifest", "").replace("json", "")

    def load(self) -> bool:
        """Load manifest content from URL."""
        try:
            self.content = get_json(self.url)
            if config.save_manifest:
                with open(self.manifest_dir / "manifest.json", "w") as f:
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
                    save_dir=self.manifest_dir,
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
