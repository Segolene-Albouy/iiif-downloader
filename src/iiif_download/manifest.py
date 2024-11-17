from pathlib import Path
from typing import Optional, Dict, Any, List

from .image import IIIFImage
from .config import config
from .utils import sanitize_str, get_json, get_id, get_license_url, get_meta_value, mono_val
from .utils.logger import logger

LICENSE = [
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


class IIIFManifest:
    """Represents a IIIF manifest with its metadata and image list."""

    def __init__(self, url: str, img_dir: Path = None, manifest_dir_name: str = None):
        self.url = url
        self.content: Optional[Dict[str, Any]] = None
        self.manifest_dir = (Path(img_dir) if img_dir else config.img_dir) / (manifest_dir_name or self.get_dir_name())

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

        if "license" in self.content:
            lic = self.content.get("license")
            return get_license_url(mono_val(lic))

        if "metadata" in self.content:
            for label in LICENSE:
                for meta in self.content.get("metadata", []):
                    if label in str(meta.get("label", "")).lower():
                        return get_license_url(meta.get("value", ""))

                    if value := get_meta_value(meta, label):
                        return get_license_url(value)

        attribution = self.content.get("attribution")
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
                logger.error(f"Failed to extract images from manifest", exception=e)

        return resources

    def get_images(self) -> List[IIIFImage]:
        """Get all images from manifest."""
        images = []
        for i, resource in enumerate(self.get_resources()):
            images.append(IIIFImage(
                idx=i + 1,
                img_id=get_id(resource["service"]),
                resource=resource,
                save_dir=self.manifest_dir
            ))
        return images

    @staticmethod
    def get_image_resource(image_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract image resource from image data."""
        try:
            return image_data.get("resource") or image_data.get("body")
        except KeyError:
            return None

    def get_dir_name(self) -> str:
        """Generate a directory name from manifest URL."""
        return sanitize_str(self.url).replace("manifest", "").replace("json", "")
