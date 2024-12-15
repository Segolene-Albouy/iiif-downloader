"""
Configuration module for iiif_download package.

This module handles all configurable parameters of the package,
providing both default values and methods to override them.
"""

import os
from asyncio import Semaphore
from pathlib import Path
from typing import Optional


class Config:
    """Global configuration for the iiif_download package."""

    def __init__(self):
        self._base_dir = Path(__file__).resolve().parent.parent.parent
        self._img_dir = self._base_dir / "img"
        self._log_dir = self._base_dir / "log"

        # Image processing settings
        self._max_size = 2500
        self._min_size = 1000
        self._max_res = 300
        self._allow_truncation = False

        # Network settings
        self._retry_attempts = 3
        self._sleep_time = {"default": 0.05, "gallica": 12}
        self._semaphore = Semaphore(5)

        # Dev settings
        self._debug = False
        self._is_logged = True
        self._save_manifest = False
        self._user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"

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
            # TODO if img_dir is absolute, do not put it inside base_dir
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

        if retries := os.getenv("IIIF_RETRY_ATTEMPTS"):
            self._retry_attempts = int(retries)

        if sleep_time := os.getenv("IIIF_SLEEP"):
            self._sleep_time = {"default": float(sleep_time), "gallica": 12}

        if debug := os.getenv("IIIF_DEBUG"):
            self._debug = debug.lower() in ("true", "1", "yes")

        if save := os.getenv("IIIF_SAVE_MANIFEST"):
            self._save_manifest = save.lower() in ("true", "1", "yes")

        # TODO add is_logged, semaphore, user_agent

    def _create_dirs(self):
        """Create necessary directories if they don't exist."""
        self._img_dir.mkdir(parents=True, exist_ok=True)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        # TODO maybe delete ?, by default the base_dir should be
        #  the current dir where the user executes python
        """Base directory for logs and images"""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, path):
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be Path or string")
        self._base_dir = Path(path)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def img_dir(self) -> Path:
        """Directory where images will be saved."""
        return self._img_dir

    @img_dir.setter
    def img_dir(self, path):
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be Path or string")
        self._img_dir = Path(path)
        self._img_dir.mkdir(parents=True, exist_ok=True)

    @property
    def log_dir(self) -> Path:
        """Directory where logs will be saved."""
        return self._log_dir

    @log_dir.setter
    def log_dir(self, path: Path):
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be Path or string")
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
        if value > self.max_size:
            raise ValueError("min_size cannot be larger than max_size")
        self._min_size = value

    @property
    def max_res(self) -> int:
        """Maximum resolution for saved images."""
        # TODO use
        return self._max_res

    @max_res.setter
    def max_res(self, value):
        """Maximum resolution for saved images."""
        if value < 0:
            raise ValueError("max_res must be positive")
        self._max_res = value

    @property
    def retry_attempts(self) -> int:
        """Number of retry attempts for failed downloads."""
        # TODO use
        return self._retry_attempts

    @retry_attempts.setter
    def retry_attempts(self, value: int):
        if value < 0:
            raise ValueError("Retry attempts must be positive")
        self._retry_attempts = value

    @property
    def sleep_time(self) -> dict:
        """Sleep time between requests for different providers."""
        return self._sleep_time.copy()

    def set_sleep_time(self, value: float, provider: str = "default") -> None:
        """
        Set sleep time for a specific provider.
        """
        if not isinstance(value, (int, float)):
            raise TypeError("Sleep time must be a number")
        if value <= 0:
            raise ValueError("Sleep time must be positive")

        self._sleep_time[provider] = float(value)

    def get_sleep_time(self, url: Optional[str] = None) -> float:
        """Get sleep time for a specific URL."""
        if url and "gallica" in url:
            return self._sleep_time["gallica"]
        return self._sleep_time["default"]

    @property
    def semaphore(self) -> Semaphore:
        return self._semaphore

    @semaphore.setter
    def semaphore(self, value: int):
        if value < 0:
            raise ValueError("Semaphore value must be positive")
        self._semaphore = Semaphore(value)

    @property
    def debug(self) -> bool:
        """Enable debug mode."""
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("Debug must be a boolean")
        self._debug = value

    @property
    def user_agent(self) -> str:
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value: str):
        if not isinstance(value, str):
            raise TypeError("User agent must be a string in the format 'Browser/V. (OS) Platform/V.'")
        self._user_agent = value

    @property
    def is_logged(self) -> bool:
        """Save logs to file."""
        return self._is_logged

    @is_logged.setter
    def is_logged(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("is_logged must be a boolean")
        self._is_logged = value

    @property
    def save_manifest(self) -> bool:
        """Enable debug mode."""
        return self._save_manifest

    @save_manifest.setter
    def save_manifest(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("Save manifest must be a boolean")
        self._save_manifest = value

    @property
    def allow_truncation(self) -> bool:
        """Allow truncation of images."""
        return self._allow_truncation

    @allow_truncation.setter
    def allow_truncation(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("Allow truncation must be a boolean")
        self._allow_truncation = value


# Global configuration instance
config = Config()
