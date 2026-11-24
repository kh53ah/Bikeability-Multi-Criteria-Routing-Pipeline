import csv
import os

# ============================================================
# PARAMETERS
# ============================================================
OUTPUT_DIR  = "results"
OUTPUT_FILE = "SVI_Results.csv"

SVI_COLUMNS = [
    "Vegetation",
    "Pothole",
    "Traffic Sign (Back)",
    "Catch Basin",
    "Traffic Light",
    "Rail Track",
    "Lane Marking - Crosswalk",
    "Utility Pole",
    "Crosswalk - Plain",
    "Traffic Sign (Front)",
    "Curb Cut",
    "Traffic Sign Frame",
    "Sidewalk",
    "Building",
    "Water",
    "Street Light",
    "Bench",
    "Bike Rack",
    "Phone Booth",
]
# ============================================================


class BI_Results_SVI:
    """
    Exports SVI scores to CSV.
    Each row = one OSM way.
    Columns = street_name, osm_way_id, osm_way_idx, all SVI criteria scores.
    Missing criteria default to None.
    Appends to existing CSV if it exists, creates new one if not.
    """

    @staticmethod
    def export(street_name, osm_way_id, osm_way_idx, svi_scores):
        """
        Parameters
        ----------
        street_name : str  — name of the street
        osm_way_id  : any  — OSM way index value from gdf
        osm_way_idx : int  — 0-based position of this way within the street
        svi_scores  : dict — SVI criteria scores {criteria: score}
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        fieldnames = ["street_name", "osm_way_id", "osm_way_idx"] + SVI_COLUMNS

        row = {
            "street_name": street_name,
            "osm_way_id":  osm_way_id,
            "osm_way_idx": osm_way_idx,
        }
        for col in SVI_COLUMNS:
            val = svi_scores.get(col)
            row[col] = round(val, 4) if val is not None else None

        file_exists = os.path.isfile(csv_path)

        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"  SVI results saved → {csv_path}")
