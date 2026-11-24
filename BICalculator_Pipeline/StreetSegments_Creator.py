import geopandas as gpd
from shapely.geometry import box, LineString, Point
import pyproj

# ============================================================
# PARAMETERS
# ============================================================
SEGMENT_LENGTH = 20.0          # target sub-segment length in metres
UTM_CRS        = "EPSG:32632"  # UTM zone 32N — covers Germany
WGS84_CRS      = "EPSG:4326"   # lon/lat — used by Mapillary
# ============================================================


class StreetSegmentsCreator:
    """
    Step 3 of the main pipeline.

    Accepts a SINGLE OSM way (one-row GeoDataFrame) and divides it into
    fixed-length sub-segments of SEGMENT_LENGTH metres, building an
    axis-aligned bbox around each sub-segment.

    The loop over OSM ways lives in BI_Pipeline.py — this class only
    knows about one way at a time.

    Output GeoDataFrame columns
    ---------------------------
    geometry     : bbox polygon (WGS84)
    sub_seg_idx  : position of this sub-segment within the OSM way (0-based)
    start_point  : WGS84 Point at the sub-segment start
    end_point    : WGS84 Point at the sub-segment end
    """

    def __init__(self, way_gdf, total_width):
        """
        Parameters
        ----------
        way_gdf     : GeoDataFrame — single-row GeoDataFrame for one OSM way
        total_width : float        — bbox padding width in metres
        """
        self.way_gdf     = way_gdf
        self.total_width = total_width + 2 * 2.5 # adding pavement width on both sides

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def create_segments(self):
        """
        Divides the single OSM way into sub-segments and returns a
        GeoDataFrame (WGS84) with one row per sub-segment.
        Returns None if the geometry is not a valid LineString.
        """
        way_geom = self.way_gdf.geometry.iloc[0]

        if way_geom.geom_type != "LineString":
            print(f"  Skipping — geometry type '{way_geom.geom_type}' is not a LineString.")
            return None

        # Project to UTM for metric calculations
        way_utm = (
            gpd.GeoDataFrame(geometry=[way_geom], crs=WGS84_CRS)
            .to_crs(UTM_CRS)
            .geometry.iloc[0]
        )

        utm_to_wgs84 = pyproj.Transformer.from_crs(UTM_CRS, WGS84_CRS, always_xy=True)

        way_length  = way_utm.length
        distance    = 0.0
        sub_seg_idx = 0
        rows        = []

        while distance < way_length:
            start_d = distance
            end_d   = min(distance + SEGMENT_LENGTH, way_length)

            sub_line = self._cut_line(way_utm, start_d, end_d)

            # Start / end points → WGS84
            start_wgs = Point(utm_to_wgs84.transform(*sub_line.coords[0]))
            end_wgs   = Point(utm_to_wgs84.transform(*sub_line.coords[-1]))

            # Axis-aligned bbox padded by total_width on each side
            minx, miny, maxx, maxy = sub_line.bounds
            half_w   = self.total_width / 2
            bbox_utm = box(
                minx - half_w, miny - half_w,
                maxx + half_w, maxy + half_w,
            )

            rows.append({
                "geometry":    bbox_utm,
                "sub_seg_idx": sub_seg_idx,
                "start_point": start_wgs,
                "end_point":   end_wgs,
            })

            distance    += SEGMENT_LENGTH
            sub_seg_idx += 1

        if not rows:
            print("  Warning: no sub-segments were created.")
            return None

        segments_utm = gpd.GeoDataFrame(rows, crs=UTM_CRS)
        segments_gdf = segments_utm.to_crs(WGS84_CRS)

        print(f"  {len(segments_gdf)} sub-segments created (~{SEGMENT_LENGTH} m each)")
        return segments_gdf

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _cut_line(self, line, start, end):
        """
        Returns the sub-LineString of `line` between metric distances
        `start` and `end` (measured along the line in UTM metres).
        """
        coords      = []
        accumulated = 0.0
        line_coords = list(line.coords)

        for i in range(len(line_coords) - 1):
            p1      = line_coords[i]
            p2      = line_coords[i + 1]
            seg_len = LineString([p1, p2]).length

            seg_start = accumulated
            seg_end   = accumulated + seg_len

            if seg_start <= start <= seg_end:
                t = (start - seg_start) / seg_len if seg_len > 0 else 0
                coords.append((p1[0] + t * (p2[0] - p1[0]),
                               p1[1] + t * (p2[1] - p1[1])))

            if start <= accumulated <= end:
                coords.append(p1)

            if seg_start <= end <= seg_end:
                t = (end - seg_start) / seg_len if seg_len > 0 else 0
                coords.append((p1[0] + t * (p2[0] - p1[0]),
                               p1[1] + t * (p2[1] - p1[1])))
                break

            accumulated += seg_len

        if len(coords) < 2:
            coords = [line_coords[-1], line_coords[-1]]

        return LineString(coords)