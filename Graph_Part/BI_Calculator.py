import pandas as pd
import numpy as np

# =============================================================================
# WEIGHTS CONFIGURATION
# BI = sum(weight_i * score_i)  —  adjust values as needed
# =============================================================================

WEIGHTS = {
    "aqi_score": 0.052632,
    "distance": 0.052632,
    "elevation_score": 0.052632,
    "Vegetation": 0.052632,
    "congestion_score": 0.052632,
    "road_width": 0.052632,
    "road_type": 0.052632,
    "max_speed": 0.052632,
    "pavement": 0.052632,
    "landuse": 0.052632,
    "parking": 0.052632,
    "Building": 0.052632,
    "Utility Pole": 0.052632,
    "transit_facilities": 0.052632,
    "Traffic Sign": 0.052632,
    "Traffic Light": 0.052632,
    "Crosswalk": 0.052632,
    "Curb Cut": 0.052632,
    "Catch Basin": 0.052632,
}

# =============================================================================
# PATHS
# =============================================================================

INPUT_CSV  = "C:\\Studium\\SS26\\Abschlussarbeit\\Abschlussarbeit\\Graph_Part\\Criteria_scores_with_length.csv"
OUTPUT_CSV = "C:\\Studium\\SS26\\Abschlussarbeit\\Abschlussarbeit\\Graph_Part\\BI_results_Equal_Weights.csv" #TO BE CHANGED

# =============================================================================
# CALCULATION
# =============================================================================

def calculate_bi(input_path: str, output_path: str, weights: dict) -> None:
    df = pd.read_csv(input_path)

    # -------------------------------------------------------------------------
    # Merge: Traffic Sign (Back) + Traffic Sign (Front) + Traffic Sign Frame
    #        → Traffic Sign = 1 if any of the three equals 1, else 0
    # -------------------------------------------------------------------------
    traffic_sign_cols = ["Traffic Sign (Back)", "Traffic Sign (Front)", "Traffic Sign Frame"]
    missing_ts = [c for c in traffic_sign_cols if c not in df.columns]
    if missing_ts:
        raise ValueError(f"Expected traffic sign columns not found: {missing_ts}")
    df["Traffic Sign"] = (df[traffic_sign_cols].eq(1).any(axis=1)).astype(int)
    df.drop(columns=traffic_sign_cols, inplace=True)

    # -------------------------------------------------------------------------
    # Merge: Lane Marking - Crosswalk + Crosswalk - Plain
    #        → Crosswalk = 1 if any of the two equals 1, else 0
    # -------------------------------------------------------------------------
    crosswalk_cols = ["Lane Marking - Crosswalk", "Crosswalk - Plain"]
    missing_cw = [c for c in crosswalk_cols if c not in df.columns]
    if missing_cw:
        raise ValueError(f"Expected crosswalk columns not found: {missing_cw}")
    df["Crosswalk"] = (df[crosswalk_cols].eq(1).any(axis=1)).astype(int)
    df.drop(columns=crosswalk_cols, inplace=True)

    # -------------------------------------------------------------------------
    # Verify all weight keys are present as columns after merging
    # -------------------------------------------------------------------------
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