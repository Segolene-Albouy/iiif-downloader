import json
import shutil

import pytest
from pathlib import Path

from ..manifest import IIIFManifest

TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"


@pytest.fixture
def manifest_files():
    """Fixture providing paths to test manifest files."""
    return {
        "v2": FIXTURES_DIR / "manifest_v2.json",
        "v3": FIXTURES_DIR / "manifest_v3.json",
        "test": FIXTURES_DIR / "manifest_test.json",
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


@pytest.fixture
def temp_download_dir():
    """Fixture providing a temporary download directory that's cleaned up after test."""
    download_dir = Path(__file__).parent / "temp"
    download_dir.mkdir(parents=True, exist_ok=True)
    yield download_dir
    # Clean up after test
    if download_dir.exists():
        shutil.rmtree(download_dir)
