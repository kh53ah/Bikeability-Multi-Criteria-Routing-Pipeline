import pandas as pd
import ast

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CRITERIA_FILE = "Criteria_scores.csv"
LENGTHS_FILE  = "street_lengths.csv"
OUTPUT_FILE   = "Criteria_scores_with_length.csv"

# ==============================================================================
# LOAD
# ==============================================================================
criteria = pd.read_csv(CRITERIA_FILE)
lengths  = pd.read_csv(LENGTHS_FILE)

# Extract integer way ID from both CSVs
def extract_id(val):
    try:
        parsed = ast.literal_eval(str(val))
        return int(parsed[1]) if isinstance(parsed, tuple) else int(float(str(val)))
    except:
        return None

criteria["_way_id_norm"] = criteria["osm_way_id"].apply(extract_id)
lengths["_way_id_norm"]  = lengths["osm_way_id"].apply(extract_id)

# ==============================================================================
# MERGE on street_name + osm_way_idx + normalized way id
# ==============================================================================
merged = criteria.merge(
    lengths[["street_name", "osm_way_idx", "_way_id_norm", "length/max_length"]],
    on=["street_name", "osm_way_idx", "_way_id_norm"],
    how="left"
)

merged.drop(columns=["_way_id_norm"], inplace=True)

matched   = merged["length/max_length"].notna().sum()
unmatched = merged["length/max_length"].isna().sum()
print(f"Matched:   {matched} rows")
print(f"Unmatched: {unmatched} rows")

merged.to_csv(OUTPUT_FILE, index=False)
print(f"Saved → {OUTPUT_FILE}")