from pathlib import Path
from typing import Optional, Dict, Any, List

from src.Image import IIIFImage
from utils import IMG_PATH, sanitize_str, get_json, get_id
from utils.logger import logger


class IIIFManifest:
    """Represents a IIIF manifest with its metadata and image list."""

    def __init__(self, url: str, img_dir: Path = IMG_PATH, manifest_dir_name: str = None):
        self.url = url
        self.content: Optional[Dict[str, Any]] = None
        self.manifest_dir = img_dir / (manifest_dir_name or self._get_dir_name())

    def load(self) -> bool:
        """Load manifest content from URL."""
        try:
            self.content = get_json(self.url)
            return bool(self.content)
        except Exception as e:
            logger.error(f"Failed to load manifest from {self.url}", exception=e)
            return False

    @property
    def license(self) -> str:
        """Get license information from manifest."""
        if not self.content:
            return "No manifest loaded"

        if "license" in self.content:
            return self.content["license"]

        if "metadata" in self.content:
            for item in self.content.get("metadata", []):
                for label in ["license", "rights", "copyright"]:
                    if label in str(item.get("label", "")).lower():
                        return item.get("value", "")

        return self.content.get("attribution", "No license information found")

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
                    if resource := self._get_image_resource(image):
                        resources.append(resource)
        except KeyError:
            try:
                # Try items path
                items = self.content["items"]
                for item in items:
                    for sub_item in item["items"][0]["items"]:
                        if resource := self._get_image_resource(sub_item):
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
    def _get_image_resource(image_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract image resource from image data."""
        try:
            return image_data.get("resource") or image_data.get("body")
        except KeyError:
            return None

    def _get_dir_name(self) -> str:
        """Generate a directory name from manifest URL."""
        return sanitize_str(self.url).replace("manifest", "").replace("json", "")
