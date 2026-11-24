import osmnx as ox
import geopandas as gpd
import os

# 1. Setup paths and load Graph
current_dir = os.path.dirname(os.path.abspath(__file__))
gpkg_path = os.path.join(current_dir, "wuerzburg_for_qgis.gpkg")
gdf_nodes = gpd.read_file(gpkg_path, layer="nodes").set_index('osmid')
gdf_edges = gpd.read_file(gpkg_path, layer="edges").set_index(['u', 'v', 'key'])
G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)

# 2. Your Test IDs
test_ids = ["6193413", "55443007", "55443022", "160085175", "269966125", 
            "274772262", "274772263", "1248240300", "1340653717"]

# 3. Identify Matched Edges and their connected Nodes
matched_nodes = set()
edge_colors = []

for u, v, k, data in G.edges(data=True, keys=True):
    osmid_attr = str(data.get('osmid', ''))
    is_match = any(tid in osmid_attr for tid in test_ids)

    if is_match:
        edge_colors.append('red')
        # Add the start and end node of this segment to our "highlight" list
        matched_nodes.add(u)
        matched_nodes.add(v)
    else:
        edge_colors.append('#e0e0e0')

# 4. Define Node Colors and Sizes
# If a node is in our matched_nodes set, make it blue and large. Otherwise, invisible.
node_colors = ['blue' if node in matched_nodes else 'none' for node in G.nodes()]
node_sizes = [30 if node in matched_nodes else 0 for node in G.nodes()]

# 5. Plot to verify connectivity
print(f"Verifying... Found {len(matched_nodes)} connected nodes along the street.")
# Print the total count for your Würzburg graph
# 1. Total unique nodes connected to the matched segments
print(f"Total highlighted nodes for this street: {len(matched_nodes)}")

# 2. Detailed breakdown
print(f"Total segments (edges) matched: {len(matched_nodes)}")

ox.plot_graph(G, 
              edge_color=edge_colors, 
              edge_linewidth=2,
              node_color=node_colors, 
              node_size=node_sizes, 
              node_zorder=3, # Puts nodes on top of edges
              bgcolor='white')