import os
import pytest
from pathlib import Path
from ...iiif_download.config import Config


def test_config_attribute_types():
    """Test that Config attributes are defined with correct types and constraints"""
    config = Config()

    # Test numeric attributes
    assert isinstance(config.max_size, int)
    assert isinstance(config.min_size, int)
    assert isinstance(config.max_res, int)
    assert isinstance(config.retry_attempts, int)

    # Test that numeric values are positive
    assert config.max_size > 0, "max_size should be positive"
    assert config.min_size > 0, "min_size should be positive"
    assert config.max_res > 0, "max_res should be positive"
    assert config.retry_attempts > 0, "retry_attempts should be positive"

    # Test boolean attributes
    assert isinstance(config.debug, bool)
    assert isinstance(config.allow_truncation, bool)

    # Test sleep time dictionary
    assert isinstance(config.sleep_time, dict)
    assert "default" in config.sleep_time
    assert "gallica" in config.sleep_time
    assert isinstance(config.sleep_time["default"], (int, float))
    assert isinstance(config.sleep_time["gallica"], (int, float))
    assert config.sleep_time["default"] > 0
    assert config.sleep_time["gallica"] > 0

    # Test path attributes
    assert isinstance(config.img_dir, Path)
    assert isinstance(config.log_dir, Path)

    with pytest.raises(ValueError):
        config.max_size = -100

    with pytest.raises(ValueError):
        config.min_size = -50


def test_config_value_constraints():
    """Test that Config values respect their constraints"""
    config = Config()

    # Test setting invalid values
    with pytest.raises(ValueError, match="max_size must be positive"):
        config.max_size = -100

    with pytest.raises(ValueError, match="min_size must be positive"):
        config.min_size = -50

    # Test that min_size cannot be larger than max_size
    config.max_size = 1000
    config.min_size = 500  # Should work

    with pytest.raises(ValueError, match="min_size cannot be larger than max_size"):
        config.min_size = 1500

    # Test path setters with invalid values
    with pytest.raises(TypeError, match="path must be Path or string"):
        config.img_dir = 123

    with pytest.raises(TypeError, match="path must be Path or string"):
        config.log_dir = 123

    # Test sleep time validation
    with pytest.raises(ValueError, match="Sleep time must be positive"):
        config.set_sleep_time(-1, "default")

    with pytest.raises(TypeError, match="Sleep time must be a number"):
        config.set_sleep_time("invalid")


def test_config_env_override():
    """Test that environment variables properly override default config values"""
    # Setup environment variables
    os.environ["IIIF_MAX_SIZE"] = "3000"
    os.environ["IIIF_MIN_SIZE"] = "1500"
    os.environ["IIIF_DEBUG"] = "true"

    config = Config()

    # Test overridden values
    assert config.max_size == 3000
    assert config.min_size == 1500
    assert config.debug is True

    # Cleanup environment
    del os.environ["IIIF_MAX_SIZE"]
    del os.environ["IIIF_MIN_SIZE"]
    del os.environ["IIIF_DEBUG"]


def test_config_directory_creation():
    """Test that config creates necessary directories"""
    test_base = Path("/tmp/iiif_test")
    os.environ["IIIF_BASE_DIR"] = str(test_base)

    config = Config()

    # Test that directories were created
    assert config.img_dir.exists()
    assert config.log_dir.exists()

    # Cleanup
    import shutil

    shutil.rmtree(test_base)
    del os.environ["IIIF_BASE_DIR"]
