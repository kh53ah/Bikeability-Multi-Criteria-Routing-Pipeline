import pandas as pd
import numpy as np

# =============================================================================
# WEIGHTS CONFIGURATION
# =============================================================================

WEIGHTS = {
    # --- Environment ---
    "aqi_score":                    0.053,
    "distance":                     0.053,
    "elevation_score":              0.053,
    "Vegetation":                   0.053,

    # --- Traffic & Road ---
    "congestion_score":             0.053,
    "road_width":                   0.053,
    "road_type":                    0.053,
    "max_speed":                    0.053,

    # --- Land Use & Infrastructure ---
    "pavement":                     0.053,
    "landuse":                      0.053,
    "parking":                      0.053,
    "Building":                     0.053,
    "Utility Pole":                 0.053,

    # --- Traffic Control & Micro-Infrastructure ---
    "transit_facilities":           0.053,
    "Traffic Sign":                 0.053,
    "Traffic Light":                0.053,
    "Crosswalk":                    0.053,
    "Curb Cut":                     0.053,
    "Catch Basin":                  0.053,
}

# =============================================================================
# STREET-SPECIFIC OVERRIDES
# Streets in OVERRIDE_STREETS will use OVERRIDE_VALUE for every criterion
# listed in OVERRIDE_CRITERIA instead of their real CSV scores.
# All other streets are calculated normally.
# =============================================================================

OVERRIDE_STREETS  = [
    "Salvatorstraße",
    "Mönchbergstraße",

    "Simon-Breu-Straße",
    "Albert-Hoffa-Straße",

    "Rosa-Buchbinder-Straße",
    "Walther-von-der-Vogelweide-Straße",
    "Keesburgstraße",
    "Schellingstraße",
    "Ebertsklinge"
]

OVERRIDE_CRITERIA = [
    "road_type",
    "max_speed",
    "parking",
    "road_width"
]

OVERRIDE_VALUE = 1.0

# =============================================================================
# PATHS
# =============================================================================

INPUT_CSV  = "C:\\Studium\\SS26\\Abschlussarbeit\\Abschlussarbeit\\Graph_Part\\Criteria_scores_with_length.csv"
OUTPUT_CSV = "C:\\Studium\\SS26\\Abschlussarbeit\\Abschlussarbeit\\Graph_Part\\BI_results_with_Improvements_ew.csv"

STREET_NAME_COLUMN = "street_name"

# =============================================================================
# CALCULATION
# =============================================================================

def calculate_bi(input_path, output_path, weights,
                 override_streets, override_criteria, override_value):
    df = pd.read_csv(input_path)

    # Merge Traffic Sign columns
    traffic_sign_cols = ["Traffic Sign (Back)", "Traffic Sign (Front)", "Traffic Sign Frame"]
    missing_ts = [c for c in traffic_sign_cols if c not in df.columns]
    if missing_ts:
        raise ValueError(f"Expected traffic sign columns not found: {missing_ts}")
    df["Traffic Sign"] = (df[traffic_sign_cols].eq(1).any(axis=1)).astype(int)
    df.drop(columns=traffic_sign_cols, inplace=True)

    # Merge Crosswalk columns
    crosswalk_cols = ["Lane Marking - Crosswalk", "Crosswalk - Plain"]
    missing_cw = [c for c in crosswalk_cols if c not in df.columns]
    if missing_cw:
        raise ValueError(f"Expected crosswalk columns not found: {missing_cw}")
    df["Crosswalk"] = (df[crosswalk_cols].eq(1).any(axis=1)).astype(int)
    df.drop(columns=crosswalk_cols, inplace=True)

    # Apply overrides to specific streets only
    if override_streets and override_criteria:
        if STREET_NAME_COLUMN not in df.columns:
            raise ValueError(f"Column '{STREET_NAME_COLUMN}' not found in CSV.")

        mask = df[STREET_NAME_COLUMN].isin(override_streets)
        matched_streets = df.loc[mask, STREET_NAME_COLUMN].unique().tolist()
        not_found = [s for s in override_streets if s not in matched_streets]

        if not_found:
            print(f"  [WARNING] Streets not found in CSV: {not_found}")

        for col in override_criteria:
            if col not in df.columns:
                df[col] = np.nan
            df.loc[mask, col] = override_value

        print(f"  [OVERRIDE] {len(matched_streets)} streets × "
              f"{len(override_criteria)} criteria set to {override_value}")
        print(f"    Streets:  {matched_streets}")
        print(f"    Criteria: {override_criteria}")

    # Verify all weight keys exist
    missing = [col for col in weights if col not in df.columns]
    if missing:
        raise ValueError(f"Weight keys not found as columns:\n  {missing}")

    criteria_cols = list(weights.keys())
    weight_values = np.array([weights[col] for col in criteria_cols])
    scores = df[criteria_cols].fillna(0.0).to_numpy(dtype=float)

    df["BI"] = np.round(scores @ weight_values, 4)

    df.to_csv(output_path, index=False)
    print(f"\nDone. {len(df)} rows written to: {output_path}")


if __name__ == "__main__":
    calculate_bi(INPUT_CSV, OUTPUT_CSV, WEIGHTS,
                 OVERRIDE_STREETS, OVERRIDE_CRITERIA, OVERRIDE_VALUE)