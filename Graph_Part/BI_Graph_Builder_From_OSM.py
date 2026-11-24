import ast
import pandas as pd
import osmnx as ox

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CONFIG = {
    "csv_file":   r"C:\Studium\SS26\Abschlussarbeit\Abschlussarbeit\Graph_Part\BI_results_with_length.csv",        # <-- Update path as needed
    "location":   "Würzburg, Germany",
    "output_dir": r"C:\Studium\SS26\Abschlussarbeit\Abschlussarbeit\Graph_Part",                      # <-- Where to save outputs

    # Edge weight: "bi_score" = raw BI (higher = better bike street)
    # For Dijkstra (finds lowest cost), we store 1/BI as "cost" as well
    "weight_column": "BI",
}

# ==============================================================================
# 1. LOAD CSV → OSM ID LOOKUP
# ==============================================================================
print(f"Loading {CONFIG['csv_file']}...")
df = pd.read_csv(CONFIG["csv_file"], low_memory=False)

# Build lookup: osm_way_id (int) → full row data
way_lookup = {}
for _, row in df.iterrows():
    try:
        raw = str(row["osm_way_id"])
        _, way_id = ast.literal_eval(raw) if raw.startswith("(") else (None, int(raw))
        way_lookup[int(way_id)] = row
    except (ValueError, SyntaxError):
        continue

print(f"  {len(way_lookup)} way segments loaded.")

# ==============================================================================
# 2. DOWNLOAD OSM NETWORK
# ==============================================================================
print(f"Downloading road network for {CONFIG['location']}...")
G_full = ox.graph_from_place(CONFIG["location"], network_type="all")

# ==============================================================================
# 3. FILTER TO MATCHED EDGES ONLY
# ==============================================================================
print("Matching CSV segments to OSM edges...")
edges_to_keep = []
for u, v, key, data in G_full.edges(keys=True, data=True):
    osm_ids = data.get("osmid", [])
    if not isinstance(osm_ids, list):
        osm_ids = [osm_ids]
    if any(int(oid) in way_lookup for oid in osm_ids):
        edges_to_keep.append((u, v, key))

if not edges_to_keep:
    raise ValueError("No matching OSM IDs found between CSV and downloaded graph.")

G = G_full.edge_subgraph(edges_to_keep).copy()
isolated = [n for n, deg in dict(G.degree()).items() if deg == 0]
G.remove_nodes_from(isolated)
print(f"  {G.number_of_edges()} edges, {G.number_of_nodes()} nodes kept.")

# ==============================================================================
# 4. INJECT BI ATTRIBUTES INTO EVERY EDGE
# ==============================================================================
# Stored per edge:
#   bi_score   → raw BI value (higher = more bikeable)
#   cost       → 1 / BI  (lower = more bikeable, used for Dijkstra)
#   street_name → human-readable name from your CSV

print("Injecting BI scores into graph edges...")
unmatched = 0
for u, v, key, data in G.edges(keys=True, data=True):
    osm_ids = data.get("osmid", [])
    if not isinstance(osm_ids, list):
        osm_ids = [osm_ids]

    matched_row = None
    for oid in osm_ids:
        if int(oid) in way_lookup:
            matched_row = way_lookup[int(oid)]
            break

    if matched_row is not None:
        bi = float(matched_row[CONFIG["weight_column"]])
        G[u][v][key]["bi_score"]    = bi
        G[u][v][key]["cost"]        = 1.0 / bi if bi > 0 else float("inf")
        G[u][v][key]["street_name"] = str(matched_row["street_name"])
    else:
        unmatched += 1

if unmatched:
    print(f"  Warning: {unmatched} edges could not be matched (kept without BI score).")

# ==============================================================================
# 5. SAVE AS GRAPHML  (for Python / Dijkstra)
# ==============================================================================
graphml_path = f"{CONFIG['output_dir']}/BI_graph.graphml"
ox.save_graphml(G, filepath=graphml_path)
print(f"Saved GraphML → {graphml_path}")

# ==============================================================================
# 6. SAVE AS GEOPACKAGE  (for QGIS / visual inspection)
# ==============================================================================
gpkg_path = f"{CONFIG['output_dir']}/BI_graph.gpkg"
ox.save_graph_geopackage(G, filepath=gpkg_path)
print(f"Saved GeoPackage → {gpkg_path}")

print("\nDone! You can now:")
print("  • Open BI_graph.gpkg in QGIS to inspect nodes/edges by name")
print("  • Load BI_graph.graphml in Python for Dijkstra:")
print("      G = ox.load_graphml('BI_graph.graphml')")
print("      path = nx.shortest_path(G, source, target, weight='cost')")