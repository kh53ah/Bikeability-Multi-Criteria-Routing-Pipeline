import json
import os
import osmnx as ox
import geopandas as gpd
from GDF_Importer import StreetImporter
from StreetWidth_Calculator import StreetWidthCalculator
from StreetSegments_Creator import StreetSegmentsCreator
from SVI_pipeline.Run_SVI_Calculations import RoadSegmentation
from OSM_pipeline.OSM_Criterias_Calculator import OSM_Score
from Elevation_Calculator import ElevationCalculator
from Congestion_Calculator import CongestionCalculator
from AQI_Calculator import AQICalculator
from Results.BI_Results_AQI import BI_Results_AQI
from Results.BI_Results_Congestion import BI_Results_Congestion
from Results.BI_Results_Elevation import BI_Results_Elevation
from Results.BI_Results_OSM import BI_Results_OSM
from Results.BI_Results_SVI import BI_Results_SVI

# PARAMETERS
STREETS_FILE = os.path.join(os.path.dirname(__file__), "Streets_list.json")
CITY_NAME = "Würzburg, Germany"


def load_streets(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(street_name, city_name):
    print("\n" + "=" * 60)
    print(f"PROCESSING: {street_name}, {city_name}")
    print("=" * 60)

    # ── STEP 1 — Import street from OSM ──────────────────────
    print("\nSTEP 1 — Importing street from OSM")
    importer = StreetImporter(street_name, city_name)
    gdf = importer.import_by_name()

    if gdf is None:
        print(f"Step 1 failed — '{street_name}' not found. Skipping.")
        return
    print(f"Step 1 complete. {len(gdf)} OSM ways imported.")

    # ── STEP 2 — Calculate street width (once for whole street) ──
    print("\nSTEP 2 — Calculating street width")
    width_calc = StreetWidthCalculator(gdf)
    street_width = width_calc.calculate()
    print(f"Step 2 complete. Street width: {street_width:.2f} m")
    
    # ── STEP 3 — Loop over each OSM way ──────────────────────
    
    print(f"\nSTEP 3 — Processing {len(gdf)} OSM way(s) individually")

    for osm_way_idx, (way_id, way_row) in enumerate(gdf.iterrows()):
        print(f"\n  OSM way {osm_way_idx + 1}/{len(gdf)} — ID: {way_id}")

        # Wrap the single row back into a one-row GeoDataFrame
        way_gdf = gpd.GeoDataFrame([way_row], geometry="geometry", crs=gdf.crs)

        # ── STEP 3a — Create sub-segments for this OSM way ───
        segments_creator = StreetSegmentsCreator(way_gdf, street_width)
        segments_gdf = segments_creator.create_segments()

        if segments_gdf is None or segments_gdf.empty:
            print(f"  No segments created for way {way_id}. Skipping.")
            continue

        way_scores = {}

        # ── STEP 4 — OSM Pipeline ────────────────────────────
        """
        try:
            osm_scores = OSM_Score(segments_gdf, way_gdf, street_width, landuse_gdf, transit_gdf).run()
            if osm_scores:
                way_scores.update(osm_scores)
            print(f"  OSM complete.")
        except Exception as e:
            print(f"  OSM failed — {e}")
        
        # ── STEP 5 — SVI Pipeline ────────────────────────────
        
        svi_export_scores = {}
        try:
            svi_scores, svi_count = RoadSegmentation(segments_gdf).run()
            if svi_scores and svi_count > 0:
                svi_export_scores = {k: v / svi_count for k, v in svi_scores.items()}
                way_scores.update(svi_export_scores)
            print(f"  SVI complete. {svi_count} sub-segments scored.")
        except Exception as e:
            print(f"  SVI failed — {e}")
        
        # ── STEP 6 — Elevation Pipeline ──────────────────────
        
        elevation_scores = {}
        try:
            elevation_scores = ElevationCalculator(segments_gdf).run()
            way_scores.update(elevation_scores)
            print("  Elevation complete.")
        except RuntimeError as e:
            print(f"  Elevation failed — {e}")
        
        # ── STEP 7 — Congestion Pipeline ─────────────────────
        """
        congestion_scores = {}
        try:
        
            congestion_scores = CongestionCalculator(segments_gdf).run()
            way_scores.update(congestion_scores)
            print("  Congestion complete.")
        except RuntimeError as e:
            print(f"  Congestion failed — {e}")
        """
        
        # ── STEP 9 — Export this OSM way's scores to CSV ─────
        if svi_export_scores:
            BI_Results_SVI.export(street_name, way_id, osm_way_idx, svi_export_scores)
        else:
            print(f"  No SVI scores collected for way {way_id}. Skipping SVI export.")
        if osm_scores:
            BI_Results_OSM.export(street_name, way_id, osm_way_idx, osm_scores)
        else:
            print(f"  No OSM scores collected for way {way_id}. Skipping OSM export.")
        
        if elevation_scores:
            BI_Results_Elevation.export(street_name, way_id, osm_way_idx, elevation_scores)
        else:
            print(f"  No Elevation scores collected for way {way_id}. Skipping Elevation export.")
                """

        if congestion_scores:
            BI_Results_Congestion.export(street_name, way_id, osm_way_idx, congestion_scores)
        else:
            print(f"  No Congestion scores collected for way {way_id}. Skipping Congestion export.")

    # ── STEP 8 — AQI Pipeline ────────────────────────────
    
    try:
        first_centroid = segments_gdf.iloc[0].geometry.centroid
        aqi_scores = AQICalculator(first_centroid.y, first_centroid.x).run()
        way_scores.update(aqi_scores)
        BI_Results_AQI.export(street_name, way_id, osm_way_idx, aqi_scores)
        print("  AQI complete.")
    except RuntimeError as e:
        print(f"  AQI failed — {e}")
    

    print(f"\nFinished processing all OSM ways for '{street_name}'.")
    


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 0 — Loading streets list")
    print("=" * 60)
    streets = load_streets(STREETS_FILE)
    print(f"Step 0 complete. {len(streets)} streets loaded.\n")

    landuse_gdf = ox.features_from_place(CITY_NAME, tags={"landuse": True})
    transit_gdf = ox.features_from_place(CITY_NAME, tags={"public_transport": True})

    for street in streets:
        run_pipeline(street, CITY_NAME)

    print("\n" + "=" * 60)
    print("ALL STREETS PROCESSED")
    print("=" * 60)