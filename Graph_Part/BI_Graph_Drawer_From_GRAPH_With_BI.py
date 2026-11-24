import os
import warnings

import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

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
GRAPHML_FILE = os.path.join(SCRIPT_DIR, "final_Graph_b.graphml") 
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "BI_Bikes.png") 

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

# ------------------------------------------------------------------------------
# BIKEABILITY INDEX (BI) DISPLAY CONFIGURATION
# ------------------------------------------------------------------------------
# Edge attribute in the GraphML holding the BI score (0.0 - 1.0 expected)
BI_ATTRIBUTE = "bi_score"

# Colormap for BI edges (low BI = red, high BI = green)
BI_COLORMAP = "inferno"

# Color for edges with no usable bi_score (missing/empty/unparseable)
UNKNOWN_BI_COLOR = "#999999"
UNKNOWN_BI_WIDTH = 0.8
UNKNOWN_BI_ALPHA = 0.5

# Width/alpha for BI gradient edges
BI_EDGE_WIDTH = 3.25
BI_EDGE_ALPHA = 0.85

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

# ------------------------------------------------------------------------------
# Parse bi_score into a clean numeric column (GraphML stores everything as text,
# and some synthetic/placeholder edges have an empty bi_score)
# ------------------------------------------------------------------------------
def _parse_bi(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None

if BI_ATTRIBUTE in edges_gdf.columns:
    edges_gdf["bi_value"] = edges_gdf[BI_ATTRIBUTE].apply(_parse_bi)
else:
    warnings.warn(f"Edge attribute '{BI_ATTRIBUTE}' not found in GraphML. All edges will be treated as unknown BI.")
    edges_gdf["bi_value"] = None

n_missing_bi = edges_gdf["bi_value"].isna().sum()
if n_missing_bi:
    print(f"NOTE: {n_missing_bi} edge(s) have no usable {BI_ATTRIBUTE} value and will be drawn as unknown BI.")

origin_ids = {str(n) for n in ORIGIN_NODES.keys()}
destination_id = str(DESTINATION_NODE)
marked_ids = origin_ids | {destination_id}

# Isolate synthetic connections touching target centroids
edges_gdf["is_synthetic_connector"] = (
    edges_gdf["u_str"].isin(origin_ids) | edges_gdf["v_str"].isin(origin_ids)
)

real_edges = edges_gdf.loc[~edges_gdf["is_synthetic_connector"]]
synthetic_edges = edges_gdf.loc[edges_gdf["is_synthetic_connector"]]

# Split real (non-synthetic) edges into those with a usable BI value vs. unknown
has_bi = real_edges["bi_value"].notna()
bi_normal = real_edges.loc[has_bi]
bi_unknown = real_edges.loc[~has_bi]

print(f"BI breakdown -> with BI value: {len(bi_normal)}, unknown: {len(bi_unknown)}")

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

# Colormap for BI gradient
bi_norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
bi_cmap = plt.get_cmap(BI_COLORMAP)

# Layer 1 & 2: Background network edges, colored by Bikeability Index (BI)

# 1a. Unknown-BI edges (no usable score) - neutral gray, drawn first/underneath
if not bi_unknown.empty:
    bi_unknown.plot(ax=ax, color=UNKNOWN_BI_COLOR, linewidth=UNKNOWN_BI_WIDTH, alpha=UNKNOWN_BI_ALPHA, zorder=2)

# 1b. BI edges - red->green gradient by bi_value
if not bi_normal.empty:
    bi_normal.plot(
        ax=ax,
        color=[bi_cmap(bi_norm(v)) for v in bi_normal["bi_value"]],
        linewidth=BI_EDGE_WIDTH,
        alpha=BI_EDGE_ALPHA,
        zorder=2,
    )

# Layer 3: Overlay high-priority synthetic structure arrays
if not synthetic_edges.empty:
    synthetic_edges.plot(
        ax=ax,
        color=SYNTHETIC_EDGE_COLOR,
        linewidth=SYNTHETIC_EDGE_WIDTH,
        alpha=0.95,
        zorder=4,
    )

# Layer 4: Origin and destination markers
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

# Categorical Legend Assembly
legend_elements = [
    plt.Line2D([], [], marker="o", linestyle="None", markersize=8,
               markerfacecolor=ORIGIN_NODE_COLOR, markeredgecolor="white",
               label="Synthetic Origin Node"),
    plt.Line2D([], [], marker="o", linestyle="None", markersize=9,
               markerfacecolor=DESTINATION_NODE_COLOR, markeredgecolor="white",
               label="Real Destination Node (Hubland Campus)"),
    plt.Line2D([], [], color=SYNTHETIC_EDGE_COLOR, linewidth=3,
               label="Synthetic Connector Access Edge"),
    plt.Line2D([], [], color=bi_cmap(bi_norm(0.1)), linewidth=3,
               label="Bikeability Index (red\u2192green gradient)"),
    plt.Line2D([], [], color=UNKNOWN_BI_COLOR, linewidth=3,
               label="BI unknown / missing"),
]

ax.legend(
    handles=legend_elements,
    loc="lower left",
    frameon=True,
    framealpha=0.95,
    facecolor="white",
    edgecolor="#dddddd"
)

# BI gradient colorbar
sm = cm.ScalarMappable(cmap=bi_cmap, norm=mcolors.Normalize(vmin=0.0, vmax=1.0))
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.35, pad=0.02, anchor=(0.1, 0.45), location="right")
cbar.set_label("Bikeability Index (BI)", fontsize=9)

ax.set_axis_off()
plt.tight_layout(pad=0)
plt.savefig(
    OUTPUT_PATH,
    dpi=250,
    bbox_inches="tight",
    pad_inches=0,
    facecolor="white"
)
print(f"Process Complete. Output graphic recorded at -> {OUTPUT_PATH}")
plt.show()