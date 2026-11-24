import pandas as pd
import geopandas as gpd
from OSM_pipeline.OSM_Criterias import OSMCriterias

# ============================================================
# PARAMETERS
# ============================================================
UTM_CRS   = "EPSG:32632"
WGS84_CRS = "EPSG:4326"
# ============================================================


class OSM_Score:
    """
    Calculates the BI scores for only one OSM segment of the street.
    Returns BI scores dict for each OSM of the street.
    """

    def __init__(self, segments_gdf, gdf, total_width, landuse_gdf, transit_gdf):
        self.segments_gdf = segments_gdf
        self.gdf          = gdf
        self.total_width  = total_width
        self.landuse_gdf  = landuse_gdf
        self.transit_gdf  = transit_gdf

    def _get_tag(self, row, tag):
        """Safely retrieves a tag value from a pandas Series row."""
        try:
            val = row[tag]
            if pd.isna(val):
                return None
            return val
        except (KeyError, TypeError):
            return None

    def run(self):
        """
        Runs OSM criteria calculation for the whole OSM segment of the street.
        """

        # ── Per-street criteria (read once from first OSM way) ────────────
        first_way = self.gdf.iloc[0]
        highway  = self._get_tag(first_way, "highway")
        surface  = self._get_tag(first_way, "surface")
        maxspeed = self._get_tag(first_way, "maxspeed")
        has_cycleway = self._check_bike_lanes(first_way)
        has_parking = self._check_parking(first_way)
        has_traffic_calming = self._check_traffic_calming(first_way)
        has_transit = self._check_transit(self.transit_gdf)

        street_scores = {
            "road_type":  OSMCriterias.road_type_criteria(highway, has_cycleway),
            "pavement":   OSMCriterias.pavement_criteria(surface),
            "road_width": OSMCriterias.road_width_criteria(self.total_width, highway, has_cycleway),
            "max_speed":  OSMCriterias.max_speed_criteria(maxspeed, has_cycleway),
            "landuse":    OSMCriterias.landuse_criteria(self.segments_gdf, self.landuse_gdf),
            "parking":      OSMCriterias.parking_criteria(has_parking, has_cycleway),
            "traffic_calming": OSMCriterias.traffic_calming_criteria(has_traffic_calming),
            "transit_facilities" : OSMCriterias.transit_facilities_criteria(has_transit)
        }
        
        return street_scores
    
    def _check_bike_lanes(self, row):
        POSITIVE_VALUES = {"yes", "separate", "lane", "exclusive", "advisory"}
        for tag in ["cycleway", "cycleway:left", "cycleway:right", "cycleway:both"]:
            val = self._get_tag(row, tag)
            if isinstance(val, str) and val.lower().strip() in POSITIVE_VALUES:
                return True
        return False

    def _check_parking(self, row):
        NEGATIVE_VALUES = {"yes"}
        for tag in ["parking:left", "parking:right", "parking:right", "parking:both"]:
            val = self._get_tag(row, tag)
            if isinstance(val, str) and val.lower().strip() in NEGATIVE_VALUES:
                return True
        return False

    def _check_traffic_calming(self, row):
        val = self._get_tag(row, "traffic_calming")
        return isinstance(val, str) and val.strip() != ""
    
    def _check_transit(self, transit_gdf):
        UTM_CRS       = "EPSG:32632"
        WGS84_CRS     = "EPSG:4326"
        BUFFER_RADIUS = 20

        transit_utm = transit_gdf.to_crs(UTM_CRS)

        for _, segment in self.segments_gdf.iterrows():
            centroid_gdf = gpd.GeoDataFrame(geometry=[segment.geometry.centroid], crs=WGS84_CRS)
            buffer       = centroid_gdf.to_crs(UTM_CRS).geometry.iloc[0].buffer(BUFFER_RADIUS)
            if not transit_utm[transit_utm.geometry.intersects(buffer)].empty:
                return True

        return False