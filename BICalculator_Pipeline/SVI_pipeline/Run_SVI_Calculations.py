from SVI_pipeline.Images_Fetcher import ImageFetcher
from SVI_pipeline.Mask2Former import Mask2FormerSegmentation
from SVI_pipeline.SVI_Criteria_Calculator import SVI_Score


class RoadSegmentation:
    """
    Step 4 of the main pipeline.
    Runs the full inner segmentation pipeline for all segments in two passes:
      Pass 1 — ImageFetcher   : fetch one Mapillary image per segment (N calls)
      Pass 2 — Mask2Former    : send all images in one batch (1 server call)
    Then scores each result with SVI_Score and accumulates into a global dict.
    Returns the global dict and the segment count to Street_BI_Calculator.
    """

    def __init__(self, segments_gdf):
        """
        Parameters
        ----------
        segments_gdf : GeoDataFrame — output of StreetSegmentsCreator.create_segments()
        """
        self.segments_gdf = segments_gdf

    def run(self):
        """
        Returns
        -------
        tuple : (global_scores dict, segment_count int)
        """
        global_scores = {}
        segment_count = 0

        # ── PASS 1 — Fetch one image per segment (N Mapillary calls) ─────
        print(f"  SVI Pass 1 — fetching images for {len(self.segments_gdf)} segments...")

        images        = []  # PIL images to send to server
        valid_indices = []  # track which segments actually got an image

        for idx, segment in self.segments_gdf.iterrows():
            image_list = ImageFetcher.get_images_for_segment(segment.geometry) or []
            if image_list:
                images.append(image_list[0])
                valid_indices.append(idx)

        print(f"  SVI Pass 1 complete. {len(images)}/{len(self.segments_gdf)} images fetched.")

        if not images:
            print("  No images found for any segment. Skipping SVI.")
            return global_scores, segment_count

        # ── PASS 2 — Batch segmentation (1 server call) ──────────────────
        print(f"  SVI Pass 2 — sending {len(images)} images to Mask2Former...")

        batch_results = Mask2FormerSegmentation.segment_batch(images)

        if not batch_results:
            print("  Mask2Former batch returned no results.")
            return global_scores, segment_count

        print(f"  SVI Pass 2 complete. {len(batch_results)} results received.")

        # ── SCORING — one result per image, in order ──────────────────────
        for segmentation_result in batch_results:
            segment_scores = SVI_Score.calculate_SVI(segmentation_result)

            if segment_scores is None:
                continue

            segment_count += 1

            for label, score in segment_scores.items():
                if label in global_scores:
                    global_scores[label] += score
                else:
                    global_scores[label] = score

        print(f"  SVI scoring complete. {segment_count} segments scored.")
        return global_scores, segment_count
