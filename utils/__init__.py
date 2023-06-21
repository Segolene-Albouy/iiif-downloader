import json
from pathlib import Path

import requests
from PIL import Image

from utils.constants import IMG_PATH, MAX_SIZE, MAX_RES


def check_dir(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError('{} does not exist'.format(path.absolute()))
    return path


def create_dir(path):
    path = Path(path)
    # do nothing if directory already exists
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_url(string):
    return string.replace(" ", "+").replace(" ", "+")


def sanitize_str(string):
    return string.replace("/", "").replace(".", "").replace("https:", "").replace("www", "").replace(" ", "_")


def save_img(
    img,
    img_filename,
    img_path=IMG_PATH,
    error_msg="Failed to save img",
    max_dim=MAX_SIZE,
    dpi=MAX_RES,
    img_format="JPEG",
):
    # if glob.glob(img_path / img_filename):
    #     return False  # NOTE: maybe download again anyway because manifest / pdf might have changed

    try:
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail(
                (max_dim, max_dim), Image.ANTIALIAS
            )  # Image.Resampling.LANCZOS
        img.save(img_path / img_filename, format=img_format)
        return True
    except Exception as e:
        raise f"[save_img] {error_msg}:\n{e}"


def get_json(url):
    try:
        r = requests.get(url)
    except requests.exceptions.SSLError:
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
        try:
            requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += (
                "HIGH:!DH:!aNULL"
            )
        except AttributeError:
            # no pyopenssl support used / needed / available
            pass
        r = requests.get(url, verify=False)

    return json.loads(r.text)


def get_id(dic):
    if isinstance(dic, list):
        dic = dic[0]

    if isinstance(dic, dict):
        try:
            return dic["@id"]
        except KeyError:
            try:
                return dic["id"]
            except KeyError as e:
                raise f"[get_id] No id provided {e}"

    if isinstance(dic, str):
        return dic

    return None


def get_height(img_rsrc):
    try:
        img_height = img_rsrc["height"]
    except KeyError:
        return None
    return int(img_height)


def get_width(img_rsrc):
    try:
        img_width = img_rsrc["width"]
    except KeyError:
        return None
    return int(img_width)
