from typing import List
from unittest.mock import patch, Mock

import pytest

from ..config import config
from ..image import IIIFImage
from ..manifest import IIIFManifest


class TestManifest:
    """Tests for IIIFManifest."""

    manifest_url = "https://example.org/manifest"

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

    @pytest.mark.parametrize(
        "version,expected_license",
        [
            ("v2", "creativecommons.org/licenses/by-nc/1.0"),
            ("v3", "creativecommons.org/licenses/by/4.0"),
            ("test", "creativecommons.org/publicdomain/mark/1.0"),
        ],
    )
    def test_license_extraction(self, version, expected_license, mock_manifest, manifest_files):
        """Test license extraction."""
        manifest = mock_manifest(manifest_files[version])
        assert expected_license in manifest.license

    @pytest.mark.parametrize(
        "manifest_content,expected_resources",
        [
            ({}, []),  # Empty manifest
            ({"sequences": [{"canvases": []}]}, []),  # Missing fields
            ({"sequences": [{"canvases": [{"images": [{}]}]}]}, []),  # Malformed data
        ],
    )
    def test_error_handling(self, manifest_content, expected_resources):
        """Test error handling for malformed manifests."""
        manifest = IIIFManifest("https://example.org/manifest")
        manifest.content = manifest_content
        assert manifest.get_resources() == expected_resources

    @pytest.mark.parametrize(
        "manifest_content,expected_license",
        [
            ({}, "No manifest loaded"),  # Empty manifest
            (
                {"sequences": [{"canvases": []}]},
                "No license information found",
            ),  # Missing fields
        ],
    )
    def test_no_license(self, manifest_content, expected_license):
        """Test manifest with no license."""
        manifest = IIIFManifest("https://example.org/manifest")
        manifest.content = manifest_content
        assert expected_license in manifest.license

    def MockManifest(self, images: List[IIIFImage] = [], **kwargs):
        """Create a mock IIIFManifest instance."""
        mock_manifest = Mock(spec=IIIFManifest)
        mock_manifest.url = "https://creativecommons.org/licenses/by/4.0/"
        mock_manifest.load.return_value = True
        mock_manifest.get_images.return_value = images

        for k, v in kwargs.items():
            setattr(mock_manifest, k, v)

        return mock_manifest

    def test_info_file(self, tmp_base_dir, mock_manifest, manifest_files):
        """Test that the downloader appends metadata to info.json."""
        config.img_dir = tmp_base_dir
        config.is_logged = True

        # TODO test get_images that is not empty
        manifest = mock_manifest(manifest_files["empty"])
        manifest.download()

        assert manifest.save_dir.exists()

        info_file = manifest.save_dir / "info.json"
        assert info_file.exists()

        content = info_file.read_text()
        assert self.manifest_url in content
        assert "https://creativecommons.org/licenses/by/4.0/" in content

    def test_save_dir(self, tmp_base_dir):
        """Test manifest directory creation."""
        config.base_dir = tmp_base_dir

        assert str(config.base_dir) == str(tmp_base_dir)

        # only base_dir defined
        manifest = IIIFManifest(self.manifest_url)
        assert str(manifest.save_dir) == str(config.img_dir)

        # only base_dir defined, img_dir and save_dir set to None
        manifest = IIIFManifest(self.manifest_url, img_dir=None, save_dir=None)
        assert str(manifest.save_dir) == str(tmp_base_dir)

        # definition of img_dir relative to base_dir
        manifest = IIIFManifest(self.manifest_url, img_dir="images", save_dir=None)
        assert str(manifest.config.img_dir) == str(tmp_base_dir / "images")
        assert str(manifest.save_dir) == str(tmp_base_dir / "images")

        # definition of img_dir and save_dir relative to base_dir
        manifest = IIIFManifest(self.manifest_url, img_dir="images", save_dir="manifests")
        assert str(manifest.save_dir) == str(tmp_base_dir / "images" / "manifests")

        abs_path = "/private/tmp/abs/path"
        # definition of absolute path to img_dir
        manifest = IIIFManifest(self.manifest_url, img_dir=abs_path)
        assert str(manifest.save_dir) == abs_path

        # definition of absolute path to save_dir
        manifest = IIIFManifest(self.manifest_url, img_dir="path/to/ignore", save_dir=abs_path)
        assert str(manifest.save_dir) == abs_path


# def test_image_download_count(self, manifest_files, mock_manifest):
#     """Test that all images from manifest are downloaded."""
#     downloader = IIIFDownloader(img_dir=TEMP_DIR)
#
#     with patch('src.iiif_download.manifest.IIIFManifest') as mock:
#         # Use our mock manifest with one image
#         manifest = mock_manifest(manifest_files["v2"], TEMP_DIR)
#         mock.return_value = manifest
#
#         # Mock image save to always succeed
#         for image in manifest.get_images():
#             image.save = Mock(return_value=True)
#
#         downloader.download_manifest("https://example.org/manifest")
#
#         # Verify number of downloads matches manifest
#         downloaded_images = list((TEMP_DIR / "example.org").glob("*.jpg"))
#         assert len(downloaded_images) == len(manifest.get_images())
#
# def test_failed_download_logging(self, manifest_files, mock_manifest):
#     """Test that failed downloads are logged in info.txt."""
#     downloader = IIIFDownloader(img_dir=TEMP_DIR)
#
#     with patch('src.iiif_download.manifest.IIIFManifest') as mock:
#         manifest = mock_manifest(manifest_files["v2"])
#         mock.return_value = manifest
#
#         # Make image save fail
#         for image in manifest.get_images():
#             image.save = Mock(return_value=False)
#             image.sized_url = Mock(return_value="https://example.org/iiif/image1/full/2000,/0/default.jpg")
#
#         downloader.download_manifest("https://example.org/manifest")
#
#         # Check info.txt for failed download entry
#         info_file = TEMP_DIR / "example.org" / "info.txt"
#         assert info_file.exists()
#         content = info_file.read_text()
#         assert "Failed to download" in content
#         assert "https://example.org/iiif/image1/full/2000,/0/default.jpg" in content

# def test_info_file_with_images(self):
#     """Test manifest download with images."""
#     downloader = IIIFDownloader(img_dir=TEMP_DIR)
#     manifest_url = "https://example.org/manifest"
#     save_dir = TEMP_DIR / "example.org"
#     manifest_license = "http://creativecommons.org/licenses/by/4.0/"
#
#     # Create mock images
#     mock_image1 = Mock()
#     mock_image1.idx = 1
#     mock_image1.save.return_value = True
#     mock_image1.sized_url.return_value = "https://example.org/image1.jpg"
#
#     mock_image2 = Mock()
#     mock_image2.idx = 2
#     mock_image2.save.return_value = False
#     mock_image2.sized_url.return_value = "https://example.org/image2.jpg"
#
#     # Create mock manifest
#     mock_manifest = Mock(spec=IIIFManifest)
#     mock_manifest.load.return_value = True
#     mock_manifest.get_images.return_value = [mock_image1, mock_image2]
#     mock_manifest.save_dir = save_dir
#     mock_manifest.license = manifest_license
#     mock_manifest.url = manifest_url
#
#     # Patch both the logger and IIIFManifest
#     with patch('src.iiif_download.downloader.IIIFManifest', return_value=mock_manifest), \
#             patch('src.iiif_download.downloader.logger'):
#         result = downloader.download_manifest(manifest_url)
#
#         # Verify the manifest was processed correctly
#         assert result is mock_manifest
#         assert mock_manifest.load.called
#         assert mock_manifest.get_images.called
#
#         # Verify both images were attempted
#         mock_image1.save.assert_called_once()
#         mock_image2.save.assert_called_once()
#
#         # Check info file contents
#         info_file = mock_manifest.save_dir / "info.txt"
#         content = info_file.read_text()
#         assert manifest_url in content
#         assert manifest_license in content
#         assert "image2.jpg" in content  # Failed image should be logged
