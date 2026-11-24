import pandas as pd
import numpy as np
import os

# =============================================================================
# WEIGHTS CONFIGURATION
# BI = sum(weight_i * score_i)  —  adjust values as needed
# =============================================================================

WEIGHTS = {
    # --- Environment ---
    "aqi_score":                    1.0,
    "elevation_score":              1.0,

    # --- Traffic & Road ---
    "congestion_score":             1.0,
    "road_type":                    1.0,
    "pavement":                     1.0,
    "road_width":                   1.0,
    "max_speed":                    1.0,

    # --- Land Use & Infrastructure ---
    "landuse":                      1.0,
    "parking":                      1.0,
    "transit_facilities":           1.0,

    # --- SVI: Scene Elements ---
    "Vegetation":                   1.0,
    "Building":                     1.0,

    # --- SVI: Safety & Accessibility Features ---
    "Traffic Sign (Back)":          1.0,
    "Catch Basin":                  1.0,
    "Traffic Light":                1.0,
    "Lane Marking - Crosswalk":     1.0,
    "Utility Pole":                 1.0,
    "Crosswalk - Plain":            1.0,
    "Traffic Sign (Front)":         1.0,
    "Curb Cut":                     1.0,
    "Traffic Sign Frame":           1.0,
}

# =============================================================================
# PATHS
# =============================================================================

INPUT_CSV  = "C:\Studium\SS26\Abschlussarbeit\Abschlussarbeit\Criteria_scores.csv"
OUTPUT_CSV = "BI_results.csv"

# =============================================================================
# CALCULATION
# =============================================================================

def calculate_bi(input_path: str, output_path: str, weights: dict) -> None:
    df = pd.read_csv(input_path)

    # Verify all weight keys exist as columns
    missing = [col for col in weights if col not in df.columns]
    if missing:
        raise ValueError(f"The following weight keys were not found as columns in the CSV:\n  {missing}")

    criteria_cols = list(weights.keys())
    weight_values = np.array([weights[col] for col in criteria_cols])

    # Fill missing SVI values with 0 (streets with no imagery)
    scores = df[criteria_cols].fillna(0.0).to_numpy(dtype=float)

    # BI = sum(weight_i * score_i)
    df["BI"] = np.round(scores @ weight_values, 4)

    df.to_csv(output_path, index=False)
    print(f"Done. {len(df)} rows written to: {output_path}")


if __name__ == "__main__":
    calculate_bi(INPUT_CSV, OUTPUT_CSV, WEIGHTS)