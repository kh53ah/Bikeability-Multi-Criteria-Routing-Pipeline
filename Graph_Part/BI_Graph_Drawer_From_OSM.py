import pandas as pd
import ast
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.colors as colors

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CONFIG = {
    "csv_file": r"C:\Studium\SS26\Abschlussarbeit\Abschlussarbeit\BI_results.csv",
    "location": "Würzburg, Germany",

    # Column to visualize — "BI" for the final index, or any score column
    "metric_column": "BI",
    "metric_name": "Bikeability Index (BI)",

    # "RdYlGn" = red (low) → green (high), good for BI
    # Other options: "viridis", "plasma", "YlOrRd", "inferno"
    "colormap_style": "RdYlGn",
}

# ==============================================================================
# 1. LOAD DATA
# ==============================================================================
print(f"Loading data from {CONFIG['csv_file']}...")
df = pd.read_csv(CONFIG["csv_file"], low_memory=False)

# Build lookup: OSM way ID (int) → metric score
bi_lookup = {}
for _, row in df.iterrows():
    try:
        raw = str(row["osm_way_id"])
        if raw.startswith("("):
            _, way_id = ast.literal_eval(raw)
        else:
            way_id = int(raw)
        bi_lookup[int(way_id)] = row[CONFIG["metric_column"]]
    except (ValueError, SyntaxError):
        continue

print(f"  Loaded {len(bi_lookup)} way segments.")

# ==============================================================================
# 2. DOWNLOAD NETWORK & FILTER TO MATCHED EDGES
# ==============================================================================
print(f"Downloading road network for {CONFIG['location']}...")
G_full = ox.graph_from_place(CONFIG["location"], network_type="all")

print("Filtering to matched OSM edges...")
edges_to_keep = []
for u, v, key, data in G_full.edges(keys=True, data=True):
    if "osmid" in data:
        osm_ids = data["osmid"] if isinstance(data["osmid"], list) else [data["osmid"]]
        if any(int(oid) in bi_lookup for oid in osm_ids):
            edges_to_keep.append((u, v, key))

if not edges_to_keep:
    raise ValueError("No matching OSM IDs found. Check that your CSV way IDs match the download area.")

G = G_full.edge_subgraph(edges_to_keep).copy()
isolated = [n for n, deg in dict(G.degree()).items() if deg == 0]
G.remove_nodes_from(isolated)
print(f"  Kept {G.number_of_edges()} edges, {G.number_of_nodes()} nodes.")

# ==============================================================================
# 3. INJECT SCORES INTO EDGES
# ==============================================================================
for u, v, key, data in G.edges(keys=True, data=True):
    osm_ids = data["osmid"] if isinstance(data["osmid"], list) else [data["osmid"]]
    for oid in osm_ids:
        if int(oid) in bi_lookup:
            G[u][v][key]["bi_score"] = bi_lookup[int(oid)]
            break

# ==============================================================================
# 4. COLOR & WIDTH ARRAYS
# ==============================================================================
extracted_weights = [
    data["bi_score"]
    for u, v, k, data in G.edges(keys=True, data=True)
    if "bi_score" in data
]

min_w = min(extracted_weights)
max_w = max(extracted_weights)
print(f"  Score range: {min_w:.4f} → {max_w:.4f}")

cmap = plt.colormaps[CONFIG["colormap_style"]]
norm = colors.Normalize(vmin=min_w, vmax=max_w)

edge_colors = []
edge_widths = []

for u, v, key, data in G.edges(keys=True, data=True):
    w = data.get("bi_score", None)
    if w is None:
        edge_colors.append("#cccccc")
        edge_widths.append(1.0)
    else:
        norm_val = norm(w)
        edge_colors.append(colors.to_hex(cmap(norm_val)))
        edge_widths.append(1.5 + norm_val * 3.5)

# ==============================================================================
# 5. PLOT
# ==============================================================================
print("Plotting map...")
fig, ax = ox.plot_graph(
    G,
    edge_color=edge_colors,
    edge_linewidth=edge_widths,
    node_size=10,
    node_color="#2c3e50",
    node_alpha=0.7,
    bgcolor="#f8f8f8",
    show=False,
    close=False,
    figsize=(14, 14),
)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=colors.Normalize(vmin=0, vmax=1))
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.6, pad=0.02)
cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
cbar.set_ticklabels(["0.00", "0.25", "0.50", "0.75", "1.00"])
cbar.set_label(CONFIG["metric_name"], fontsize=12, labelpad=12)

plt.title(f"{CONFIG['metric_name']} — Würzburg", fontsize=13, pad=15)

output_path = "BI_map.jpg"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Saved to {output_path}")
plt.show()