"""
IIIF Downloader
==============

A Python package to download images from IIIF manifests.
"""

from .downloader import IIIFDownloader
from .manifest import IIIFManifest
from .image import IIIFImage

__version__ = "0.1.0"

__all__ = ["IIIFDownloader", "IIIFManifest", "IIIFImage"]
