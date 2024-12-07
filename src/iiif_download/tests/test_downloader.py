from unittest.mock import Mock, patch

from ...iiif_download.downloader import IIIFDownloader, IIIFManifest


class TestDownloader:
    """Test suite for IIIFDownloader class."""

    # @pytest.mark.parametrize("version", ["v2", "v3", "test"])
    def test_info_file(self, temp_download_dir):
        """Test that the downloader appends metadata to info.txt."""
        downloader = IIIFDownloader(img_dir=temp_download_dir)
        manifest_url = "https://example.org/manifest"
        manifest_dir = temp_download_dir / "test_downloaded"
        manifest_license = "http://creativecommons.org/licenses/by/4.0/"

        mock_manifest = Mock(spec=IIIFManifest)
        mock_manifest.load.return_value = True
        # TODO test get_images that is not empty
        mock_manifest.get_images.return_value = []
        mock_manifest.manifest_dir = manifest_dir
        mock_manifest.license = manifest_license
        mock_manifest.url = manifest_url

        # Make IIIFManifest return a mock manifest
        with patch("src.iiif_download.downloader.IIIFManifest", return_value=mock_manifest):
            result = downloader.download_manifest(manifest_url)
            assert result is mock_manifest
            assert mock_manifest.load.called
            assert mock_manifest.manifest_dir.exists()

            info_file = mock_manifest.manifest_dir / "info.txt"
            assert info_file.exists()

            content = info_file.read_text()
            assert manifest_url in content
            assert manifest_license in content

            # manifest = mock_manifest(manifest_files[version])
            # mock.return_value = manifest

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
#     manifest_dir = TEMP_DIR / "example.org"
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
#     mock_manifest.manifest_dir = manifest_dir
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
#         info_file = mock_manifest.manifest_dir / "info.txt"
#         content = info_file.read_text()
#         assert manifest_url in content
#         assert manifest_license in content
#         assert "image2.jpg" in content  # Failed image should be logged
