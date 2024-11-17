import json
import sys

import pytest
from pathlib import Path
from unittest.mock import patch
from ..iiif_download.manifest import IIIFManifest

sys.path.append(str(Path(__file__).resolve().parent.parent))
GET_JSON_PATH = 'src.iiif_download.utils.get_json'


@pytest.fixture
def manifest_files():
    """Paths to manifest test files."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return {
        "v2": fixtures_dir / "manifest_v2.json",
        "v3": fixtures_dir / "manifest_v3.json",
        "test": fixtures_dir / "manifest_test.json"
    }


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


class TestManifest:
    """Tests for IIIFManifest."""

    @pytest.mark.parametrize("version", ["v2", "v3", "test"])
    def test_image_extraction(self, version, mock_manifest, manifest_files):
        """Test image extraction from manifest."""
        manifest = mock_manifest(manifest_files[version])
        images = manifest.get_images()

        assert len(images) == 1
        image = images[0]
        assert image.idx == 1
        assert image.url == "https://example.org/iiif/image1"
        assert image.height == 2000
        assert image.width == 1500

    @pytest.mark.parametrize("version", ["v2", "v3", "test"])
    def test_metadata_extraction(self, version, mock_manifest, manifest_files):
        """Test metadata extraction."""
        manifest = mock_manifest(manifest_files[version])
        assert manifest.get_meta("author") == "Test Author"
        assert manifest.get_meta("date") == "2024"
        assert manifest.get_meta("truc") is None

    @pytest.mark.parametrize("version,expected_license", [
        ("v2", "creativecommons.org/licenses/by-nc/1.0"),
        ("v3", "creativecommons.org/licenses/by/4.0"),
        ("test", "creativecommons.org/publicdomain/mark/1.0")
    ])
    def test_license_extraction(self, version, expected_license, mock_manifest, manifest_files):
        """Test license extraction."""
        manifest = mock_manifest(manifest_files[version])
        assert expected_license in manifest.license

    @pytest.mark.parametrize("manifest_content,expected_resources", [
        ({}, []),  # Empty manifest
        ({"sequences": [{"canvases": []}]}, []),  # Missing fields
        ({"sequences": [{"canvases": [{"images": [{}]}]}]}, [])  # Malformed data
    ])
    def test_error_handling(self, manifest_content, expected_resources):
        """Test error handling for malformed manifests."""
        manifest = IIIFManifest("https://example.org/manifest")
        manifest.content = manifest_content
        assert manifest.get_resources() == expected_resources

    @pytest.mark.parametrize("manifest_content,expected_license", [
        ({}, 'No manifest loaded'),  # Empty manifest
        ({"sequences": [{"canvases": []}]}, "No license information found"),  # Missing fields
    ])
    def test_no_license(self, manifest_content, expected_license):
        """Test manifest with no license."""
        manifest = IIIFManifest("https://example.org/manifest")
        manifest.content = manifest_content
        assert expected_license in manifest.license
