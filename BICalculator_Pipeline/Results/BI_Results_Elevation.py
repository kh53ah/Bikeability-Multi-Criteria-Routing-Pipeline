import csv
import os

# ============================================================
# PARAMETERS
# ============================================================
OUTPUT_DIR  = "results"
OUTPUT_FILE = "Elevation_Results.csv"

ELEVATION_COLUMNS = [
    "elevation_score",
]
# ============================================================


class BI_Results_Elevation:
    """
    Exports Elevation scores to CSV.
    Each row = one OSM way.
    Columns = street_name, osm_way_id, osm_way_idx, all Elevation criteria scores.
    Missing criteria default to None.
    Appends to existing CSV if it exists, creates new one if not.
    """

    @staticmethod
    def export(street_name, osm_way_id, osm_way_idx, elevation_scores):
        """
        Parameters
        ----------
        street_name      : str  — name of the street
        osm_way_id       : any  — OSM way index value from gdf
        osm_way_idx      : int  — 0-based position of this way within the street
        elevation_scores : dict — Elevation criteria scores {criteria: score}
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        fieldnames = ["street_name", "osm_way_id", "osm_way_idx"] + ELEVATION_COLUMNS

        row = {
            "street_name": street_name,
            "osm_way_id":  osm_way_id,
            "osm_way_idx": osm_way_idx,
        }
        for col in ELEVATION_COLUMNS:
            val = elevation_scores.get(col)
            row[col] = round(val, 4) if val is not None else None

        file_exists = os.path.isfile(csv_path)

        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"  Elevation results saved → {csv_path}")