import requests
from io import BytesIO

# ============================================================
# PARAMETERS — update these if server changes
# ============================================================
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080
SERVER_URL  = f"http://{SERVER_HOST}:{SERVER_PORT}/segment"
BATCH_SIZE  = 5
# ============================================================


class Mask2FormerSegmentation:

    @staticmethod
    def segment_batch(images):
        """
        Sends images to the Mask2Former Flask server in chunks of BATCH_SIZE.
        Returns a flat list of segmentation results in the same order as input.

        Parameters
        ----------
        images : list of PIL.Image

        Returns
        -------
        list of list of dict : [[{"label": str, "area": int}, ...], ...]
        """
        all_results = []

        for chunk_start in range(0, len(images), BATCH_SIZE):
            chunk = images[chunk_start:chunk_start + BATCH_SIZE]
            print(f"    Sending images {chunk_start + 1}–{chunk_start + len(chunk)} of {len(images)}...")

            try:
                files = []
                for i, image in enumerate(chunk):
                    buffer = BytesIO()
                    image.save(buffer, format="JPEG")
                    files.append(("images", (f"image_{i}.jpg", buffer.getvalue(), "image/jpeg")))

                response = requests.post(SERVER_URL, files=files, timeout=120)
                response.raise_for_status()

                results = response.json()

                if isinstance(results, dict) and "error" in results:
                    print(f"    Server error on chunk: {results['error']}")
                    # fill with empty results to keep indices aligned
                    all_results.extend([[] for _ in chunk])
                    continue

                all_results.extend(results)

            except Exception as e:
                print(f"    Mask2Former chunk error: {e}")
                # fill with empty results to keep indices aligned
                all_results.extend([[] for _ in chunk])

        return all_results