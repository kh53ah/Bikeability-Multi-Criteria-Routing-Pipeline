import pandas as pd
import ast
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.colors as colors

# ==============================================================================
# DATA PIPELINE CONFIGURATION
# Adjust these variables whenever your data source, columns, or metrics change!
# ==============================================================================
CONFIG = {
    "csv_file": r"C:\Studium\SS26\Abschlussarbeit\Abschlussarbeit\results\AQI_Results.csv",
    "location": "Würzburg, Germany",
    
    # Define which columns are summed together to create your baseline intensity score
    "columns_to_sum": [
        "aqi_score"
    ],
    
    # Label metadata used to dynamically style your visualization colorbar axes
    "metric_name": "Air Quality",  # e.g., "AQI Level", "Elevation (m)", "SVI Score"
    "colormap_style": "inferno"          # Try: "viridis", "magma", "plasma", "YlOrRd"
}

# ==============================================================================
# 1. LOAD DATA & CALCULATE METRIC
# ==============================================================================
print(f"Loading data from {CONFIG['csv_file']}...")
df = pd.read_csv(CONFIG['csv_file'], low_memory=False)

# Sum up targeted columns dynamically
df['calculated_score'] = df[CONFIG['columns_to_sum']].sum(axis=1)

# Store weights inside a structured lookup dictionary
bi_lookup = {}
for idx, row in df.iterrows():
    try:
        # Gracefully handle standard ints or tuple strings like "('way', 12345)"
        if str(row['osm_way_id']).startswith('('):
            _, way_id = ast.literal_eval(str(row['osm_way_id']))
        else:
            way_id = row['osm_way_id']
        bi_lookup[int(way_id)] = row['calculated_score']
    except (ValueError, SyntaxError):
        continue

# ==============================================================================
# 2. DOWNLOAD & SUBSET THE NETWORK (Isolating Only Used Components)
# ==============================================================================
print(f"Downloading road network for {CONFIG['location']}...")
G_full = ox.graph_from_place(CONFIG['location'], network_type="drive")

print("Filtering graph to isolate ONLY the roads mentioned in your dataset...")
edges_to_keep = []

# Scan the full graph to find edges matching your dataset's OSM IDs
for u, v, key, data in G_full.edges(keys=True, data=True):
    if "osmid" in data:
        osm_ids = data["osmid"] if isinstance(data["osmid"], list) else [data["osmid"]]
        # If any edge segment matches our CSV keys, cache it
        if any(int(osmid) in bi_lookup for osmid in osm_ids):
            edges_to_keep.append((u, v, key))

# Create a clean subgraph containing only matching edges
if not edges_to_keep:
    raise ValueError("Critical Error: No matching OSM IDs found between your CSV and the download area.")

G = G_full.edge_subgraph(edges_to_keep).copy()

# Remove isolated/dead-end nodes that no longer connect to our active edges
nodes_to_remove = [node for node, degree in dict(G.degree()).items() if degree == 0]
G.remove_nodes_from(nodes_to_remove)

# ==============================================================================
# 3. GENERATE INTENSITY STYLING & MAP GRADIENT
# ==============================================================================
# Inject dynamic data weights straight into the refined network model
for u, v, key, data in G.edges(keys=True, data=True):
    osm_ids = data["osmid"] if isinstance(data["osmid"], list) else [data["osmid"]]
    for osmid in osm_ids:
        if int(osmid) in bi_lookup:
            G[u][v][key]["intensity_weight"] = bi_lookup[int(osmid)]
            break

# Collect final clean list of score weights to scale colormap ranges
extracted_weights = [data["intensity_weight"] for u, v, k, data in G.edges(keys=True, data=True)]
max_weight = max(extracted_weights) if extracted_weights else 1.0
min_weight = min(extracted_weights) if extracted_weights else 0.0

# Initialize modern colormap registry to ensure future compatibility
cmap = plt.colormaps[CONFIG["colormap_style"]]

edge_colors = []
edge_widths = []

for weight in extracted_weights:
    # Scale calculation between 0.0 and 1.0
    norm_divisor = (max_weight - min_weight) if (max_weight - min_weight) > 0 else 1.0
    norm_val = (weight - min_weight) / norm_divisor
    
    # Map color value smoothly (padding bottom range slightly so low values stay legible)
    color_rgba = cmap(0.15 + (norm_val * 0.85))
    edge_colors.append(colors.to_hex(color_rgba))
    edge_widths.append(2.0 + (norm_val * 4.0)) # Scaled line widths (Thicker = Stronger)

# ==============================================================================
# 4. PLOT COMPACT SPATIAL INTENSITY NETWORK
# ==============================================================================
print("Plotting your custom structured data map...")
fig, ax = ox.plot_graph(
    G,
    edge_color=edge_colors,
    edge_linewidth=edge_widths,
    node_size=18,               # Clear structural intersection markers
    node_color="#2c3e50",       # Clean, modern slate anchor color
    node_alpha=0.9,
    bgcolor="#ffffff",          # Pure white map backdrop to amplify contrast
    show=False,
    close=False
)

# Add matching color scale legend matching the specific configured metric type
scalar_mappable = plt.cm.ScalarMappable(
    cmap=cmap, 
    norm=colors.Normalize(vmin=min_weight, vmax=max_weight)
)
scalar_mappable.set_array([])
colorbar = fig.colorbar(scalar_mappable, ax=ax, orientation="vertical", shrink=0.7, pad=0.02)
colorbar.set_label(f"{CONFIG['metric_name']} Intensity Scale", fontsize=11, labelpad=10)

plt.title(f"Metric: {CONFIG['metric_name']}", fontsize=13, pad=15)
plt.show()