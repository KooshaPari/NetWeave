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
import os
import numpy as np
from typing import Dict, List, Tuple

warnings.filterwarnings("ignore")


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


def get_border_nodes(G: nx.Graph) -> List[int]:
    """Identify nodes that lie on the border of the graph"""
    bbox = ox.utils_geo.bbox_from_point(
        (G.graph["center_lat"], G.graph["center_lng"]), dist=G.graph["dist"]
    )
    border_nodes = []

    for node, data in G.nodes(data=True):
        lat, lon = data["y"], data["x"]
        # Check if node is within small distance of boundary
        margin = 0.0001  # Adjust based on your scale
        if (
            abs(lat - bbox[0]) < margin
            or abs(lat - bbox[1]) < margin
            or abs(lon - bbox[2]) < margin
            or abs(lon - bbox[3]) < margin
        ):
            border_nodes.append(node)

    return border_nodes


def validate_network_connectivity(G: nx.Graph) -> bool:
    """Validate network has sufficient border connections and connectivity"""
    border_nodes = get_border_nodes(G)

    if len(border_nodes) < 2:
        return False

    # Check if graph is connected
    if not nx.is_connected(G):
        return False

    # Check connectivity between border points
    for i, start in enumerate(border_nodes[:-1]):
        path_exists = False
        for end in border_nodes[i + 1 :]:
            if nx.has_path(G, start, end):
                path_exists = True
                break
        if not path_exists:
            return False

    return True


def generate_properties(G: nx.Graph) -> List[Dict]:
    """Generate properties along the road network"""
    properties = []
    edges = list(G.edges(data=True))

    # Determine number of properties based on network size
    num_properties = max(5, len(edges) // 3)

    for _ in range(num_properties):
        # Select random edge
        edge = random.choice(edges)

        # Get point along edge
        start = Point(G.nodes[edge[0]]["x"], G.nodes[edge[0]]["y"])
        end = Point(G.nodes[edge[1]]["x"], G.nodes[edge[1]]["y"])
        line = LineString([start, end])

        # Random point along edge
        distance = random.random()
        point = line.interpolate(distance, normalized=True)

        # Determine property type
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


def process_city_sample(args):
    """Process a single sample for a city with enhanced validation and properties"""
    city, i, output_dir, size = args
    try:
        plt.ioff()

        # Get coordinates with jitter
        lat = city["lat"] + random.uniform(-0.009, 0.009)
        lon = city["lon"] + random.uniform(-0.009, 0.009)

        # Create bounding box
        delta = 0.0045
        sample_box = box(lon - delta, lat - delta, lon + delta, lat + delta)

        # Get road network with custom filter
        custom_filter = (
            '["highway"~"motorway|trunk|primary|'
            'secondary|tertiary|residential|unclassified"]'
        )
        G = ox.graph_from_polygon(
            sample_box,
            network_type="drive",
            custom_filter=custom_filter,
            simplify=True,
        )

        # Validate network
        if not validate_network_connectivity(G):
            return None

        # Generate properties
        properties = generate_properties(G)

        city_name = city["city"]
        sample_id = f"{city_name}_{i}"

        # Create and save control image (sketch)
        fig, ax = plt.subplots(figsize=(8, 8))
        ox.plot_graph(
            G,
            ax=ax,
            node_size=0,
            edge_color="black",
            edge_linewidth=2,
            bgcolor="white",
            show=False,
        )
        ax.axis("off")

        control_path = Path(output_dir) / "control" / f"{sample_id}.png"
        fig.savefig(control_path, bbox_inches="tight", pad_inches=0, dpi=size / 8)
        plt.close(fig)

        # Create target image with road hierarchy and properties
        fig, ax = plt.subplots(figsize=(8, 8))

        # Draw roads with hierarchy
        for u, v, data in G.edges(data=True):
            road_type = data.get("highway", "unclassified")
            style = RoadProperties.ROAD_HIERARCHY.get(
                road_type, RoadProperties.ROAD_HIERARCHY["unclassified"]
            )

            edge_coords = [
                (G.nodes[u]["y"], G.nodes[u]["x"]),
                (G.nodes[v]["y"], G.nodes[v]["x"]),
            ]

            ax.plot(
                *zip(*edge_coords),
                color=style["color"],
                linewidth=style["width"],
                solid_capstyle="round",
                zorder=1,
            )

        # Draw properties
        for prop in properties:
            ax.scatter(
                prop["position"][1],
                prop["position"][0],
                c=RoadProperties.PROPERTY_TYPES[prop["type"]]["color"],
                s=30 * prop["size"],
                zorder=2,
            )

        ax.axis("off")

        target_path = Path(output_dir) / "target" / f"{sample_id}.png"
        fig.savefig(target_path, bbox_inches="tight", pad_inches=0, dpi=size / 8)
        plt.close(fig)

        # Process images
        for path in [control_path, target_path]:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                img.save(path, quality=95)

        return {
            "sample_id": sample_id,
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "road_count": len(G.edges()),
            "node_count": len(G.nodes()),
            "border_nodes": len(get_border_nodes(G)),
            "properties": len(properties),
        }

    except Exception as e:
        print(f"Error in {city['city']} sample {i}: {str(e)}")
        return None


class RoadNetworkDataCollector:
    def __init__(self, output_dir: str, size: int = 512):
        self.output_dir = Path(output_dir)
        self.size = size
        self.setup_directories()

        # Configure OSMnx
        ox.settings.log_console = False
        ox.settings.use_cache = True
        ox.settings.timeout = 30
        ox.settings.memory = True

    def setup_directories(self):
        for dir_name in ["control", "target", "metadata"]:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)

    def collect_from_cities(self, cities_file: str, samples_per_city: int = 10):
        cities = pd.read_csv(cities_file)
        total_samples = len(cities) * samples_per_city
        print(f"Starting collection of {total_samples} samples...")

        # Prepare arguments for multiprocessing
        args_list = []
        for _, city in cities.iterrows():
            for i in range(samples_per_city):
                args_list.append((city, i, str(self.output_dir), self.size))

        # Process samples using multiprocessing
        metadata = []
        start_time = time.time()
        completed = 0

        # Use number of CPU cores minus 1 to avoid overloading
        num_processes = max(1, multiprocessing.cpu_count() - 1)

        with Pool(processes=num_processes) as pool:
            for result in tqdm(
                pool.imap_unordered(process_city_sample, args_list),
                total=len(args_list),
            ):
                if result:
                    metadata.append(result)
                    completed += 1

                    # Calculate and show progress
                    if completed % 10 == 0:  # Update every 10 samples
                        elapsed_time = time.time() - start_time
                        avg_time = elapsed_time / completed
                        remaining = total_samples - completed
                        eta_hours = (remaining * avg_time) / 3600

                        print(f"\nCompleted {completed}/{total_samples} samples")
                        print(f"Average time per sample: {avg_time:.1f}s")
                        print(f"Estimated time remaining: {eta_hours:.1f} hours")

        # Save metadata
        pd.DataFrame(metadata).to_csv(
            self.output_dir / "metadata" / "samples.csv", index=False
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--size", type=int, default=512)
    args = parser.parse_args()

    collector = RoadNetworkDataCollector(args.output_dir, size=args.size)
    collector.collect_from_cities("cities.csv", samples_per_city=args.samples)
