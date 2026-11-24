# Multi-Criteria Bikeability Index (BI) Data & Scoring Pipeline

An end-to-end geospatial analysis and scoring pipeline developed as part of a Bachelor's thesis at the University of Würzburg. The framework evaluates urban bikeability (*Bikeability Index*) across street networks by combining computer vision imagery analysis, OpenStreetMap (OSM) infrastructure data, elevation profiles, traffic congestion metrics, and air quality indices.

---

## Project Overview

This pipeline automates the ingestion, segmentation, and multi-criteria scoring of street segments in urban transportation networks. The resulting segment-level scores serve as edge weights for downstream graph-based routing algorithms (e.g., Dijkstra routing) to evaluate campus accessibility and simulate the impact of new bicycle infrastructure.

### Core Evaluation Dimensions
- **OSM Infrastructure (`OSM_pipeline`):** Evaluates dedicated cycling paths, street width, land-use characteristics, and public transit proximity.
- **Street View Imagery (`SVI_pipeline`):** Uses deep learning vision models (**Mask2Former**) to perform semantic segmentation on street imagery for visual suitability.
- **Elevation & Topography (`ElevationCalculator`):** Quantifies slope and elevation changes across sub-segments.
- **Traffic Congestion (`CongestionCalculator`):** Incorporates real-time/historical traffic density data.
- **Air Quality (`AQICalculator`):** Ingests point-based Air Quality Index (AQI) metrics for geospatial centroids.

---

## Pipeline Architecture

The main entry point `BI_Pipeline.py` executes an 8-stage automated workflow:

```
                  ┌──────────────────────────────┐
                  │   Streets_list.json / OSM    │
                  └──────────────┬───────────────┘
                                 │
                   [Step 1] Ingest OSM Ways
                                 │
                  [Step 2] Compute Street Width
                                 │
             ┌───────────────────┴───────────────────┐
             │ Loop over individual OSM ways        │
             │ [Step 3] Sub-Segment Creation        │
             └───────────────────┬───────────────────┘
                                 │
     ┌──────────────┬────────────┼────────────┬──────────────┐
     │              │            │            │              │
[Step 4]       [Step 5]     [Step 6]     [Step 7]       [Step 8]
OSM Score     SVI Model   Elevation    Congestion      AQI Score
(Land/Transit) (Mask2Former)  (Slope)     (Traffic)    (Air Quality)
     │              │            │            │              │
     └──────────────┴────────────┼────────────┴──────────────┘
                                 │
                   [Step 9] Export Results
                   (Modular CSV Generators)
```

### Detailed Execution Steps

1. **OSM Street Ingestion (`StreetImporter`):** Ingests raw street geometries from OpenStreetMap using `OSMnx` and `GeoPandas`.
2. **Width Calculation (`StreetWidthCalculator`):** Determines overall street width across imported ways.
3. **Sub-Segment Generation (`StreetSegmentsCreator`):** Subdivides long OSM ways into micro-segments to enable high-resolution spatial scoring.
4. **OSM Infrastructure Scoring (`OSM_Score`):** Intersects segments with land-use zones and public transport networks.
5. **Computer Vision Road Segmentation (`RoadSegmentation`):** Scores visual street environment quality via pixel-level semantic segmentation.
6. **Topographic Elevation Analysis (`ElevationCalculator`):** Calculates incline profiles for each sub-segment.
7. **Traffic Congestion Analysis (`CongestionCalculator`):** Computes localized vehicle traffic scores.
8. **Geospatial AQI Analysis (`AQICalculator`):** Fetches localized air quality metrics based on segment centroid coordinates.
9. **Results Export (`Results/`):** Persists criteria scores into modular CSV outputs per street and OSM way ID.

---

## Tech Stack & Dependencies

- **Language:** Python 3.10+
- **Geospatial & Graph Analysis:** `GeoPandas`, `OSMnx`, `Shapely`, `NetworkX`
- **Data Manipulation:** `pandas`, `numpy`
- **Computer Vision / AI:** PyTorch, Hugging Face Transformers (`Mask2Former`)
- **Plotting & Visualization:** `matplotlib`

---

## Getting Started

### 1. Prerequisites
Ensure you have a Python virtual environment (`.venv`) set up with standard geospatial C-libraries (GEOS, GDAL, PROJ) installed.

### 2. Installation
Clone the repository and install the dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
pip install -r requirements.txt
```

### 3. Configuration
Edit `Streets_list.json` to define the target street names to process:

```json
[
  "Am Hubland",
  "Rottendorfer Straße",
  "Sanderring"
]
```

### 4. Run the Pipeline
Execute the main pipeline script from the root directory:

```bash
python BI_Pipeline.py
```

Scored results will be automatically exported to the `Results/` directory as individual CSV files per metric and street.
