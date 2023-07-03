import argparse
import glob
import os
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import requests
from urllib.parse import urlparse
import time

from utils import MAX_SIZE, IMG_PATH, sanitize_str, get_json, save_img
from utils.constants import MIN_SIZE
from utils import create_dir, get_height, get_width, get_id, sanitize_url
from utils.logger import console, log


class IIIFDownloader:
    """Download all image resources from a list of manifest urls."""

    def __init__(
        self,
        manifest_list,
        max_dim=MAX_SIZE,
        min_dim=1500,
        allow_truncation=False,
    ):
        self.manifest_urls = manifest_list
        self.manifest_id = None  # Identifier for the directory name
        self.manifest_dir_path = IMG_PATH
        self.current_manifest_url = None
        self.allow_truncation = allow_truncation

        self.max_dim = max_dim  # Maximal height in px
        self.min_dim = min_dim  # Minimal height in px


    def run(self):
        for url in self.manifest_urls:
            url, first_canvas = self.get_first_canvas(url)
            self.current_manifest_url = url
            manifest = get_json(url)
            if manifest is not None:
                self.manifest_id = self.get_manifest_id(manifest)
                console(f"Processing {self.manifest_id}...")

                self.manifest_dir_path = create_dir(
                    IMG_PATH / self.manifest_id
                )
                i = 1
                for rsrc in self.get_iiif_resources(manifest):
                    if i >= first_canvas:
                        self.save_iiif_img(rsrc, i)
                    i += 1


    def save_iiif_img(self, img_rsrc, i, size=None, re_download=False):
        img_name = f"{i:04d}.jpg"
        f_size = size if size is not None else self.get_size(img_rsrc)

        if (
            glob.glob(os.path.join(self.manifest_dir_path, img_name))
            and not re_download
        ):
            img = Image.open(self.manifest_dir_path / img_name)
            if self.check_size(img, img_rsrc):
                # if the img is already downloaded and has the correct size, don't download it again
                return False

        img_url = get_id(img_rsrc["service"])
        iiif_url = sanitize_url(f"{img_url}/full/{f_size}/0/default.jpg")

        # Gallica is not accepting more than 5 downloads of >1000px / min after
        sleep = 12 if "gallica" in self.current_manifest_url else 0.25
        time.sleep(sleep)

        try:
            with requests.get(iiif_url, stream=True) as response:
                response.raw.decode_content = True
                try:
                    img = Image.open(response.raw)
                except (UnidentifiedImageError, SyntaxError) as e:
                    time.sleep(sleep)
                    if size == f_size:
                        size = self.get_reduced_size(img_rsrc)
                        self.save_iiif_img(img_rsrc, i, self.get_formatted_size(size))
                        return
                    else:
                        log(f"[save_iiif_img] {iiif_url} is not a valid img file: {e}")
                        return
                except (IOError, OSError) as e:
                    if size == "full":
                        size = self.get_reduced_size(img_rsrc)
                        self.save_iiif_img(img_rsrc, i, self.get_formatted_size(size))
                        return
                    else:
                        log(
                            f"[save_iiif_img] {iiif_url} is a truncated or corrupted image: {e}"
                        )
                        return
        except requests.exceptions.RequestException as e:
            log(f"[save_iiif_img] Failed to download image from {iiif_url} (#{i}):\n{e}")
            return False

        try:
            save_img(img, img_name, self.manifest_dir_path)
        except OSError as e:
            if not self.allow_truncation:
                log(f"[save_iiif_img] {iiif_url} was truncated by {e} bytes (#{i}): ")
                return False
            try:
                if 0 < int(f"{e}") < 3:
                    log(f"[save_iiif_img] {iiif_url} was truncated by {e} bytes (#{i})\nSaving the truncated version")
                    save_img(img, img_name, self.manifest_dir_path, load_truncated=True)
            except ValueError as e:
                log(f"[save_iiif_img] Failed to save image from {iiif_url} (#{i}):\n{e}")
                return False
            except Exception as e:
                log(f"[save_iiif_img] Couldn't save the truncated image {iiif_url} (#{i}):\n{e} bytes not processed")
                return False
        return True

    def get_first_canvas(self, manifest_line):
        if len(manifest_line.split(" ")) != 2:
            return manifest_line, 0

        url = manifest_line.split(" ")[0]
        try:
            first_canvas = int(manifest_line.split(" ")[1])
        except (ValueError, IndexError) as e:
            log(f"[get_first_canvas] Could not retrieve canvas from {manifest_line}: {e}")
            first_canvas = 0

        return url, first_canvas

    def get_img_rsrc(self, iiif_img):
        try:
            img_rsrc = iiif_img["resource"]
        except KeyError:
            try:
                img_rsrc = iiif_img["body"]
            except KeyError:
                return None
        return img_rsrc

    def get_iiif_resources(self, manifest, only_img_url=False):
        try:
            # Usually images URL are contained in the "canvases" field
            img_list = [
                canvas["images"] for canvas in manifest["sequences"][0]["canvases"]
            ]
            img_info = [self.get_img_rsrc(img) for imgs in img_list for img in imgs]
        except KeyError:
            # But sometimes in the "items" field
            try:
                img_list = [
                    item
                    for items in manifest["items"]
                    for item in items["items"][0]["items"]
                ]
                img_info = [self.get_img_rsrc(img) for img in img_list]
            except KeyError as e:
                log(
                    f"[get_iiif_resources] Unable to retrieve resources from manifest {self.current_manifest_url}\n{e}"
                )
                return []

        return img_info

    def get_size(self, img_rsrc):
        if self.max_dim is None:
            return "full"
        h, w = get_height(img_rsrc), get_width(img_rsrc)
        if h > w:
            return self.get_formatted_size("", str(self.max_dim))
        return self.get_formatted_size(str(self.max_dim), "")

    def check_size(self, img, img_rsrc):
        """
        Checks if an already downloaded image has the correct dimensions
        """
        if self.max_dim is None:
            if int(img.height) == get_height(img_rsrc):  # for full size
                return True

        if int(img.height) == self.max_dim or int(img.width) == self.max_dim:
            # if either the height or the width corresponds to max dimension
            # if it is too big, re-download again
            return True

        return False  # Download again

    def get_formatted_size(self, width="", height=""):
        if not hasattr(self, "max_dim"):
            self.max_dim = None

        if not width and not height:
            if self.max_dim is not None:
                return f",{self.max_dim}"
            return "full"

        if width and self.max_dim and int(width) > self.max_dim:
            width = f"{self.max_dim}"
        if height and self.max_dim and int(height) > self.max_dim:
            height = f"{self.max_dim}"

        return f"{width or ''},{height or ''}"

    def get_reduced_size(self, img_rsrc):
        h, w = get_height(img_rsrc), get_width(img_rsrc)
        larger_side = h if h > w else w

        if larger_side < self.min_dim:
            return ""
        if larger_side > self.min_dim * 2:
            return str(int(larger_side / 2))
        return str(self.min_dim)

    def get_dir_name(self):
        return sanitize_str(self.current_manifest_url).replace("manifest", "").replace("json", "")

    def get_manifest_id(self, manifest):
        manifest_id = get_id(manifest)
        if manifest_id is None:
            return self.get_dir_name()
        if "manifest" in manifest_id:
            try:
                manifest_id = Path(urlparse(get_id(manifest)).path).parent.name
                if "manifest" in manifest_id:
                    return self.get_dir_name()
                return sanitize_str(manifest_id)
            except Exception:
                return self.get_dir_name()
        return sanitize_str(manifest_id.split("/")[-1])



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all image resources from a list of manifest urls')
    parser.add_argument('-f', '--file', nargs='?', type=str, required=True, help='File containing manifest urls')
    parser.add_argument('-max', '--max_dim', nargs='?', type=int, default=MAX_SIZE, help='Maximal size in pixel')
    parser.add_argument('-min', '--min_dim', nargs='?', type=int, default=MIN_SIZE, help='Minimal size in pixel')
    args = parser.parse_args()

    with open(args.file, mode='r') as f:
        manifests = f.read().splitlines()
    manifests = list(filter(None, manifests))

    downloader = IIIFDownloader(manifests, max_dim=args.max_dim, min_dim=args.min_dim)
    downloader.run()
