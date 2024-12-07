"""
IIIF Downloader
==============

A Python package to download images from IIIF manifests.
"""

from .downloader import IIIFDownloader
from .image import IIIFImage
from .manifest import IIIFManifest

__version__ = "0.1.2"

__all__ = ["IIIFDownloader", "IIIFManifest", "IIIFImage", "config"]
