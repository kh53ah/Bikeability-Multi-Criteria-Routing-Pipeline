import os
import warnings

import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd

# Essential package check for city basemap visualization
try:
    import contextily as ctx
    HAS_CONTEXTILY = True
except ImportError:
    HAS_CONTEXTILY = False

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHML_FILE = os.path.join(SCRIPT_DIR, "final_Graph.graphml") 
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "routing_graph_synthetic_nodes.png") 

# Representative manually initialized origin nodes
ORIGIN_NODES = {
    "1": "Altstadt / Sanderau",
    "2": "Grombühl",
    "8284442591": "Gerbrunn",
    "13115365264": "Heidingsfeld",
}

# Real target node destination at the university perimeter
DESTINATION_NODE = "727678361"
DESTINATION_LABEL = "Hubland / University"

# Appearance Configuration
REAL_EDGE_COLOR = "#444444"          # Dark gray to contrast against clean map backgrounds
REAL_EDGE_WIDTH = 0.9
SYNTHETIC_EDGE_COLOR = "#0066cc"      # Vivid blue access links
SYNTHETIC_EDGE_WIDTH = 2.8
ORIGIN_NODE_COLOR = "#d7191c"         # Distinct red origin markers
DESTINATION_NODE_COLOR = "#1a9641"    # Emerald green destination marker
NETWORK_NODE_COLOR = "#333333"
ORIGIN_NODE_SIZE = 100
DESTINATION_NODE_SIZE = 140
NETWORK_NODE_SIZE = 5

# Text Meta Headers
FIGURE_TITLE = "Routing Analysis Network"

# ==============================================================================
# 1. LOAD GRAPH DATA
# ==============================================================================
print(f"Loading GraphML payload from: {GRAPHML_FILE}...")
try:
    G = ox.load_graphml(GRAPHML_FILE)
except Exception:
    G = nx.read_graphml(GRAPHML_FILE, force_multigraph=True)

if "crs" not in G.graph or G.graph["crs"] is None:
    warnings.warn("Graph has no CRS metadata tracking. Falling back to default EPSG:4326.")
    G.graph["crs"] = "EPSG:4326"

print(f"Successfully loaded {G.number_of_edges()} edges and {G.number_of_nodes()} nodes.")

# ==============================================================================
# 2. COORDINATE WRAPPING FOR GEOGRAPHIC BASEMAP
# ==============================================================================
print("Projecting street matrix coordinates to EPSG:3857 for Web Mercator basemap overlay...")
G_proj = ox.project_graph(G, to_crs="EPSG:3857")

nodes_gdf, edges_gdf = ox.graph_to_gdfs(G_proj, nodes=True, edges=True, fill_edge_geometry=True)

# Parse database indices to standard strings
nodes_gdf["node_id_str"] = nodes_gdf.index.astype(str)
edges_gdf["u_str"] = edges_gdf.index.get_level_values(0).astype(str)
edges_gdf["v_str"] = edges_gdf.index.get_level_values(1).astype(str)

origin_ids = {str(n) for n in ORIGIN_NODES.keys()}
destination_id = str(DESTINATION_NODE)
marked_ids = origin_ids | {destination_id}

# Isolate synthetic connections touching target centroids
edges_gdf["is_synthetic_connector"] = (
    edges_gdf["u_str"].isin(origin_ids) | edges_gdf["v_str"].isin(origin_ids)
)

real_edges = edges_gdf.loc[~edges_gdf["is_synthetic_connector"]]
synthetic_edges = edges_gdf.loc[edges_gdf["is_synthetic_connector"]]

origin_nodes = nodes_gdf.loc[nodes_gdf["node_id_str"].isin(origin_ids)]
destination_node = nodes_gdf.loc[nodes_gdf["node_id_str"] == destination_id]
other_nodes = nodes_gdf.loc[~nodes_gdf["node_id_str"].isin(marked_ids)]

# Debug verification boundaries
missing_origins = sorted(origin_ids - set(origin_nodes["node_id_str"]))
if missing_origins:
    print("WARNING: Specified origin nodes missing from GraphML matrix:", missing_origins)
if destination_node.empty:
    print(f"WARNING: Target destination key node {destination_id} could not be resolved.")

# ==============================================================================
# 3. GEOSPATIAL RENDERING PIPELINE
# ==============================================================================
print("Plotting network layers over spatial map landscape...")
fig, ax = plt.subplots(figsize=(14, 14))

# Layer 1 & 2: Background network components
real_edges.plot(ax=ax, color=REAL_EDGE_COLOR, linewidth=REAL_EDGE_WIDTH, alpha=0.70, zorder=2)
other_nodes.plot(ax=ax, color=NETWORK_NODE_COLOR, markersize=NETWORK_NODE_SIZE, alpha=0.40, zorder=3)

# Layer 3: Overlay high-priority synthetic structure arrays
if not synthetic_edges.empty:
    synthetic_edges.plot(
        ax=ax,
        color=SYNTHETIC_EDGE_COLOR,
        linewidth=SYNTHETIC_EDGE_WIDTH,
        alpha=0.95,
        zorder=4,
    )

if not origin_nodes.empty:
    origin_nodes.plot(
        ax=ax,
        color=ORIGIN_NODE_COLOR,
        edgecolor="white",
        linewidth=1.5,
        markersize=ORIGIN_NODE_SIZE,
        zorder=5,
    )

if not destination_node.empty:
    destination_node.plot(
        ax=ax,
        color=DESTINATION_NODE_COLOR,
        edgecolor="white",
        linewidth=1.5,
        markersize=DESTINATION_NODE_SIZE,
        zorder=6,
    )

# Annotation typography mapping
for node_id, label in ORIGIN_NODES.items():
    row = nodes_gdf.loc[nodes_gdf["node_id_str"] == str(node_id)]
    if not row.empty:
        x = row.geometry.iloc[0].x
        y = row.geometry.iloc[0].y
        ax.annotate(
            label,
            xy=(x, y),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=9.5,
            fontweight="bold",
            color="black",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.90, edgecolor="#cccccc", linewidth=0.5),
            zorder=7,
        )

if not destination_node.empty:
    x = destination_node.geometry.iloc[0].x
    y = destination_node.geometry.iloc[0].y
    ax.annotate(
        DESTINATION_LABEL,
        xy=(x, y),
        xytext=(7, 7),
        textcoords="offset points",
        fontsize=9.5,
        fontweight="bold",
        color="black",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.90, edgecolor="#cccccc", linewidth=0.5),
        zorder=7,
    )

# Base Tile Context Deployment
if HAS_CONTEXTILY:
    try:
        # Utilizing CartoDB Positron to legibly display roads, topography, and parks behind data layers
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.Positron,
            crs=edges_gdf.crs,
            attribution_size=5,
            zorder=1,
        )
    except Exception as exc:
        print(f"CRITICAL: Map frame builder aborted. Reason: {exc}")
else:
    print("WARNING: Contextily dependencies missing. Map layout could not be drawn.")

# Text Element Compilations
fig.suptitle(FIGURE_TITLE, fontsize=15, fontweight="bold", y=0.97)

# Categorical Legend Assembly (No Continuous Colorbars)
legend_elements = [
    plt.Line2D([], [], marker="o", linestyle="None", markersize=8,
               markerfacecolor=ORIGIN_NODE_COLOR, markeredgecolor="white",
               label="Synthetic Origin Node"),
    plt.Line2D([], [], marker="o", linestyle="None", markersize=9,
               markerfacecolor=DESTINATION_NODE_COLOR, markeredgecolor="white",
               label="Real Destination Node (Hubland Campus)"),
    plt.Line2D([], [], color=SYNTHETIC_EDGE_COLOR, linewidth=3,
               label="Synthetic Connector Access Edge"),
    plt.Line2D([], [], color=REAL_EDGE_COLOR, linewidth=1.5,
               label="Existing Street Network Infrastructure")
]

ax.legend(
    handles=legend_elements,
    loc="lower left",
    frameon=True,
    framealpha=0.95,
    facecolor="white",
    edgecolor="#dddddd"
)

ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=250, bbox_inches="tight", facecolor="white")
print(f"Process Complete. Output graphic recorded at -> {OUTPUT_PATH}")
plt.show()