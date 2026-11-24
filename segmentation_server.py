from flask import Flask, request, jsonify
from transformers import Mask2FormerForUniversalSegmentation, Mask2FormerImageProcessor
from PIL import Image
from io import BytesIO
import torch

# ============================================================
# PARAMETERS
# ============================================================
MODEL_ID = "facebook/mask2former-swin-large-mapillary-vistas-panoptic"
HOST     = "0.0.0.0"
PORT     = 5000
# ============================================================

app = Flask(__name__)

# Load model once at startup into GPU
print("Loading model...")
processor = Mask2FormerImageProcessor.from_pretrained(MODEL_ID)
model     = Mask2FormerForUniversalSegmentation.from_pretrained(MODEL_ID)
model     = model.to("cuda")
model.eval()
print("Model ready.")


@app.route("/segment", methods=["POST"])
def segment():
    """
    Accepts a multipart/form-data POST with N image files.
    Runs them through Mask2Former as a single batch.
    Returns a JSON array of N results in the same order as the images sent.
    """
    try:
        # Read all images from multipart request
        files = request.files.getlist("images")
        if not files:
            return jsonify({"error": "No images provided"}), 400

        images = [Image.open(BytesIO(f.read())).convert("RGB") for f in files]
        target_sizes = [img.size[::-1] for img in images]

        # Run batch through model in one forward pass
        inputs = processor(images=images, return_tensors="pt")
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        # Post-process all images at once
        results = processor.post_process_panoptic_segmentation(
            outputs,
            target_sizes=target_sizes
        )

        # Build response: one list of {label, area} per image
        batch_response = []
        for result in results:
            segmentation_map = result["segmentation"].cpu().numpy()
            segments_info    = result["segments_info"]

            image_response = []
            for seg in segments_info:
                seg_id = seg["id"]
                label  = model.config.id2label[seg["label_id"]]
                area   = int((segmentation_map == seg_id).sum())
                image_response.append({"label": label, "area": area})

            image_response.sort(key=lambda x: x["area"], reverse=True)
            batch_response.append(image_response)

        return jsonify(batch_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
