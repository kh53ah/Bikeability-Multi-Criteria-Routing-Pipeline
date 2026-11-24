import requests

# ============================================================
# PARAMETERS
# ============================================================
TOMTOM_URL              = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
TOMTOM_API_KEY          = "wNH7P3hO4Eer2U8gRqHsfYUyqxhuxUha"
# ============================================================


class CongestionCalculator:
    """
    Congestion pipeline.
    Fetches typical traffic flow data per segment via TomTom Flow API,
    finds the worst (highest congestion) segment, and calculates a score.
    Follows the same pattern as ElevationCalculator.
    """

    def __init__(self, segments_gdf):
        """
        Parameters
        ----------
        segments_gdf : GeoDataFrame — output of StreetSegmentsCreator.create_segments()
        """
        self.segments_gdf = segments_gdf

    def run(self):
        """
        Runs the congestion pipeline:
        1. Gets max congestion across all segments
        2. Calculates congestion score from max congestion
        Returns dict {"congestion": score}
        """
        max_congestion = self.get_max_congestion()
        score= self.congestion_criteria(max_congestion)
        print(f"Max congestion: {max_congestion:.4f} → score: {score:.4f}")
        return {"congestion_score": score}

    def get_max_congestion(self):
        """
        Loops through all segments, fetches traffic flow for each segment
        centroid, calculates congestion index, and returns the maximum
        congestion value found across all segments.

        Congestion index = 1 - (currentSpeed / freeFlowSpeed)
        0 = no congestion, 1 = full congestion

        Returns
        -------
        float : maximum congestion index across all segments

        Raises
        ------
        RuntimeError : if TomTom API is unreachable or returns an error
        """
        max_congestion = 0.0

        for idx, segment in self.segments_gdf.iterrows():
            print(f"Fetching congestion for segment {idx + 1}/{len(self.segments_gdf)}...")

            centroid = segment.geometry.centroid
            lat      = centroid.y
            lon      = centroid.x

            current_speed, free_flow_speed = self._fetch_traffic(lat, lon)

            if free_flow_speed == 0:
                continue

            congestion = 1 - (current_speed / free_flow_speed)
            congestion = max(congestion, 0.0)  # cap at 0 if current > freeflow

            if congestion > max_congestion:
                max_congestion = congestion

        return max_congestion

    def _fetch_traffic(self, lat, lon):
        """
        Fetches typical traffic flow data for a given coordinate.

        Parameters
        ----------
        lat : float — latitude
        lon : float — longitude

        Returns
        -------
        tuple : (currentSpeed, freeFlowSpeed) in km/h

        Raises
        ------
        RuntimeError : if API is unreachable or returns an error
        """
        try:
            response = requests.get(
                TOMTOM_URL,
                params={
                    "point": f"{lat},{lon}",
                    "key":   TOMTOM_API_KEY
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()["flowSegmentData"]
            return float(data["currentSpeed"]), float(data["freeFlowSpeed"])

        except requests.exceptions.ConnectionError:
            raise RuntimeError("TomTom API is unreachable. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise RuntimeError("TomTom API timed out.")
        except Exception as e:
            raise RuntimeError(f"TomTom API error: {e}")

    @staticmethod
    def congestion_criteria(max_congestion):
        """
        Calculates congestion score from max congestion index.
        Scale: 1 - max_congestion (inverted — lower congestion = higher score).

        Parameters
        ----------
        max_congestion : float — max congestion index (0–1)

        Returns
        -------
        float : congestion score
        """
        raw = 1.0 - max_congestion
        return raw