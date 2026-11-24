import ast
import csv
import pandas as pd
import osmnx as ox
from pyproj import Geod

# ==============================================================================
# CONFIGURATION  ← edit here
# ==============================================================================
CITY          = "Würzburg, Germany"
CRITERIA_FILE = "Criteria_scores.csv"
OUTPUT_FILE   = "Criteria_scores_with_length.csv"

geod = Geod(ellps="WGS84")

# ==============================================================================
# HELPER: Extract integer way ID from tuple string like ('way', 4825010)
# ==============================================================================
def extract_way_id(val) -> int:
    try:
        parsed = ast.literal_eval(str(val))
        return int(parsed[1]) if isinstance(parsed, tuple) else int(float(str(val)))
    except:
        return None

# ==============================================================================
# HELPER: Calculate geodetic length in metres from shapely geometry
# ==============================================================================
def calc_length(geom) -> float:
    return round(abs(geod.geometry_length(geom)), 2)

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    # --- Load criteria CSV ---
    print(f"Loading {CRITERIA_FILE}...")
    criteria = pd.read_csv(CRITERIA_FILE)
    criteria["_way_id_int"] = criteria["osm_way_id"].apply(extract_way_id)
    all_way_ids = set(criteria["_way_id_int"].dropna().astype(int).tolist())
    print(f"  {len(criteria)} rows, {len(all_way_ids)} unique way IDs.")

    # --- Download full network once ---
    print(f"\nDownloading full street network for {CITY}...")
    G = ox.graph_from_place(CITY, network_type="all")
    edges = ox.graph_to_gdfs(G, nodes=False)
    print(f"  {len(edges)} total edges downloaded.")

    # --- Build way_id → length lookup ---
    print("\nCalculating lengths for matched edges...")
    length_lookup = {}
    for osm_id, row in edges.iterrows():
        way_id = row.get("osmid")
        if isinstance(way_id, list):
            ids = way_id
        else:
            try:
                ids = [int(float(way_id))]
            except:
                continue

        for wid in ids:
            wid = int(wid)
            if wid in all_way_ids and wid not in length_lookup:
                try:
                    length_lookup[wid] = calc_length(row.geometry)
                except:
                    continue

    print(f"  {len(length_lookup)} way IDs matched with lengths.")

    # --- Assign lengths to criteria rows ---
    criteria["length"] = criteria["_way_id_int"].apply(
        lambda wid: length_lookup.get(int(wid)) if pd.notna(wid) else None
    )

    # --- Compute ratio ---
    max_length = criteria["length"].max()
    print(f"  Max length: {max_length:.2f} m")
    criteria["distance"] = (1 - criteria["length"] / max_length).round(6)

    # --- Drop helper column and save ---
    criteria.drop(columns=["_way_id_int", "length"], inplace=True)
    criteria.to_csv(OUTPUT_FILE, index=False)

    matched   = criteria["distance"].notna().sum()
    unmatched = criteria["distance"].isna().sum()
    print(f"\n  Matched:   {matched} rows")
    print(f"  Unmatched: {unmatched} rows")
    print(f"\nSaved → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()