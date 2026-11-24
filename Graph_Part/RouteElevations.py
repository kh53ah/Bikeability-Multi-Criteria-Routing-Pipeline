import json
import requests
import networkx as nx
import numpy as np

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
JSON_INPUT_PATH   = "x.json"  # TO BE CHANGED
GRAPHML_PATH      = "final_Graph_Bikes.graphml" # TO BE CHANGED
ELEVATION_API_URL = "https://api.open-elevation.com/api/v1/lookup"
# ──────────────────────────────────────────────────────────────────────────────

def load_graph_coordinates(path: str) -> nx.Graph:
    """Load the GraphML file to extract coordinate mappings."""
    print(f"Loading graph from {path} to extract coordinates...")
    return nx.read_graphml(path)


def get_route_coordinates(G: nx.Graph, node_path: list) -> list:
    """Convert a list of node IDs into a list of {'latitude': y, 'longitude': x} dicts."""
    coordinates = []
    for node_id in node_path:
        node_id_str = str(node_id)
        if node_id_str in G.nodes:
            node_data = G.nodes[node_id_str]
            # OSMnx uses 'x' for longitude and 'y' for latitude
            if 'x' in node_data and 'y' in node_data:
                coordinates.append({
                    "latitude": float(node_data['y']),
                    "longitude": float(node_data['x'])
                })
    return coordinates


def fetch_elevations(locations: list) -> list:
    """Send a POST request to the Open-Elevation API to get heights in meters."""
    if not locations:
        return []
    
    payload = {"locations": locations}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        print(f"Querying Open-Elevation API for {len(locations)} points...")
        response = requests.post(ELEVATION_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result_data = response.json()
        return [res["elevation"] for res in result_data.get("results", [])]
    except Exception as e:
        print(f"Error fetching data from Elevation API: {e}")
        return []


def analyze_elevation():
    # 1. Load the computed routes from your original script's JSON
    try:
        with open(JSON_INPUT_PATH, "r", encoding="utf-8") as f:
            route_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find '{JSON_INPUT_PATH}'. Make sure your first script ran successfully.")
        return

    # 2. Load the base graph to extract geometric attributes
    G = load_graph_coordinates(GRAPHML_PATH)
    
    print("\n" + "="*65)
    print(f"TYPICAL ELEVATION PROFILES: {route_data.get('start_label')} → {route_data.get('end_label')}")
    print("="*65)

    # 3. Process each route found in the JSON
    for route in route_data.get("routes", []):
        label = route.get("label")
        node_path = route.get("node_path", [])
        
        # Get lat/lon pairs from node IDs
        coords = get_route_coordinates(G, node_path)
        if not coords:
            print(f"\n[{label}] Could not find coordinate data for the path nodes.")
            continue
            
        # Fetch elevations from the open API
        elevations = fetch_elevations(coords)
        
        if elevations:
            # Convert to a numpy array for statistical calculations
            elev_array = np.array(elevations)
            
            # Calculate the 25th and 75th percentiles (The Middle 50%)
            q1 = np.percentile(elev_array, 25)
            q3 = np.percentile(elev_array, 75)
            
            # Additional standard metrics
            min_h = np.min(elev_array)
            max_h = np.max(elev_array)
            avg_h = np.mean(elev_array)
            total_climb = sum(max(0, elevations[i] - elevations[i-1]) for i in range(1, len(elevations)))

            print(f"\n📊 Route Profile: {label}")
            print(f"  • Absolute Range:   {min_h:.1f} m to {max_h:.1f} m")
            print(f"  • Average Height:   {avg_h:.1f} m")
            print(f"  • Cumulative Climb: {total_climb:.1f} m")
            print(f"  • Summary Statement:")
            print(f"    👉 \"Along this route, the typical elevation values are between {q1:.1f} m and {q3:.1f} m.\"")
            print(f"    (The middle 50% of the journey stays within this {q3-q1:.1f} meter bracket, ignoring extreme outliers).")
            print("-" * 65)
        else:
            print(f"\n❌ Failed to calculate elevation for {label}.")

if __name__ == "__main__":
    analyze_elevation()