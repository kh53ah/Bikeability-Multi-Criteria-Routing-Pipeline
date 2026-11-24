import requests
import math
import pandas as pd

# ============================================================
# PARAMETERS
# ============================================================
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"
MAX_SLOPE_PERCENT  = 6.0    # slopes above this get score 0.0
# ============================================================


class ElevationCalculator:
    """
    Elevation pipeline.
    Fetches elevation for all segment endpoints in bulk via a single
    Open-Elevation API POST request, finds the maximum slope across
    all segments, and calculates a slope score.
    """

    def __init__(self, segments_gdf):
        """
        Parameters
        ----------
        segments_gdf : GeoDataFrame — output of StreetSegmentsCreator.create_segments()
                       must have start_point and end_point columns (WGS84)
        """
        self.segments_gdf = segments_gdf

    def run(self):
        """
        Runs the elevation pipeline:
        1. Gets max slope across all segments
        2. Calculates slope score from max slope
        Returns dict {"slope": score}
        """
        max_slope = self.get_max_slope()
        score     = self.slope_criteria(max_slope)
        print(f"Max slope: {max_slope:.2f}% → score: {score:.4f}")
        return {"elevation_score": score}

    def get_max_slope(self):
        """
        Collects all coordinate points, sends a single batch POST request to the 
        Open-Elevation API, updates elevations, and calculates the max slope.
        """
        if self.segments_gdf.empty:
            return 0.0

        # 1. Build a unique list of coordinates to fetch to minimize payload
        # Each location payload item expects {"latitude": lat, "longitude": lon}
        locations = []
        for _, segment in self.segments_gdf.iterrows():
            start_pt = segment["start_point"]
            end_pt   = segment["end_point"]
            locations.append({"latitude": start_pt.y, "longitude": start_pt.x})
            locations.append({"latitude": end_pt.y, "longitude": end_pt.x})

        # 2. Fetch ALL elevations at once via POST
        elevations = self._fetch_elevations_batch(locations)

        # 3. Calculate slopes using the returned list (2 elevations per segment row)
        max_slope = 0.0
        
        for idx, (_, segment) in enumerate(self.segments_gdf.iterrows()):
            start_pt = segment["start_point"]
            end_pt   = segment["end_point"]

            segment_length = self._haversine(
                start_pt.y, start_pt.x,
                end_pt.y,   end_pt.x
            )

            if segment_length == 0:
                continue

            # Extrapolate indices from our sequential locations mapping
            elevation_start = elevations[idx * 2]
            elevation_end = elevations[(idx * 2) + 1]

            # Calculate slope percentage
            elevation_diff = abs(elevation_end - elevation_start)
            slope_percent  = (elevation_diff / segment_length) * 100
            
            if slope_percent > max_slope:
                max_slope = slope_percent

        return max_slope

    @staticmethod
    def slope_criteria(max_slope):
        raw = max((MAX_SLOPE_PERCENT - max_slope) / MAX_SLOPE_PERCENT, 0.0)
        return raw

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R       = 6371000
        phi1    = math.radians(lat1)
        phi2    = math.radians(lat2)
        dphi    = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a       = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _fetch_elevations_batch(self, locations):
        """
        Sends a single POST request containing all coordinates to the API.

        Returns
        -------
        list : flat list of elevation floats matching input order
        """
        payload = {"locations": locations}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        try:
            # Using POST for bulk payloads instead of a congested GET query string
            response = requests.post(
                OPEN_ELEVATION_URL,
                json=payload,
                headers=headers,
                timeout=30 # Bumped up slightly because larger payloads take a second to process
            )
            response.raise_for_status()
            
            # Extract elevation values in order
            results = response.json()["results"]
            return [item["elevation"] for item in results]

        except requests.exceptions.ConnectionError:
            raise RuntimeError("Open-Elevation API is unreachable. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise RuntimeError("Open-Elevation batch API timed out. Try a smaller slice of segments.")
        except Exception as e:
            raise RuntimeError(f"Open-Elevation API error: {e}")