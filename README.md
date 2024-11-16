# Download images from IIIF manifests

This repository contains code to download images from IIIF manifests.
It takes into account limitations and data specificities various institution.

```
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python run.py -f test-manifests.txt -max <max_dimension> -min <min_dimension>
```

# Code structure

- `Manifest.py`: class to handle IIIF manifests
- `Image.py`: class to handle images
- `Downloader.py`: class to download images
