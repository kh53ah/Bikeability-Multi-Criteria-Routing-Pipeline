# Multi-Criteria Bikeability Index (BI) Data & Scoring Pipeline

An end-to-end geospatial analysis and scoring pipeline developed as part of a Bachelor's thesis at the University of Würzburg. The framework evaluates urban bikeability (*Bikeability Index*) across street networks by combining computer vision imagery analysis, OpenStreetMap (OSM) infrastructure data, elevation profiles, traffic congestion metrics, and air quality indices.

---

## 📌 Project Overview

This pipeline automates the ingestion, segmentation, and multi-criteria scoring of street segments in urban transportation networks (with primary focus on **Würzburg, Germany**). The resulting segment-level scores serve as edge weights for downstream graph-based routing algorithms (e.g., Dijkstra routing) to evaluate campus accessibility and simulate the impact of new bicycle infrastructure.

### Core Evaluation Dimensions
- **OSM Infrastructure (`OSM_pipeline`):** Evaluates dedicated cycling paths, street width, land-use characteristics, and public transit proximity.
- **Street View Imagery (`SVI_pipeline`):** Uses deep learning vision models (**Mask2Former**) to perform semantic segmentation on street imagery for visual suitability.
- **Elevation & Topography (`ElevationCalculator`):** Quantifies slope and elevation changes across sub-segments.
- **Traffic Congestion (`CongestionCalculator`):** Incorporates real-time/historical traffic density data.
- **Air Quality (`AQICalculator`):** Ingests point-based Air Quality Index (AQI) metrics for geospatial centroids.

---

## 🏗 Pipeline Architecture

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

## 📁 Repository Structure

```
├── BI_Pipeline.py                   # Main pipeline execution entry point
├── GDF_Importer.py                  # Ingests OSM street geometries
├── StreetWidth_Calculator.py        # Computes street width metrics
├── StreetSegmentsCreator.py         # Subdivides OSM ways into sub-segments
├── Elevation_Calculator.py          # Topography and slope scoring
├── Congestion_Calculator.py         # Traffic congestion analysis
├── AQI_Calculator.py                # Air Quality Index API integration
├── Streets_list.json                # Target street configuration list
│
├── OSM_pipeline/
│   └── OSM_Criterias_Calculator.py  # Land use, transit, and infrastructure criteria
│
├── SVI_pipeline/
│   └── Run_SVI_Calculations.py      # Mask2Former computer vision segmentation engine
│
├── Results/
│   ├── BI_Results_OSM.py            # CSV exporter for OSM criteria
│   ├── BI_Results_SVI.py            # CSV exporter for SVI criteria
│   ├── BI_Results_Elevation.py      # CSV exporter for Elevation criteria
│   ├── BI_Results_Congestion.py     # CSV exporter for Congestion criteria
│   └── BI_Results_AQI.py            # CSV exporter for AQI criteria
│
└── Graph_Part/                      # Dijkstra routing & network graph generation scripts
```

---

## 🛠 Tech Stack & Dependencies

- **Language:** Python 3.10+
- **Geospatial & Graph Analysis:** `GeoPandas`, `OSMnx`, `Shapely`, `NetworkX`
- **Data Manipulation:** `pandas`, `numpy`
- **Computer Vision / AI:** PyTorch, Hugging Face Transformers (`Mask2Former`)
- **Plotting & Visualization:** `matplotlib`

---

## 🚀 Getting Started

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

---

## 📜 License & Citation

Developed as part of a Bachelor's Thesis on data-driven bicycle mobility planning at the University of Würzburg. Feel free to use and adapt the code for academic and open-source geospatial research.