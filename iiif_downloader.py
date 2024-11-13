import requests
import os


def download_iiif_images(manifest_url, output_dir='images', finish_after=None):
    os.makedirs(output_dir, exist_ok=True)

    response = requests.get(manifest_url)
    json_manifest = response.json()

    canvases = json_manifest['sequences'][0]['canvases']
    for i, canvas in enumerate(canvases):
        if finish_after and i >= finish_after:
            return

        image_url = canvas['images'][0]['resource']['@id']
        print(f"Downloading {image_url}...")

        # Download image
        image_response = requests.get(image_url)

        # Save image
        filepath = os.path.join(output_dir, f"image_{i + 1}.jpg")
        with open(filepath, 'wb') as f:
            f.write(image_response.content)

        print(f"{image_url} has been downloaded!")


if __name__ == "__main__":
    with open("test-manifests.txt", mode='r') as file:
        manifests = list(file.read().splitlines())

    for manifest in manifests:
        print(f"Downloading {manifest}...")
        download_iiif_images(manifest, finish_after=3)
