import math

import geopandas as gpd

class OSMCriterias:
    """
    Contains all OSM-based criteria functions for the Bikeability Index.
    Each function reads the relevant OSM tag(s) and the score.
    """
    Segment_length = 20
    Buffer_distance = Segment_length / 2

    @staticmethod
    def road_type_criteria(highway, has_cycleway):
        """
        Type of road — based on OSM highway tag.
        Scale: lookup table (see ROAD_TYPE_SCORES).
        """
        ROAD_TYPE_SCORES = {
            # 0.0 for steps,
            # 0.6 for streets of max speed = 30km/h
            # 0.8 for streets shared with pedestrians,
            #  1.0 for cycleways, regardless of max speed.

            "steps":            0.0,

            "motorway":         0.2,
            "motorway_link":    0.2,
            "trunk":            0.2,
            "trunk_link":       0.2,
            "primary":          0.2,
            "primary_link":     0.2,

            "secondary":        0.3,
            "secondary_link":   0.3,
            "tertiary":         0.4,
            "tertiary_link":    0.4,

            "unclassified":     0.6, 
            "residential":      0.6,

            "footway":          0.8,
            "living_street":    0.8,    
            "pedestrian":       0.8,
            "service":          0.8,
            "track":            0.8,
            "cycleway":         1.0,
            }

        if has_cycleway:
            return 1.0

        if highway is None or not isinstance(highway, str):
            return 0.0

        return ROAD_TYPE_SCORES.get(highway.lower().strip(), 0.0)

    @staticmethod
    def pavement_criteria(surface):
        """
        Type of pavement — based on OSM surface tag.
        Returns 0.0 for unknown/unlisted surface types.
        """
        PAVEMENT_SCORES = {
            "unhewn_cobblestone": 0.2,
            "cobblestone":        0.2,
            "sett":               0.4,
            "metal":              0.4,
            "wood":               0.4,
            "paved":              1.0,
            "concrete:lanes":     1.0,
            "concrete:plates":    1.0,
            "paving_stones":      1.0,
            "asphalt":            1.0,
            "concrete":           1.0,
        }
        
        if surface is None or not isinstance(surface, str):
            return 0.0
        
        return PAVEMENT_SCORES.get(surface.lower().strip(), 0.0)

    @staticmethod
    def max_speed_criteria(maxspeed, has_cycleway):
        """
        Vehicles' speed — based on OSM maxspeed tag.
        Scale: (50 - maxspeed) / 50, capped at 0 for speeds above 50.
        Lower speed → higher score.
        """
        DEFAULT_SPEEDS = {
            "footway":          0,
            "living_street":    0,    
            "pedestrian":       0,
            "service":          0,
            "track":            0,
            "cycleway":         0,

            "residential":   30,
            "living_street": 30,
            "pedestrian":    10,
            "tertiary":      50,
            "unclassified":  50,
            "secondary":     70,
            "primary":       100,
        }

        if has_cycleway:
            return 1.0

        if not maxspeed or not isinstance(maxspeed, str):
            return 0.4 #assuming that it is a small street without a maxspeed tag

        try:
            speed = float(maxspeed.strip())
        except ValueError:
            speed = DEFAULT_SPEEDS.get(maxspeed.lower().strip())
            if speed is None:
                return 0.4 #assuming that it is a small street without a maxspeed tag

        return max((50 - speed) / 50, 0.0)

    @staticmethod
    def parking_criteria(has_parking, has_cycleway):
        """
        Presence of on-street parking — 1 if not present, 0 if present.
        """
        
        if has_cycleway:
            return 1.0

        if has_parking:
            return 0.0

        return 1.0
    
    @staticmethod
    def traffic_calming_criteria(has_traffic_calming):
        """
        No. of speed control devices — 1 if present, 0 if not present.
        """
        if has_traffic_calming:
            return 1.0
        return 0.0
    
    @staticmethod
    def transit_facilities_criteria(has_transit):
        """
        No. of transit facilities — 1 if present, 0 if not present.
        """
        if has_transit:
            return 1.0
        return 0.0
    
    @staticmethod
    def road_width_criteria(total_width, highway, has_cycleway):
        """
        Road width — based on total street cross section width.
        Scale: min(total_width / 10, 1.0) — capped at 1.0 for widths >= 10m.
        Wider street = better score.
        """
        NON_VEHICLE_TYPES = {
            "service", "footway", "steps", "pedestrian", "cycleway"
        }

        if has_cycleway:
            return 1.0

        if isinstance(highway, str) and highway.lower().strip() in NON_VEHICLE_TYPES:
            return 1.0

        width_without_sidewalk = math.fabs(total_width - 2 * 2.5)

        return min(width_without_sidewalk / 13, 1.0)
 
    @staticmethod
    def landuse_criteria(segments_gdf, landuse_gdf):
        """
        Preferred landuse check — binary street-level score.
        Returns 1 if any segment along the street passes through
        a preferred landuse type (green areas, commercial, retail).
        Returns 0 if no preferred landuse found along the whole street.
 
        Preferred types: grass, forest, park, meadow, village_green,
        recreation_ground, commercial, retail, allotments.
        """

        PREFERRED_LANDUSE = {
            "commercial", "retail", "allotments"
        }
        UTM_CRS   = "EPSG:32632"
        WGS84_CRS = "EPSG:4326"
 
        landuse_utm = landuse_gdf.to_crs(UTM_CRS)
        preferred   = landuse_utm[landuse_utm["landuse"].isin(PREFERRED_LANDUSE)]
        
        for _, segment in segments_gdf.iterrows():
            centroid_gdf = gpd.GeoDataFrame(geometry=[segment.geometry.centroid], crs=WGS84_CRS)
            buffer       = centroid_gdf.to_crs(UTM_CRS).geometry.iloc[0].buffer(OSMCriterias.Segment_length / 2 + OSMCriterias.Buffer_distance)
            if not preferred[preferred.geometry.intersects(buffer)].empty:
                return 1.0
 
        return 0.0