import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageFile

from utils.constants import IMG_PATH, MAX_SIZE, MAX_RES


def check_dir(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'{path.absolute()} does not exist')
    return path


def create_dir(path):
    path = Path(path)
    # do nothing if directory already exists
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_url(url: str, safe: str = "/:=?&#") -> str:
    # try:
    #     return quote(url, safe=safe)
    # except Exception:
    #     return url.strip().replace(" ", "%20")
    return url.replace(" ", "+").replace(" ", "+")


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
    load_truncated=False
):
    # if glob.glob(img_path / img_filename):
    #     return False  # NOTE: maybe download again anyway because manifest / pdf might have changed

    # truncated files are downloaded and missing bytes are replaced by a gray area
    ImageFile.LOAD_TRUNCATED_IMAGES = load_truncated

    try:
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail(
                (max_dim, max_dim), Image.Resampling.LANCZOS
            )  # Image.Resampling.LANCZOS
        img.save(img_path / img_filename, format=img_format)
        return True
    except OSError as e:
        error = f"{e}"
        if "image file is truncated" in error:
            missing_bytes = error[25:].split(" ")[0]
            raise OSError(missing_bytes)

        raise OSError(f"[save_img] {error_msg}:\n{e}")
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
    """Get ID from a dictionary, handling different ID formats"""
    if isinstance(dic, list):
        dic = dic[0]

    if isinstance(dic, dict):
        try:
            return dic["@id"]
        except KeyError:
            try:
                return dic["id"]
            except KeyError as e:
                raise ValueError(f"[get_id] No id provided: {e}")

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


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def handle_entityref(self, name):
        self.fed.append("&%s;" % name)

    def handle_charref(self, name):
        self.fed.append("&#%s;" % name)

    def get_data(self):
        return "".join(self.fed)


def _strip_once(value):
    """
    Internal tag stripping utility used by strip_tags.
    """
    s = MLStripper()
    s.feed(value)
    s.close()
    return s.get_data()


def strip_tags(value):
    """Return the given HTML with all tags stripped."""
    value = str(value)
    while "<" in value and ">" in value:
        new_value = _strip_once(value)
        if value.count("<") == new_value.count("<"):
            # _strip_once wasn't able to detect more tags.
            break
        value = new_value
    return value


def substrs_in_str(string, substrings):
    for substr in substrings:
        if substr in string:
            return True
    return False


def get_license_url(lic):
    # TODO improve
    validator = URLValidator()
    try:
        validator(lic)
    except ValidationError as e:
        lic = normalize_str(lic).replace(" ", "")
        version = get_version_nb(lic)
        if substrs_in_str(lic, ["publicdomain", "cc0", "pdm"]):
            return "https://creativecommons.org/publicdomain/mark/1.0/"
        if substrs_in_str(lic, ["byncsa", "noncommercialsharealike"]):
            return f"https://creativecommons.org/licenses/by-nc-sa/{version}/"
        if substrs_in_str(lic, ["byncnd", "noncommercialnoderiv"]):
            return f"https://creativecommons.org/licenses/by-nc-nd/{version}/"
        if substrs_in_str(lic, ["bysa", "sharealike"]):
            return f"https://creativecommons.org/licenses/by-sa/{version}/"
        if substrs_in_str(lic, ["bync", "noncommercial"]):
            return f"https://creativecommons.org/licenses/by-nc/{version}/"
        if substrs_in_str(lic, ["bynd", "noderiv"]):
            return f"https://creativecommons.org/licenses/by-nd/{version}/"
        if substrs_in_str(lic, ["by"]):
            return f"https://creativecommons.org/licenses/by/{version}/"
        return None
    return lic


def mono_val(val):
    if type(val) in [str, int]:
        return val
    if type(val) == dict:
        if len(val.keys()) == 1:
            val = list(val.values())[0]
    if type(val) == list and len(val) == 1:
        val = val[0]
    return val


def get_meta(metadatum, meta_type="label"):
    if meta_type not in metadatum:
        return None
    meta_label = metadatum[meta_type]
    if type(meta_label) == str:
        return meta_label
    if type(meta_label) == list:
        for lang_label in meta_label:
            if "@language" in lang_label and lang_label["@language"] == "en":
                return mono_val(lang_label["@value"])
            if "language" in lang_label and lang_label["language"] == "en":
                return mono_val(lang_label["value"])
    if type(meta_label) == dict:
        if len(meta_label.keys()) == 1:
            return mono_val(meta_label.values()[0])
        if "en" in meta_label:
            return mono_val(meta_label["en"])
    return None


def get_meta_value(metadatum, label: str):
    meta_label = get_meta(metadatum, "label")
    if meta_label not in [label, label.capitalize(), f"@{label}"]:
        return None
    return get_meta(metadatum, "value")
