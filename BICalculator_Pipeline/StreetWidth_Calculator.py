import pandas as pd

# PARAMETERS in meters
DEFAULT_LANE_WIDTH      = 3.25
DEFAULT_BIKE_LANE_WIDTH = 1.25

HIGHWAY_WIDTH_DEFAULTS = {
    "motorway":      9.75,  # 3 lanes × 3.25m
    "primary":        6.50,   # 2 lanes × 3.25m
    "secondary":      6.50,   # 2 lanes × 3.25m
    "tertiary":       6.50,   # 2 lanes × 3.25m
    "residential":    3.25,   # 1 lane  × 3.25m
    "living_street":  3.25,   # 1 lane  × 3.25m
    "cycleway":       1.25,  # bike only
    "footway":        2.5,
    "path":           2.5,
}

class StreetWidthCalculator:

    def __init__(self, gdf):

        self.gdf            = gdf
        self.street_width   = None   # carriageway width (meters)

    def calculate(self):
        """
        Runs the width cascade and computes total bbox width W.
        Returns (street_width, total_width).
        """
        self.street_width = self._extract_width()

        return self.street_width

    def _extract_width(self):
        """
        Extracts carriageway width using the following priority:
          1. Explicit 'width' tag from OSM
          2. 'lanes' * DEFAULT_LANE_WIDTH  +  bike lane if cycleway exists
          3. 'highway' type standard value  +  bike lane if cycleway exists
        """
        for _, row in self.gdf.iterrows():

            # Priority 1: explicit width tag
            if "width" in row and pd.notna(row["width"]):
                return float(row["width"])

            # Priority 2: lanes tag
            if "lanes" in row and pd.notna(row["lanes"]):
                lanes = int(row["lanes"])
                return lanes * DEFAULT_LANE_WIDTH + self._bike_lane_addition(row) #adding only one bike lane to be safe

            # Priority 3: highway type fallback
            if "highway" in row and row["highway"] is not None:
                highway = row["highway"]
                if isinstance(highway, list):
                    highway = highway[0]
                if highway in HIGHWAY_WIDTH_DEFAULTS:
                    return HIGHWAY_WIDTH_DEFAULTS[highway] * 2 + self._bike_lane_addition(row)
                
        return 5.0 # default for a one way street with a parking lane

    def _bike_lane_addition(self, row):
        """Returns total bike lane width (both sides) if cycleway tag is present."""
        cycleway = row.get("cycleway", None)
        if cycleway is not None and str(cycleway).lower() not in ("no", "none", "nan"):
            return DEFAULT_BIKE_LANE_WIDTH
        return 0.0