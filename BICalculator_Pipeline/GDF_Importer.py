import osmnx as ox

class StreetImporter:
    """
    Imports a street centerline from OSM by name or OSM way ID.
    """

    def __init__(self, street_name, city_name):
        self.street_name = street_name
        self.city_name   = city_name
        self.gdf         = None     # full OSM data — coords, tags, geometry

    def import_by_name(self):
        """
        Queries OSM for the street by name.
        Returns self.gdf for downstream use, or None if not found.
        """
        print(f"Querying OSM for '{self.street_name}' in {self.city_name}...")

        gdf = ox.features_from_place(self.city_name, tags={"name": self.street_name, "highway": True})
        gdf = gdf[gdf["name"] == self.street_name]

        if gdf.empty:
            print(f"Error: '{self.street_name}' not found in {self.city_name}")
            return None

        print(f"Found {len(gdf)} OSM way(s)")

        # Keep only line geometries (exclude points/polygons if any)
        gdf = gdf[gdf.geometry.geom_type == "LineString"]

        if gdf.empty:
            print("Error: No line geometry found")
            return None

        self.gdf = gdf
        return self.gdf

    def import_centerline(self):
        """
        Default import method — tries by name first,
        falls back to None if not found.
        For ID-based import use import_by_id().
        """
        return self.import_by_name()
