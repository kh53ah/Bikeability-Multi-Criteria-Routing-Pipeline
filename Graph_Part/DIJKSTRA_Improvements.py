import networkx as nx
import matplotlib.pyplot as plt
import contextily as ctx
from pyproj import Transformer

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
NODE_NAME       = "Heidingsfeld"  # TO BE CHANGED
OUTPUT_PATH     = f"{NODE_NAME}_compare_I_b.jpg" # TO BE CHANGED

# Title shown above the figure (and subtitle line with start/end labels below it)
FIGURE_TITLE    = "Route Comparison Using the Bike Weighting Scheme"   # TO BE CHANGED
END_NODE_LABEL  = "University of Würzburg"

# Two graph files: runs 1 and 2 both use the original graph, run 3 uses the second graph
GRAPHML_PATH_ORIGINAL  = "final_Graph_b.graphml"        # TO BE CHANGED 
GRAPHML_PATH_IMPROVED  = "final_Graph_I_b.graphml"        # TO BE CHANGED

# Labels used in the legend for each graph's path
LABEL_1         = "Original Bikeability Route"
LABEL_2         = "Distance-Based Shortest Path"
LABEL_3         = "Improved Bikeability Route"

START_OSM_ID    = 315733120                # TO BE CHANGED
END_OSM_ID      = 727678361        # OSM node ID of the end node

# Edge attribute used for routing in each graph — set independently so you can
# e.g. route Graph 1 by "cost" (BI-weighted) and Graph 2 by "length" (pure distance)
WEIGHT_ATTR_1   = "cost"
WEIGHT_ATTR_2   = "length"
WEIGHT_ATTR_3   = "cost"

PATH_COLOR_1    = "blue"
PATH_COLOR_2    = "orange"
PATH_COLOR_3    = "purple"

FIG_SIZE        = (14, 14)
DPI             = 150
# ─────────────────────────────────────────────────────────────────────────────

# Transformer: WGS84 (lon/lat) → Web Mercator (meters), used by OSM tiles
_to_mercator = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def load_graph(path: str) -> nx.Graph:
    """Load the GraphML as an undirected graph."""
    G_directed = nx.read_graphml(path)
    G = G_directed.to_undirected()
    print(f"Graph loaded from {path}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def find_shortest_path(G: nx.Graph, source: int, target: int, weight: str) -> list:
    """Run Dijkstra (using the given edge weight attribute) and return the node path."""
    source_str = str(source)
    target_str = str(target)

    if source_str not in G.nodes:
        raise ValueError(f"Start node {source} not found in graph.")
    if target_str not in G.nodes:
        raise ValueError(f"End node {target} not found in graph.")

    path = nx.dijkstra_path(G, source=source_str, target=target_str, weight=weight)
    cost = nx.dijkstra_path_length(G, source=source_str, target=target_str, weight=weight)
    print(f"Shortest path found (weight='{weight}'): {len(path)} nodes, total {weight} = {cost:.4f}")
    return path


def build_mercator_pos(G: nx.Graph) -> dict:
    """
    Convert node lon/lat (x/y in GraphML) to Web Mercator (EPSG:3857).
    OSM stores x = longitude, y = latitude.
    """
    pos = {}
    for node, data in G.nodes(data=True):
        if "x" in data and "y" in data:
            mx, my = _to_mercator.transform(float(data["x"]), float(data["y"]))
            pos[node] = (mx, my)
    return pos


def get_path_edges(path: list) -> set:
    """Build an undirected edge set (both directions) from a node path."""
    edges = set(zip(path[:-1], path[1:]))
    edges |= {(v, u) for u, v in edges}
    return edges


def plot_result(
    G1: nx.Graph, path1: list,
    G2: nx.Graph, path2: list,
    G3: nx.Graph, path3: list,
    output_path: str,
):
    """
    Visualize a simple background graph (using G1's geometry) with an OSM
    basemap, and overlay all three Dijkstra paths (one per graph) in different
    colors for comparison.
    """

    # ── Positions in Web Mercator ──────────────────────────────────────────
    # Background graph + node positions are taken from G1 for simplicity.
    pos1 = build_mercator_pos(G1)
    pos2 = build_mercator_pos(G2)
    pos3 = build_mercator_pos(G3)

    # ── Path edges for each graph ──────────────────────────────────────────
    path1_edge_set = get_path_edges(path1)
    path2_edge_set = get_path_edges(path2)
    path3_edge_set = get_path_edges(path3)

    highlight_edges_1 = [(u, v) for u, v in G1.edges() if (u, v) in path1_edge_set]
    highlight_edges_2 = [(u, v) for u, v in G2.edges() if (u, v) in path2_edge_set]
    highlight_edges_3 = [(u, v) for u, v in G3.edges() if (u, v) in path3_edge_set]

    # ── Figure ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    # Simple background: all edges/nodes from G1 in plain gray (no BI coloring)
    nx.draw_networkx_edges(
        G1, pos1,
        edge_color="lightgray",
        width=1.2,
        alpha=0.6,
        ax=ax
    )
    nx.draw_networkx_nodes(
        G1, pos1,
        node_size=6,
        node_color="gray",
        alpha=0.4,
        ax=ax
    )

    # Path 1 (from Graph 1) in blue
    nx.draw_networkx_edges(
        G1, pos1,
        edgelist=highlight_edges_1,
        edge_color=PATH_COLOR_1,
        width=5.0,
        alpha=0.9,
        ax=ax,
        label=LABEL_1,
    )

    # Path 2 (from Graph 2) in orange
    nx.draw_networkx_edges(
        G2, pos2,
        edgelist=highlight_edges_2,
        edge_color=PATH_COLOR_2,
        width=5.0,
        alpha=0.9,
        ax=ax,
        label=LABEL_2,
    )

    # Path 3 (from Graph 3) in purple
    nx.draw_networkx_edges(
        G3, pos3,
        edgelist=highlight_edges_3,
        edge_color=PATH_COLOR_3,
        width=5.0,
        alpha=0.9,
        ax=ax,
        label=LABEL_3,
    )

    # Start node (green) and end node (red) — taken from path 1's graph;
    # all three paths share the same start/end OSM IDs.
    nx.draw_networkx_nodes(G1, pos1, nodelist=[path1[0]],  node_size=150, node_color="green", ax=ax)
    nx.draw_networkx_nodes(G1, pos1, nodelist=[path1[-1]], node_size=150, node_color="red",   ax=ax)

    # ── OSM basemap ────────────────────────────────────────────────────────
    ctx.add_basemap(
        ax,
        crs="EPSG:3857",
        source=ctx.providers.OpenStreetMap.Mapnik,
        alpha=0.55,
        zoom="auto",
    )

    # ── Legend ─────────────────────────────────────────────────────────────
    legend_handles = [
        plt.Line2D([0], [0], color=PATH_COLOR_1, lw=5, label=LABEL_1),
        plt.Line2D([0], [0], color=PATH_COLOR_2, lw=5, label=LABEL_2),
        plt.Line2D([0], [0], color=PATH_COLOR_3, lw=5, label=LABEL_3),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Start'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='End'),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=12, framealpha=0.9)

    ax.set_title(
        f"{FIGURE_TITLE}\n"
        f"Start: {NODE_NAME} → End: {END_NODE_LABEL}",
        fontsize=20
    )
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, format="jpeg", dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    G1 = load_graph(GRAPHML_PATH_ORIGINAL)
    G2 = load_graph(GRAPHML_PATH_ORIGINAL)
    G3 = load_graph(GRAPHML_PATH_IMPROVED)

    path1 = find_shortest_path(G1, START_OSM_ID, END_OSM_ID, WEIGHT_ATTR_1)
    path2 = find_shortest_path(G2, START_OSM_ID, END_OSM_ID, WEIGHT_ATTR_2)
    path3 = find_shortest_path(G3, START_OSM_ID, END_OSM_ID, WEIGHT_ATTR_3)

    plot_result(G1, path1, G2, path2, G3, path3, OUTPUT_PATH)