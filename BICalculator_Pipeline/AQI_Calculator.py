import requests

# ============================================================
# PARAMETERS
# ============================================================
WAQI_URL           = "https://api.waqi.info/feed"
WAQI_TOKEN         = "523fb05916124a16f43c2df40ee17eb890605598"
# ============================================================


class AQICalculator:
    """
    Air Quality Index pipeline.
    Fetches AQI for the street location via the WAQI API,
    calculates a score and returns {"aqi": score}.
    AQI is a single value for the whole street — not per segment.
    """

    def __init__(self, lat, lon):
        """
        Parameters
        ----------
        lat : float — latitude of the street (centroid or first segment)
        lon : float — longitude of the street
        """
        self.lat = lat
        self.lon = lon

    def run(self):
        """
        Fetches AQI and calculates score.

        Returns
        -------
        dict : {"aqi": score}

        Raises
        ------
        RuntimeError : if WAQI API is unreachable or returns an error
        """
        aqi   = self.get_aqi()
        score = self.aqi_criteria(aqi)
        print(f"AQI: {aqi} → score: {score:.4f}")
        return {"aqi_score": score}

    def get_aqi(self):
        """
        Fetches AQI value for the given coordinates from WAQI API.

        Returns
        -------
        float : AQI value

        Raises
        ------
        RuntimeError : if API is unreachable or returns an error
        """
        url = f"{WAQI_URL}/geo:{self.lat};{self.lon}/"

        try:
            response = requests.get(
                url,
                params={"token": WAQI_TOKEN},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data["status"] != "ok":
                raise RuntimeError(f"WAQI API error: {data.get('data', 'Unknown error')}")

            return float(data["data"]["aqi"])

        except requests.exceptions.ConnectionError:
            raise RuntimeError("WAQI API is unreachable. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise RuntimeError("WAQI API timed out.")
        except Exception as e:
            raise RuntimeError(f"WAQI API error: {e}")

    @staticmethod
    def aqi_criteria(aqi):
        """
        Calculates AQI score.
        Scale: (100 - AQI) / 100, capped at 0.0 for AQI above 100.
        Lower AQI → higher score (better air quality).

        Parameters
        ----------
        aqi : float — AQI value (0–100)

        Returns
        -------
        float : AQI score
        """
        raw = max((100 - aqi) / 100, 0.0)
        return raw