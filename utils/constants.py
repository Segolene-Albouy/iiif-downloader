from pathlib import Path

# absolute path to iiif-downloader
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "log"
IMG_PATH = BASE_DIR / "img"

MAX_SIZE = 2500
MAX_RES = 300
MIN_SIZE = 1000
