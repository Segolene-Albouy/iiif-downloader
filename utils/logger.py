import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, Iterable, Optional, Union
from tqdm import tqdm

from utils import strip_tags
from utils.constants import LOG_PATH


def sanitize(v):
    """
    Helper function to convert non-serializable values to string representations.
    """
    if isinstance(v, (str, int, float, bool, type(None))):
        return v
    elif isinstance(v, (list, tuple)):
        return [sanitize(x) for x in v]
    elif isinstance(v, dict):
        return {str(k): sanitize(val) for k, val in v.items()}
    else:
        # For custom objects, include class name in representation
        return f"{v.__class__.__name__}({str(v)})"


def pprint(o):
    if isinstance(o, str):
        if "html" in o:
            return strip_tags(o)[:500]
        try:
            return json.dumps(json.loads(o), indent=4, sort_keys=True)
        except ValueError:
            return o
    elif isinstance(o, dict) or isinstance(o, list):
        try:
            return json.dumps(o, indent=4, sort_keys=True)
        except TypeError:
            try:
                if isinstance(o, dict):
                    sanitized = {
                        str(k): sanitize(v)
                        for k, v in o.items()
                    }
                else:
                    sanitized = [sanitize(v) for v in o]
                return json.dumps(sanitized, indent=4, sort_keys=True)
            except Exception:
                return str(o)
    return str(o)


class Logger:
    """
    Unified logger for the IIIF downloader that handles:
    - Console output with colors
    - File logging
    - Progress bars
    - Error tracking
    """

    # ANSI Color codes
    COLORS = {
        'error': '\033[91m',  # red
        'warning': '\033[93m',  # yellow
        'info': '\033[94m',  # blue
        'success': '\033[92m',  # green
        'magenta': "\033[95m",
        'cyan': "\033[96m",
        'white': "\033[97m",
        'black': '\033[90m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'end': '\033[0m'
    }

    def __init__(self, log_dir: Union[str, Path]):
        """
        Initialize the logger with a directory for log files

        Args:
            log_dir: Directory where log files will be stored
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.error_log = self.log_dir / "error.log"
        self.download_log = self.log_dir / "download_fails.log"

        # Setup logging
        self.logger = logging.getLogger("iiif-downloader")
        self.logger.setLevel(logging.INFO)

        # File handler for errors
        fh = logging.FileHandler(self.error_log)
        fh.setLevel(logging.ERROR)
        self.logger.addHandler(fh)

        # Console handler for all levels
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        self.logger.addHandler(ch)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in readable format."""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def get_color(self, color: str) -> str:
        """Get the ANSI color code for a message type."""
        return self.COLORS.get(color, '')

    def _format_message(self, msg: Any, msg_type: str = 'info') -> str:
        """Format a message with timestamp and colors."""
        color = self.get_color(msg_type)
        timestamp = self._get_timestamp()

        formatted_msg = pprint(msg)

        return f"\n\n\n{timestamp}\n{color}{self.COLORS['bold']}{formatted_msg}{self.COLORS['end']}\n\n\n"

    def error(self, msg: Any, exception: Optional[Exception] = None):
        """
        Log an error message and optionally an exception

        Args:
            msg: Message to log
            exception: Optional exception to include in log
        """
        error_msg = self._format_message(msg, 'error')

        if exception:
            error_msg += f"\n[{exception.__class__.__name__}] {str(exception)}"
            error_msg += f"\n{traceback.format_exc()}"

        self.logger.error(error_msg)

    def warning(self, msg: Any):
        """Log a warning message."""
        self.logger.warning(self._format_message(msg, 'warning'))

    def info(self, msg: Any = "🚨🚨🚨"):
        """Log an info message."""
        self.logger.info(self._format_message(msg, 'info'))

    def magic(self, msg: Any = "🪄🪄🪄"):
        self.logger.info(self._format_message(msg, 'magenta'))

    def water(self, msg: Any = "🪼🪼🪼"):
        self.logger.info(self._format_message(msg, 'cyan'))

    def white(self, msg: Any = "️🏳️🏳️️🏳️"):
        self.logger.info(self._format_message(msg, 'white'))

    def black(self, msg: Any = "️🏴️🏴🏴"):
        self.logger.info(self._format_message(msg, 'black'))

    def success(self, msg: Any):
        """Log a success message."""
        self.logger.info(self._format_message(msg, 'success'))

    @staticmethod
    def progress(iterable: Iterable, desc: str = "", total: Optional[int] = None) -> tqdm:
        """
        Create a progress bar for an iteration

        Args:
            iterable: The iterable to track
            desc: Description of the progress
            total: Total number of items (optional)

        Returns:
            tqdm: Progress bar object
        """
        return tqdm(
            iterable,
            desc=desc,
            total=total,
            unit='img',
            ncols=80,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        )

    def log_failed_download(self, img_name: str, img_url: str):
        """
        Log a failed download attempt

        Args:
            img_name: Name of the image file
            img_url: URL that failed to download
        """
        with open(self.download_log, 'a') as f:
            f.write(f"{img_name} {img_url}\n")


# Create a global logger instance
logger = Logger(LOG_PATH)
