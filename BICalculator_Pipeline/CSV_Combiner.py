import pandas as pd
import os
import glob

# ── Configuration ────────────────────────────────────────────────────────────
CSV_FOLDER = "C:\\Studium\\SS26\\Abschlussarbeit\\Abschlussarbeit\\results"
OUTPUT_FILE = "Criteria_scores.csv"
KEY_COLS = ["street_name", "osm_way_idx"]
EXCLUDE_COLS = ["traffic_calming", "Pothole", "Rail Track", "Sidewalk", "Water",
                "Street Light", "Bench", "Bike Rack", "Phone Booth"]

# Default values applied to NaN cells after merging.
# Only columns listed here will be filled — others are left as NaN.
NAN_DEFAULTS = {
    "aqi_score":                0.92, # the average
    "congestion_score":         0.894, # the average
    "elevation_score":          0.571, # average
    "road_type":                0.8, # assuming that they are smalls treets, so they get the typical value of it
    "pavement":                 1.0, # assuming that they are smalls treets, so they get the typical value of it
    "road_width":               1.0, # assuming that they are smalls treets, so they get the typical value of it
    "max_speed":                1.0, # assuming that they are smalls treets, so they get the typical value of it
    "landuse":                  0.126, # the average
    "parking":                  1.0, # assuming that they are smalls treets, so they get the typical value of it
    "transit_facilities":       0.0, # assuming that they are smalls treets, so there is no transit facilities there
    "Traffic Sign (Back)":      1.0, # assuming that they are smalls treets, so there is no traffic signs there
    "Catch Basin":              1.0, # assuming that they are smalls treets, so there is no catch basins there
    "Traffic Light":            1.0, # assuming that they are smalls treets, so there is no traffic lights there
    "Lane Marking - Crosswalk": 1.0, # assuming that they are smalls treets, so there is no crosswalks there
    "Utility Pole":             0.91, # the average
    "Crosswalk - Plain":        1.0, # assuming that they are smalls treets, so there is no crosswalks there
    "Traffic Sign (Front)":     1.0, # assuming that they are smalls treets, so there is no traffic signs there
    "Curb Cut":                 0.77, # the average
    "Traffic Sign Frame":       1.0, # assuming that they are smalls treets, so there is no traffic signs there
    "Building":                 0.164, # the average
}
# ─────────────────────────────────────────────────────────────────────────────


def detect_delimiter(path: str) -> str:
    with open(path, encoding="utf-8-sig") as f:
        first_line = f.readline()
    return ";" if first_line.count(";") > first_line.count(",") else ","


def normalize_idx(series: pd.Series) -> pd.Series:
    """Normalize osm_way_idx to a clean integer string: 0.0 -> '0', 1 -> '1'."""
    return pd.to_numeric(series, errors="coerce").fillna(-1).astype(int).astype(str)


def load_csv(path: str) -> pd.DataFrame:
    delim = detect_delimiter(path)
    df = pd.read_csv(path, sep=delim, engine="python",
                     encoding="utf-8-sig", on_bad_lines="skip")

    for col in KEY_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing key column '{col}' in file: {path}")

    df["street_name"] = df["street_name"].astype(str).str.strip()
    df["osm_way_idx"] = normalize_idx(df["osm_way_idx"])

    # Always drop osm_way_id here — it gets rebuilt separately across all files
    df = df.drop(columns=["osm_way_id"], errors="ignore")

    if EXCLUDE_COLS:
        df = df.drop(columns=EXCLUDE_COLS, errors="ignore")

    if df.duplicated(subset=KEY_COLS).any():
        dupes = df.duplicated(subset=KEY_COLS).sum()
        print(f"    → {dupes} duplicate key(s) found, aggregating...")
        df = df.groupby(KEY_COLS, as_index=False).first()

    return df


def collect_osm_way_ids(folder: str) -> pd.DataFrame:
    """Scan all CSVs and collect osm_way_id values across all files,
    filling gaps from each file that has the column."""
    csv_files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    lookup = None

    for path in csv_files:
        delim = detect_delimiter(path)
        df = pd.read_csv(path, sep=delim, engine="python",
                         encoding="utf-8-sig", on_bad_lines="skip")

        if "osm_way_id" not in df.columns:
            continue

        df["street_name"] = df["street_name"].astype(str).str.strip()
        df["osm_way_idx"] = normalize_idx(df["osm_way_idx"])
        df = df[KEY_COLS + ["osm_way_id"]].dropna(subset=["osm_way_id"])
        df = df.drop_duplicates(subset=KEY_COLS)

        if lookup is None:
            lookup = df
        else:
            # Only add rows whose key isn't already covered
            missing = ~df.set_index(KEY_COLS).index.isin(lookup.set_index(KEY_COLS).index)
            lookup = pd.concat([lookup, df[missing]], ignore_index=True)

    if lookup is not None:
        print(f"\nCollected osm_way_id for {len(lookup)} unique street segments across all files.")

    return lookup


def apply_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """Fill NaN values using per-column defaults defined in NAN_DEFAULTS."""
    for col, default in NAN_DEFAULTS.items():
        if col in df.columns:
            filled = df[col].isna().sum()
            if filled > 0:
                df[col] = df[col].fillna(default)
                print(f"  Filled {filled} NaN(s) in '{col}' with {default}")
    return df


def merge_all(folder: str) -> pd.DataFrame:
    csv_files = sorted(glob.glob(os.path.join(folder, "*.csv")))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in folder: '{folder}'")

    print(f"Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"  - {f}")

    merged = None

    for path in csv_files:
        df = load_csv(path)
        print(f"\nLoaded '{os.path.basename(path)}': {len(df)} rows, "
              f"columns: {[c for c in df.columns if c not in KEY_COLS]}")

        if merged is None:
            merged = df
        else:
            merged = pd.merge(merged, df, on=KEY_COLS, how="outer")

            if merged.duplicated(subset=KEY_COLS).any():
                merged = merged.groupby(KEY_COLS, as_index=False).first()

    return merged


def main():
    merged = merge_all(CSV_FOLDER)

    # Collect osm_way_id from all files and join it in
    osm_id_lookup = collect_osm_way_ids(CSV_FOLDER)
    if osm_id_lookup is not None:
        merged = pd.merge(merged, osm_id_lookup, on=KEY_COLS, how="left")

    print(f"\nApplying NaN defaults...")
    merged = apply_defaults(merged)

    # Column order: keys → osm_way_id → scores
    if "osm_way_id" in merged.columns:
        cols = KEY_COLS + ["osm_way_id"] + [c for c in merged.columns if c not in KEY_COLS + ["osm_way_id"]]
        merged = merged[cols]

    print(f"\nMerged result: {len(merged)} rows, {len(merged.columns)} columns")
    print(f"Columns: {list(merged.columns)}")

    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()