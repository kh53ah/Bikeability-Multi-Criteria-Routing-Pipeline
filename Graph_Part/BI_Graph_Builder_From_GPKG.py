from math import inf
import os
import ast
import pandas as pd
import geopandas as gpd
import networkx as nx

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
GPKG_FILE   = os.path.join(SCRIPT_DIR, "final_Graph2.gpkg")   
CSV_FILE    = os.path.join(SCRIPT_DIR, "BI_results_with_Improvements_ew.csv") # TO BE CHANGED
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "final_Graph_I_ew.graphml") #TO BE CHANGED

BI_COLUMN   = "BI"

# Default cost assigned to custom edges (no BI score available)
DEFAULT_COST = 100.0   
DEFAULT_LENGTH = 999999.0

# ==============================================================================
# COST FUNCTION
# ==============================================================================
def compute_cost(bi: float) -> float:
    # If BI is 3.5, cost becomes 1 - 3.5 = -2.5 (Negative weight asset!)
    return 1.0 - bi   

# ==============================================================================
# 1. LOAD CSV → SEGMENT LOOKUP (BY OSM WAY ID)
# ==============================================================================
print(f"Loading {CSV_FILE}...")
df = pd.read_csv(CSV_FILE, low_memory=False)

segment_lookup = {}
for _, row in df.iterrows():
    if pd.isna(row.get("osm_way_id")):
        continue
    try:
        raw = str(row["osm_way_id"]).strip()
        # Handle tuple format strings like "(None, 12345)" or clean integers
        if raw.startswith("("):
            _, way_id = ast.literal_eval(raw)
        else:
            way_id = int(float(raw))
        
        # Store the entire row data indexed by the specific segment ID
        segment_lookup[int(way_id)] = row
    except (ValueError, SyntaxError, TypeError):
        continue

print(f"  {len(segment_lookup)} unique OSM way segments loaded from CSV.")

# ==============================================================================
# 2. LOAD GRAPH LAYERS FROM GPKG
# ==============================================================================
CUSTOM_NODE_OSMID = 1
print(f"Loading graph layers from {GPKG_FILE}...")
nodes_gdf = gpd.read_file(GPKG_FILE, layer="final_graph__nodes")
edges_gdf = gpd.read_file(GPKG_FILE, layer="final_graph__edges")

print(f"  {len(nodes_gdf)} nodes, {len(edges_gdf)} edges loaded.")

# Build coordinate → osmid lookup for resolving custom edge endpoints
coord_to_osmid = {}
for _, row in nodes_gdf.iterrows():
    if pd.notna(row["osmid"]):
        key = (round(row.geometry.x, 4), round(row.geometry.y, 4))
        coord_to_osmid[key] = int(row["osmid"])

# ==============================================================================
# 3. REBUILD NETWORKX GRAPH & APPLY EXACT SEGMENT SCORES
# ==============================================================================
print("Rebuilding NetworkX graph matching strict OSM IDs...")
G = nx.MultiDiGraph()
G.graph["crs"] = "EPSG:4326"

# Add nodes
for i, (_, row) in enumerate(nodes_gdf.iterrows()):
    node_id = int(row["osmid"]) if pd.notna(row["osmid"]) else CUSTOM_NODE_OSMID
    G.add_node(node_id, x=row.geometry.x, y=row.geometry.y)

# Add edges
custom_count  = 0
matched_count = 0

for _, row in edges_gdf.iterrows():
    # Resolve custom geometry endpoints if u or v is missing
    if pd.isna(row["u"]) or pd.isna(row["v"]):
        coords     = list(row.geometry.coords)
        start      = (round(coords[0][0], 4),  round(coords[0][1], 4))
        end        = (round(coords[-1][0], 4), round(coords[-1][1], 4))
        custom_pt  = (round(9.93771, 4), round(49.78895, 4))
        u = CUSTOM_NODE_OSMID if start == custom_pt else coord_to_osmid.get(start)
        v = CUSTOM_NODE_OSMID if end   == custom_pt else coord_to_osmid.get(end)
        if u is None or v is None:
            continue
    else:
        u = int(row["u"])
        v = int(row["v"])
    
    key = int(row["key"]) if pd.notna(row.get("key")) else 0
    length = float(row["length"]) if pd.notna(row.get("length")) else 1.0

    # Clean the edge's OSM Way ID from GeoPackage to match it with the CSV
    gpkg_osm_id = None
    if pd.notna(row.get("osmid")):
        try:
            # Strip array formatting if present in string, e.g., '[12345]'
            raw_id = str(row["osmid"]).replace("[", "").replace("]", "")
            gpkg_osm_id = int(float(raw_id.split(",")[0])) # Take first if it's a list
        except (ValueError, TypeError):
            gpkg_osm_id = None

    # --- Match edge to our unique CSV segment calculation ---
    if gpkg_osm_id in segment_lookup:
        csv_row  = segment_lookup[gpkg_osm_id]
        bi_score = float(csv_row["BI"])
        cost     = compute_cost(bi_score)
        matched_count += 1
    else:
        # Custom edges or unmapped links fall back safely here
        bi_score = None
        cost     = DEFAULT_COST
        length   = DEFAULT_LENGTH
        custom_count += 1

    def clean(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        return val

    G.add_edge(u, v, key=int(key),
               osmid       = clean(row.get("osmid")),
               highway     = clean(row.get("highway")),
               name        = clean(row.get("name")),
               length      = length,
               bi_score    = bi_score if bi_score is not None else "",
               cost        = cost,
               street_name = clean(row.get("street_name")))

print(f"  {matched_count} unique segments matched to CSV. {custom_count} custom edges handled.")

# ==============================================================================
# 4. SAVE AS GRAPHML
# ==============================================================================
nx.write_graphml(G, OUTPUT_PATH)
print(f"\nSaved GraphML → {OUTPUT_PATH}")