import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from shapely.geometry import box, Point, LineString
import random
from PIL import Image
from tqdm import tqdm
import warnings
import time
import multiprocessing
from multiprocessing import Pool
import numpy as np
from typing import Dict, List, Tuple
import traceback

warnings.filterwarnings("ignore")


########################################
# Safe parser for lanes and maxspeed
########################################
def parse_int_attribute(value, default=1):
    """Safely parse numeric attributes from an OSM tag that might be a list or string."""
    try:
        # If it's a list, convert to single value
        if isinstance(value, list):
            # Filter out empty or None values
            value = [str(v).strip() for v in value if v is not None and str(v).strip()]
            if not value:
                return default
            value = value[0]  # Take first non-empty value

        # Convert to string to handle mixed types
        value_str = str(value).strip()

        # Extract digits
        digits = "".join(ch for ch in value_str if ch.isdigit())

        # Return extracted digits or default
        return int(digits) if digits else default

    except Exception:
        return default


########################################
# Road & Property Styles
########################################
class RoadProperties:
    ROAD_HIERARCHY = {
        "motorway": {"width": 4.0, "speed": 120, "color": "#333333"},
        "trunk": {"width": 3.5, "speed": 100, "color": "#444444"},
        "primary": {"width": 3.0, "speed": 80, "color": "#555555"},
        "secondary": {"width": 2.5, "speed": 60, "color": "#666666"},
        "tertiary": {"width": 2.0, "speed": 50, "color": "#777777"},
        "residential": {"width": 1.5, "speed": 30, "color": "#888888"},
        "unclassified": {"width": 1.5, "speed": 30, "color": "#999999"},
    }
    PROPERTY_TYPES = {
        "residential": {"weight": 0.5, "color": "#A5D6A7"},
        "commercial": {"weight": 0.3, "color": "#90CAF9"},
        "industrial": {"weight": 0.2, "color": "#FFAB91"},
    }


########################################
# Generate Road Style for CONTROL image
########################################
def get_control_line_style(data: dict) -> Tuple[str, float, str]:
    """Safely generate line style for road network control image."""
    try:
        # Safely extract highway type
        highway_type = str(data.get("highway", "unclassified")).lower()
        highway_type = (
            highway_type
            if highway_type in RoadProperties.ROAD_HIERARCHY
            else "unclassified"
        )

        # Safely parse lanes
        lanes = parse_int_attribute(data.get("lanes", 1), default=1)

        # Safely parse maxspeed and other attributes
        max_speed = data.get("maxspeed", None)
        oneway = str(data.get("oneway", "no")).lower()
        roundabout = str(data.get("junction", "")).lower() == "roundabout"

        color_map = {
            "motorway": "red",
            "trunk": "orange",
            "primary": "yellow",
            "secondary": "green",
            "tertiary": "blue",
            "residential": "purple",
            "unclassified": "brown",
        }
        color = color_map.get(highway_type, "black")

        # Base linewidth depends on lanes
        base_linewidth = 1.0 + 0.3 * lanes

        # Roundabout -> dashed
        linestyle = "-"
        if roundabout:
            linestyle = (0, (2, 2))

        # Oneway -> dotted
        if oneway == "yes":
            linestyle = (0, (1, 2))

        # If max_speed > 80, slightly thicken
        if max_speed:
            speed_val = parse_int_attribute(max_speed, default=50)
            if speed_val > 80:
                base_linewidth += 1

        return (color, base_linewidth, linestyle)

    except Exception as e:
        print(f"Error in get_control_line_style: {e}")
        return ("black", 1.0, "-")


########################################
# Border Nodes & Connectivity
########################################
def get_border_nodes(G: nx.Graph, polygon) -> List[int]:
    """Find nodes at the border of a given polygon."""
    minx, miny, maxx, maxy = polygon.bounds
    margin = 0.0001
    border_nodes = []
    for node, data in G.nodes(data=True):
        lat, lon = data["y"], data["x"]
        if (
            abs(lat - miny) < margin
            or abs(lat - maxy) < margin
            or abs(lon - minx) < margin
            or abs(lon - maxx) < margin
        ):
            border_nodes.append(node)
    return border_nodes


def validate_network_connectivity(G: nx.Graph, polygon) -> bool:
    """Validate the connectivity of the road network."""
    border_nodes = get_border_nodes(G, polygon)
    if len(border_nodes) < 2:
        return False
    if not nx.is_connected(G):
        return False
    for i, start in enumerate(border_nodes[:-1]):
        path_exists = False
        for end in border_nodes[i + 1 :]:
            if nx.has_path(G, start, end):
                path_exists = True
                break
        if not path_exists:
            return False
    return True


########################################
# Generate Random Property Points
########################################
def generate_properties(G: nx.Graph) -> List[Dict]:
    """Generate random property points along the road network."""
    properties = []
    edges = list(G.edges(data=True))
    num_properties = max(5, len(edges) // 3)

    for _ in range(num_properties):
        edge = random.choice(edges)
        start = Point(G.nodes[edge[0]]["x"], G.nodes[edge[0]]["y"])
        end = Point(G.nodes[edge[1]]["x"], G.nodes[edge[1]]["y"])
        line = LineString([start, end])

        distance = random.random()
        point = line.interpolate(distance, normalized=True)

        prop_type = random.choices(
            list(RoadProperties.PROPERTY_TYPES.keys()),
            weights=[p["weight"] for p in RoadProperties.PROPERTY_TYPES.values()],
        )[0]

        properties.append(
            {
                "type": prop_type,
                "position": (point.x, point.y),
                "size": random.randint(1, 5),
                "edge": edge[:2],
            }
        )
    return properties


########################################
# Process Single City Sample
########################################
def get_road_type(highway_data):
    """Safely extract road type from highway data."""
    if isinstance(highway_data, list):
        # Filter out empty or None values
        highway_data = [str(h).lower().strip() for h in highway_data if h]
        if not highway_data:
            return "unclassified"
        # Prioritize most specific road type
        road_type_priority = [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "unclassified",
        ]
        for road_type in road_type_priority:
            if any(road_type in h for h in highway_data):
                return road_type
        return highway_data[0]

    # If it's not a list, convert to string
    road_type = str(highway_data).lower().strip()
    return road_type if road_type in RoadProperties.ROAD_HIERARCHY else "unclassified"


def process_city_sample(args):
    """Process a single city sample, generating road network and property visualizations."""
    try:
        plt.ioff()  # Turn off interactive plotting
        city, i, output_dir, size = args

        # Safely extract city coordinates
        lat = float(city["lat"]) + random.uniform(-0.009, 0.009)
        lon = float(city["lon"]) + random.uniform(-0.009, 0.009)

        delta = 0.01
        sample_box = box(lon - delta, lat - delta, lon + delta, lat + delta)

        # Download road network
        custom_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"]'

        try:
            G = ox.graph_from_polygon(
                sample_box,
                network_type="all",
                custom_filter=custom_filter,
                simplify=True,
            )
            G = G.to_undirected()
        except Exception as network_error:
            print(
                f"Network download error for {city['city']} sample {i}: {network_error}"
            )
            return None

        # print(f"Edges: {len(G.edges())}, Nodes: {len(G.nodes())}")

        # Check connectivity
        if not validate_network_connectivity(G, sample_box):
            print(f"Skipping {city['city']} sample {i}: Network not connected")
            return None

        # Generate random property points
        # print("Generating properties...")
        properties = generate_properties(G)
        # print(f"Properties: {len(properties)}")

        city_name = str(city["city"])
        sample_id = f"{city_name}_{i}"

        # 1) CONTROL IMAGE
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_facecolor("white")
        # print("Drawing control image...")

        # Safely draw road network
        for u, v, data in G.edges(data=True):
            try:
                color, linewidth, linestyle = get_control_line_style(data)
                edge_coords = [
                    (G.nodes[u]["x"], G.nodes[u]["y"]),  # (lon, lat)
                    (G.nodes[v]["x"], G.nodes[v]["y"]),  # (lon, lat)
                ]
                ax.plot(
                    *zip(*edge_coords),
                    color=color,
                    linewidth=linewidth,
                    linestyle=linestyle,
                    solid_capstyle="round",
                )
            except Exception as edge_error:
                print(f"Error drawing edge: {edge_error}")

        ax.axis("off")
        control_path = Path(output_dir) / "control" / f"{sample_id}.png"
        fig.savefig(control_path, bbox_inches="tight", pad_inches=0, dpi=size / 8)
        plt.close(fig)
        # print(f"Control image saved: {control_path}")

        # 2) TARGET IMAGE
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_facecolor("white")
        ax.set_aspect("equal", "box")

        # print("Fetching buildings...")
        try:
            buildings = ox.features.features_from_polygon(
                sample_box, tags={"building": True}
            )
            # print(f"Buildings: {len(buildings)}")
        except Exception as buildings_error:
            print(f"Error fetching buildings: {buildings_error}")
            buildings = None

        # Plot building polygons
        if buildings is not None and not buildings.empty:
            for _, row in buildings.iterrows():
                try:
                    # print("Plotting building...")
                    geom = row.geometry
                    if geom.geom_type in ["Polygon", "MultiPolygon"]:
                        if geom.geom_type == "Polygon":
                            xs, ys = geom.exterior.xy
                            ax.fill(xs, ys, color="#CCCCCC", alpha=0.5, zorder=0)
                        else:
                            for subgeom in geom.geoms:
                                xs, ys = subgeom.exterior.xy
                                ax.fill(xs, ys, color="#CCCCCC", alpha=0.5, zorder=0)
                except Exception as building_plot_error:
                    print(f"Error plotting building: {building_plot_error}")

        # Draw roads with hierarchy styling
        for u, v, data in G.edges(data=True):
            # Safely extract road type
            road_type = get_road_type(data.get("highway", "unclassified"))

            # Get road style with fallback
            style = RoadProperties.ROAD_HIERARCHY.get(
                road_type, RoadProperties.ROAD_HIERARCHY["unclassified"]
            )

            edge_coords = [
                (G.nodes[u]["x"], G.nodes[u]["y"]),  # (lon, lat)
                (G.nodes[v]["x"], G.nodes[v]["y"]),  # (lon, lat)
            ]
            ax.plot(
                *zip(*edge_coords),
                color=style["color"],
                linewidth=style["width"],
                solid_capstyle="round",
                zorder=1,
            )

        ax.axis("off")
        target_path = Path(output_dir) / "target" / f"{sample_id}.png"
        fig.savefig(target_path, bbox_inches="tight", pad_inches=0, dpi=size / 8)
        plt.close(fig)
        # print(f"Target image saved: {target_path}")

        # 3) Resize & Save
        for path in [control_path, target_path]:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                img.save(path, quality=95)

        # Return sample metadata
        return {
            "sample_id": sample_id,
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "road_count": len(G.edges()),
            "node_count": len(G.nodes()),
            "border_nodes": len(get_border_nodes(G, sample_box)),
            "properties": len(properties),
        }

    except Exception as e:
        print(f"Detailed error in {city.get('city', 'Unknown')} sample {i}:")
        print(traceback.format_exc())
        return None


########################################
# Main Collector Class
########################################
class RoadNetworkDataCollector:
    def __init__(self, output_dir: str, size: int = 512):
        self.output_dir = Path(output_dir)
        self.size = size
        self.setup_directories()

        # Configure OSMnx
        ox.settings.log_console = False
        ox.settings.use_cache = True
        ox.settings.timeout = 60  # Increased timeout
        ox.settings.memory = True

    def setup_directories(self):
        for dir_name in ["control", "target", "metadata"]:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)

    def collect_from_cities(self, cities_file: str, samples_per_city: int = 10):
        cities = pd.read_csv(cities_file)
        total_samples = len(cities) * samples_per_city
        print(f"Starting collection of {total_samples} samples...")

        args_list = []
        for _, city in cities.iterrows():
            for i in range(samples_per_city):
                args_list.append((city, i, str(self.output_dir), self.size))

        metadata = []
        start_time = time.time()
        completed = 0

        # Use (CPU cores - 1) to avoid overload
        num_processes = max(1, multiprocessing.cpu_count() - 1)
        with Pool(processes=num_processes) as pool:
            for result in tqdm(
                pool.imap_unordered(process_city_sample, args_list),
                total=len(args_list),
            ):
                if result:
                    metadata.append(result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--size", type=int, default=512)
    args = parser.parse_args()

    collector = RoadNetworkDataCollector(args.output_dir, size=args.size)
    collector.collect_from_cities("cities.csv", samples_per_city=args.samples)
