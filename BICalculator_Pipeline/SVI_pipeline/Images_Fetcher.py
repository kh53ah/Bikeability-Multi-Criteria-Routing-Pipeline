import requests
from PIL import Image
from io import BytesIO

# ============================================================
# PARAMETERS
# ============================================================
MAPILLARY_ACCESS_TOKEN = "MLY|26696618976599591|7c8e510c2f49a99f5139ac6c4d12ff91"
MAPILLARY_API_URL      = "https://graph.mapillary.com/images"
# ============================================================


class ImageFetcher:
    """
    Step 3.1 of the Segmentation + BI-Calculations per segment pipeline.
    Fetches the first image of 1024x768 resolution from Mapillary image within a segment bbox.
    Returns a list with one downloaded image (PIL Image object),
    or an empty list if no images are found.
    """

    @staticmethod
    def get_images_for_segment(segment_bbox):
        """
        Fetches all image metadata within the segment bbox,
        picks the highest resolution image (width × height),
        downloads it and returns it in a list.

        Parameters
        ----------
        segment_bbox : Polygon — bbox geometry in WGS84 (from segments_gdf)

        Returns
        -------
        list : [PIL.Image] — single best image, or [] if no images found
        """
        west, south, east, north = segment_bbox.bounds

        # Fetch image metadata from Mapillary
        params = {
            "access_token": MAPILLARY_ACCESS_TOKEN,
            "bbox":         f"{west},{south},{east},{north}",
            "fields":       "id,width,height,thumb_original_url"
        }

        response = requests.get(MAPILLARY_API_URL, params=params)

        if response.status_code != 200:
            print(f"Mapillary API error {response.status_code}: {response.text}")
            return []

        data = response.json().get("data", [])

        if not data:
            return []

        # Pick first image
        best = next((img for img in data if img.get("width", 0) <= 3840 and img.get("height", 0) <= 2880), None)
        if not best:
            print("  No images within size limit found.")
            return []

        # Download the best image
        image_url = best.get("thumb_original_url")
        if not image_url:
            print(f"No URL found for image {best.get('id')}")
            return []

        img_response = requests.get(image_url)
        if img_response.status_code != 200:
            print(f"Failed to download image {best.get('id')}")
            return []

        # Discard metadata, return only pixel data
        image = Image.open(BytesIO(img_response.content)).convert("RGB")
        return [image]