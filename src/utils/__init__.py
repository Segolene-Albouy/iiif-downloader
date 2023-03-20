from functools import wraps
from pathlib import Path

def check_dir(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError('{} does not exist'.format(path.absolute()))
    return path


def create_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_files_from_dir(dir_path, valid_extensions=None, recursive=False, sort=False):
    path = coerce_to_path_and_check_exist(dir_path)
    if recursive:
        files = [f.absolute() for f in path.glob('**/*') if f.is_file()]
    else:
        files = [f.absolute() for f in path.glob('*') if f.is_file()]

    if valid_extensions is not None:
        valid_extensions = [valid_extensions] if isinstance(valid_extensions, str) else valid_extensions
        valid_extensions = ['.{}'.format(ext) if not ext.startswith('.') else ext for ext in valid_extensions]
        files = list(filter(lambda f: f.suffix in valid_extensions, files))

    return sorted(files) if sort else files

