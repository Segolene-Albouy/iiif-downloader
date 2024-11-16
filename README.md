# Download images from IIIF manifests

This repository contains code to download images from IIIF manifests.
It takes into account limitations and data specificities various institution.

## Basic usage

### Inside a project

```python
from iiif_download.downloader import IIIFDownloader 
from iiif_download.config import config 

# Override the default configuration
config.max_size = 2500
config.img_dir = "custom/path/to/images"

# Use downloader with global config
downloader = IIIFDownloader()

# or override the global config for a specific downloader
downloader = IIIFDownloader(
    max_dim=2000,  # surcharge config.max_size
    img_path="path/to/dir"  # surcharge config.img_dir
)

manifest = "https://bvmm.irht.cnrs.fr/iiif/24971/manifest"

# Download images from a manifest inside img_path/dir_name
downloader.download_manifest(manifest, save_dir="dir_name")
```

### Command line

```bash
# override specific variables
export IIIF_BASE_DIR=custom/path/to/images
export IIIF_MAX_SIZE=4000
# or use .env 
source .env

venv/bin/python run.py -f test-manifests.txt
```

## Configuration

The configuration is stored in `iiif_download/config.py` and can be overriden by setting environment variables.

