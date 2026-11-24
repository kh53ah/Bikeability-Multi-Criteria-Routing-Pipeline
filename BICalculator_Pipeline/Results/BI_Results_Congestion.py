import csv
import os

# ============================================================
# PARAMETERS
# ============================================================
OUTPUT_DIR  = "results"
OUTPUT_FILE = "Congestion_Results.csv"

CONGESTION_COLUMNS = [
    "congestion_score",
]
# ============================================================


class BI_Results_Congestion:
    """
    Exports Congestion scores to CSV.
    Each row = one OSM way.
    Columns = street_name, osm_way_id, osm_way_idx, all Congestion criteria scores.
    Missing criteria default to None.
    Appends to existing CSV if it exists, creates new one if not.
    """

    @staticmethod
    def export(street_name, osm_way_id, osm_way_idx, congestion_scores):
        """
        Parameters
        ----------
        street_name       : str  — name of the street
        osm_way_id        : any  — OSM way index value from gdf
        osm_way_idx       : int  — 0-based position of this way within the street
        congestion_scores : dict — Congestion criteria scores {criteria: score}
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        fieldnames = ["street_name", "osm_way_id", "osm_way_idx"] + CONGESTION_COLUMNS

        row = {
            "street_name": street_name,
            "osm_way_id":  osm_way_id,
            "osm_way_idx": osm_way_idx,
        }
        for col in CONGESTION_COLUMNS:
            val = congestion_scores.get(col)
            row[col] = round(val, 4) if val is not None else None

        file_exists = os.path.isfile(csv_path)

        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"  Congestion results saved → {csv_path}")
