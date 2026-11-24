from cProfile import label

from SVI_pipeline.SVI_Criteria import SVICriteria

# ============================================================
# LABEL → CRITERIA MAPPING
# Each label maps to a list of criteria functions it triggers.
# ============================================================
LABEL_TO_CRITERIA = {
    'Building':                 [SVICriteria.Scenery_criteria],
    'Vegetation':               [SVICriteria.Scenery_criteria],
    'Water':                    [SVICriteria.Scenery_criteria],
    'Pothole':                  [SVICriteria.Potholes_criteria],
    'Curb Cut':                 [SVICriteria.CurbCuts_criteria], 
    'Crosswalk - Plain':        [SVICriteria.CrossWalk_criteria],
    'Lane Marking - Crosswalk': [SVICriteria.CrossWalk_criteria],
    'Rail Track':               [SVICriteria.TramRails_criteria],
    'Utility Pole':             [SVICriteria.UtilityPole_criteria],
    'Traffic Light':            [SVICriteria.TrafficLights_criteria],
    'Traffic Sign Frame':       [SVICriteria.TrafficLights_criteria],
    'Traffic Sign (Back)':      [SVICriteria.TrafficLights_criteria],
    'Traffic Sign (Front)':     [SVICriteria.TrafficLights_criteria],
    'Street Light':             [SVICriteria.Streetlights_criteria],
    'Catch Basin':              [SVICriteria.CatchBasin_criteria],
    'Bench':                    [SVICriteria.StreetAmenities_criteria],
    'Bike Rack':                [SVICriteria.StreetAmenities_criteria],
    'Phone Booth':              [SVICriteria.StreetAmenities_criteria],
    'Sidewalk':                 [SVICriteria.SideWalk_criteria],
}

BAD_LABELS = {
    'Pothole',
    'Utility Pole',
    'Rail Track',
    'Crosswalk - Plain', 'Lane Marking - Crosswalk',
    'Curb Cut',
    'Traffic Light', 'Traffic Sign Frame', 'Traffic Sign (Back)', 'Traffic Sign (Front)',
    'Catch Basin'
}
# ============================================================


class SVI_Score:
    """
    Step 3 of the Segmentation + SVI-Calculations per segment pipeline.
    Scans segments_info once, calls only the relevant criteria functions
    for each detected label, and returns a dict of {label: score} for
    the segment's image.
    """

    @staticmethod
    def calculate_SVI(segments_info):
        """
        Calculates the SVI score for a single image.

        Parameters
        ----------
        segments_info : list of dict — [{"label": str, "area": int}, ...]
                        output of Mask2FormerSegmentation.segment()

        Returns
        -------
        dict : {label: score} for this segment, or None if no relevant labels found
        """
        scores               = {}
        total_image_area     = sum(s["area"] for s in segments_info)
        bad_labels_remaining = set(BAD_LABELS)

        if total_image_area == 0:
            return None

        # Single scan through segments_info
        for segment in segments_info:
            label = segment["label"]
            area  = segment["area"]

            if label in bad_labels_remaining:
                bad_labels_remaining.remove(label)
                scores[label] = 0.0          # ← explicitly mark as bad/present
                continue

            elif label in LABEL_TO_CRITERIA:

                for func in LABEL_TO_CRITERIA[label]:
                    if label in ('Building', 'Vegetation', 'Water'):
                        score = func()
                        score = SVI_Score.normalize_score_by_image_size(score, area, total_image_area)
                    else:
                        score = func()

                    if score is not None:
                        if label in scores:
                            scores[label] = min(scores[label] + score, 1.0)
                        else:
                            scores[label] = score

        # Absence defaults — bad labels not detected → good score
        for label in bad_labels_remaining:
            score = LABEL_TO_CRITERIA[label][0]()
            scores[label] = score

        if not scores:
            return None

        return scores

    @staticmethod
    def normalize_score_by_image_size(score, area, total_image_area):
        return score * area / total_image_area