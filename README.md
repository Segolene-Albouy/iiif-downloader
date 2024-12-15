# Download images from IIIF manifests

[![PyPI - Version](https://img.shields.io/pypi/v/iiif-download.svg)](https://pypi.org/project/iiif-download)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/iiif-download.svg)](https://pypi.org/project/iiif-download)
![Test Status](https://img.shields.io/github/actions/workflow/status/Segolene-Albouy/iiif-download/test.yml?branch=main)

This repository contains code to download images from IIIF manifests.
It takes into account limitations and data specificities from various institutions.

```bash
pip install iiif-download
```

## Basic usage

The configuration is stored in `iiif_download/config.py` and can be overriden by setting environment variables.

### Inside a script

```python
from iiif_download import IIIFDownloader, config

# Override the default configuration
config.max_size = 2500
config.img_dir = "custom/path/to/images"

# Use downloader with global config
downloader = IIIFDownloader()

# or override the global config for a specific downloader
downloader = IIIFDownloader(
    img_dir="path/to/dir"  # surcharge any global attribute
)

manifest = "https://example.org/manifest"

# Download images from a manifest inside img_dir/dir_name
downloader.download_manifest(manifest, save_dir="dir_name")
```

### Command line

```bash
# override specific variables
export IIIF_BASE_DIR=custom/path/to/images
export IIIF_MAX_SIZE=4000
# or use .env
source .env

iiif-download https://example.org/manifest
iiif-download -f test-manifests.txt
iiif-download -d custom/path/to/images
```

## Metadata extraction

```python
from iiif_download import IIIFManifest

manifest = IIIFManifest("https://example.org/manifest")
manifest.load()
lic = manifest.license
author = manifest.get_meta("author")
images = manifest.get_images()
```
