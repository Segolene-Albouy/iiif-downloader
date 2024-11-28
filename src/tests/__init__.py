import json
import sys
import pytest
from pathlib import Path

from ..iiif_download import IIIFManifest, IIIFImage

sys.path.append(str(Path(__file__).resolve().parent.parent))

TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"


@pytest.fixture
def manifest_files():
    """Fixture providing paths to test manifest files."""
    return {
        "v2": FIXTURES_DIR / "manifest_v2.json",
        "v3": FIXTURES_DIR / "manifest_v3.json",
        "test": FIXTURES_DIR / "manifest_test.json"
    }


def temp_download_dir():
    download_dir = TEST_DIR / "temp"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


TEMP_DIR = temp_download_dir()


@pytest.fixture
def mock_manifest():
    """Factory fixture to create a mock IIIFManifest."""
    def _create_mock(json_file):
        with open(json_file) as f:
            manifest_content = json.load(f)
        manifest = IIIFManifest("https://example.org/manifest")
        manifest.content = manifest_content
        return manifest
    return _create_mock


# @pytest.fixture
# def mock_image():
#     """Factory fixture to create a mock IIIFManifest."""
#     def _create_mock(img_id="https://example.org/iiif/image1/full/full/0/default.jpg"):
#         image = IIIFImage(
#             idx=1,
#             img_id=img_id,
#             resource={"height": 2000, "width": 1500},
#             save_dir=temp_download_dir()
#         )
#         return image
#     return _create_mock
