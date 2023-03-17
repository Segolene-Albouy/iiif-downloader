import argparse
from pathlib import Path
import requests
import shutil
from urllib.parse import urlparse
import time

from utils import coerce_to_path_and_create_dir
from utils.logger import console, log

def get_id(dic):
    if type(dic) == dict:
        try:
            return dic['@id']
        except KeyError as e:
            try:
                return dic['id']
            except KeyError as e:
                log(f"No id provided {e}")
    console(dic)

    if type(dic) == str:
        return dic

    return None


def get_canvas_img(canvas_img):
    img_id = get_img_id(canvas_img['resource'])
    img_url = get_id(canvas_img['resource']['service'])
    return img_id, img_url


def get_item_img(item_img):
    img_id = get_img_id(item_img)
    img_url = get_id(item_img['body']['service'][0])
    return img_id, img_url


def get_img_id(img):
    img_id = get_id(img)
    if "default.jpg" in img_id:
        console(img_id.split('/')[-5])
        return img_id.split('/')[-5]
        # return Path(urlparse(img_id).path).parts[-5]
    return img_id.split('/')[-1]


class IIIFDownloader:
    """Download all image resources from a list of manifest urls."""

    def __init__(self, manifest_urls, output_dir, width=None, height=None):
        self.manifest_urls = manifest_urls
        self.output_dir = coerce_to_path_and_create_dir(output_dir)
        self.size = self.get_formatted_size(width, height)

    @staticmethod
    def get_formatted_size(width, height):
        return "1000,"

    def run(self):
        for url in self.manifest_urls:
            manifest = self.get_json(url)
            if manifest is not None:
                manifest_id = Path(urlparse(get_id(manifest)).path).parent.name

                console(f"Processing {manifest_id}...")
                output_path = coerce_to_path_and_create_dir(
                    self.output_dir / manifest_id
                )
                resources = self.get_resources(manifest)

                for rsrc in resources:
                    img_id = rsrc[0]
                    img_url = f"{rsrc[1]}/full/{self.size}/0/default.jpg"
                    console(rsrc)
                    
                    with requests.get(img_url, stream=True) as response:
                        response.raw.decode_content = True
                        output_file = output_path / f"{img_id}.jpg"
                        console(f"Saving {output_file.relative_to(self.output_dir)}...")
                        time.sleep(0.5)
                        try:
                            with open(output_file, mode="wb") as f:
                                shutil.copyfileobj(response.raw, f)
                        except Exception as e:
                            console(f"{url} not working\n{e}", "error")


    @staticmethod
    def get_json(url):
        try:
            response = requests.get(url)
            if response.ok:
                return response.json()
            else:
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log(e)
            return None

    @staticmethod
    def get_resources(manifest):
        try:
            img_list = [canvas['images'] for canvas in manifest['sequences'][0]['canvases']]
            img_info = [get_canvas_img(img) for imgs in img_list for img in imgs]
        except KeyError:
            try:
                img_list = [item for items in manifest['items'] for item in items['items'][0]['items']]
                img_info = [get_item_img(img) for img in img_list]
            except KeyError as e:
                console(manifest['items'][0])
                log(f"Error when retrieving canvas {e}")
                return []

        return img_info



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all image resources from a list of manifest urls')
    parser.add_argument('-f', '--file', nargs='?', type=str, required=True, help='File containing manifest urls')
    parser.add_argument('-o', '--output_dir', nargs='?', type=str, default='output', help='Output directory name')
    parser.add_argument('--width', type=int, default=None, help='Image width')
    parser.add_argument('--height', type=int, default=None, help='Image height')
    args = parser.parse_args()

    with open(args.file, mode='r') as f:
        manifest_urls = f.read().splitlines()
    manifest_urls = list(filter(None, manifest_urls))

    output_dir = args.output_dir if args.output_dir is not None else 'output'
    downloader = IIIFDownloader(manifest_urls, output_dir=output_dir, width=args.width, height=args.height)
    downloader.run()
