"""
Configuration module for iiif_download package.

This module handles all configurable parameters of the package,
providing both default values and methods to override them.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Global configuration for the iiif_download package."""

    def __init__(self):
        # Default paths relative to user's home directory
        self._base_dir = Path(__file__).resolve().parent.parent.parent
        # self._base_dir = Path.home() / ".iiif_download"
        self._img_dir = self._base_dir / "img"
        self._log_dir = self._base_dir / "log"

        # Image processing settings
        self._max_size = 2500
        self._min_size = 1000
        self._max_res = 300
        self._allow_truncation = False

        # Network settings
        self._timeout = 30
        self._retry_attempts = 3
        self._sleep_time = {
            "default": 0.25,
            "gallica": 12
        }

        # Dev settings
        self._debug = False

        # Initialize from environment variables if present
        self._load_from_env()

        # Create directories if they don't exist
        self._create_dirs()

    def _load_from_env(self):
        """Load configuration from environment variables."""
        if path := os.getenv("IIIF_BASE_DIR"):
            self._base_dir = Path(path)
            self._img_dir = self._base_dir / "img"
            self._log_dir = self._base_dir / "log"

        if dir_name := os.getenv("IIIF_IMG_DIR"):
            self._img_dir = self._base_dir / dir_name

        if dir_name := os.getenv("IIIF_LOG_DIR"):
            self._log_dir = self._base_dir / dir_name

        if size := os.getenv("IIIF_MAX_SIZE"):
            self._max_size = int(size)

        if size := os.getenv("IIIF_MIN_SIZE"):
            self._min_size = int(size)

        if res := os.getenv("IIIF_MAX_RESOLUTION"):
            self._max_res = int(res)

        if truncation := os.getenv("IIIF_ALLOW_TRUNCATION"):
            self._allow_truncation = truncation.lower() in ("true", "1", "yes")

        if timeout := os.getenv("IIIF_TIMEOUT"):
            self._timeout = int(timeout)

        if retries := os.getenv("IIIF_RETRY_ATTEMPTS"):
            self._retry_attempts = int(retries)

        if sleep_time := os.getenv("IIIF_SLEEP"):
            self._sleep_time = {
                "default": float(sleep_time),
                "gallica": 12
            }

        if debug := os.getenv("IIIF_DEBUG"):
            self._debug = debug.lower() in ("true", "1", "yes")

    def _create_dirs(self):
        """Create necessary directories if they don't exist."""
        self._img_dir.mkdir(parents=True, exist_ok=True)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def img_dir(self) -> Path:
        """Directory where images will be saved."""
        return self._img_dir

    @img_dir.setter
    def img_dir(self, path: Path):
        self._img_dir = Path(path)
        self._img_dir.mkdir(parents=True, exist_ok=True)

    @property
    def log_dir(self) -> Path:
        """Directory where logs will be saved."""
        return self._log_dir

    @log_dir.setter
    def log_dir(self, path: Path):
        self._log_dir = Path(path)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def max_size(self) -> int:
        """Maximum size for image dimensions."""
        return self._max_size

    @max_size.setter
    def max_size(self, value: int):
        if value < 0:
            raise ValueError("max_size must be positive")
        self._max_size = value

    @property
    def min_size(self) -> int:
        """Minimum size for image dimensions."""
        return self._min_size

    @min_size.setter
    def min_size(self, value: int):
        if value < 0:
            raise ValueError("min_size must be positive")
        self._min_size = value

    @property
    def max_res(self) -> int:
        """Maximum resolution for saved images."""
        return self._max_res

    @property
    def timeout(self) -> int:
        """Timeout for network requests."""
        return self._timeout

    @property
    def retry_attempts(self) -> int:
        """Number of retry attempts for failed downloads."""
        return self._retry_attempts

    @property
    def sleep_time(self) -> dict:
        """Sleep time between requests for different providers."""
        return self._sleep_time.copy()

    def get_sleep_time(self, url: Optional[str] = None) -> float:
        """Get sleep time for a specific URL."""
        if url and "gallica" in url:
            return self._sleep_time["gallica"]
        return self._sleep_time["default"]

    @property
    def debug(self) -> bool:
        """Enable debug mode."""
        return self._debug

    @property
    def allow_truncation(self) -> bool:
        """Allow truncation of images."""
        return self._allow_truncation


# Global configuration instance
config = Config()
