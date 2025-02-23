# road_network_cleaner.py
import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.graph import route_through_array


class RoadNetworkCleaner:
    def __init__(self):
        self.min_road_length = 20
        self.intersection_radius = 5

    def process_sketch(self, sketch_img):
        # Ensure we're working with correct dimensions
        self.height, self.width = sketch_img.shape[:2]

        # Convert to binary
        if len(sketch_img.shape) > 2:
            sketch_img = cv2.cvtColor(sketch_img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(sketch_img, 127, 255, cv2.THRESH_BINARY)

        # Get skeleton
        skeleton = skeletonize(binary > 0)

        # Find network points
        endpoints, intersections = self.find_network_points(skeleton)

        # Remove spurious roads with bounds checking
        cleaned_network = self.remove_spurious_roads(skeleton, endpoints, intersections)

        return cleaned_network

    def find_network_points(self, skeleton):
        endpoints = []
        intersections = []

        padded = np.pad(skeleton, pad_width=1, mode="constant", constant_values=0)

        # Use width and height from original image
        for y in range(1, self.height + 1):
            for x in range(1, self.width + 1):
                if padded[y, x]:
                    neighbors = padded[y - 1 : y + 2, x - 1 : x + 2].sum() - 1

                    if neighbors == 1:
                        endpoints.append((x - 1, y - 1))
                    elif neighbors > 2:
                        intersections.append((x - 1, y - 1))

        return endpoints, intersections

    def remove_spurious_roads(self, skeleton, endpoints, intersections):
        cleaned = skeleton.copy()

        for endpoint in endpoints:
            # Find closest intersection
            closest_dist = float("inf")
            closest_int = None

            for intersection in intersections:
                dist = np.sqrt(
                    (endpoint[0] - intersection[0]) ** 2
                    + (endpoint[1] - intersection[1]) ** 2
                )
                if dist < closest_dist:
                    closest_dist = dist
                    closest_int = intersection

            if closest_dist < self.min_road_length and closest_int is not None:
                try:
                    path = self.get_path(skeleton, endpoint, closest_int)
                    for py, px in path:  # Note: route_through_array returns (y,x)
                        if (
                            0 <= py < self.height and 0 <= px < self.width
                        ):  # Bounds check
                            cleaned[py, px] = False
                except Exception as e:
                    print(
                        f"Warning: Could not process path for endpoint {endpoint}: {e}"
                    )

        return cleaned

    def get_path(self, skeleton, start, end):
        # Create cost array
        cost_array = ~skeleton

        try:
            indices, _ = route_through_array(
                cost_array,
                start=(start[1], start[0]),  # Convert to (y,x)
                end=(end[1], end[0]),
                fully_connected=True,
            )
            return indices
        except Exception as e:
            print(f"Warning: Path finding failed: {e}")
            return []


def visualize_cleanup(original, cleaned):
    # Convert to 3 channel images
    orig_rgb = cv2.cvtColor(original, cv2.COLOR_GRAY2RGB)
    clean_rgb = cv2.cvtColor((cleaned * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)

    # Get network points
    cleaner = RoadNetworkCleaner()
    endpoints, intersections = cleaner.find_network_points(cleaned)

    # Draw points safely
    for point in endpoints:
        x, y = point
        if 0 <= x < clean_rgb.shape[1] and 0 <= y < clean_rgb.shape[0]:
            cv2.circle(clean_rgb, (x, y), 3, (255, 0, 0), -1)

    for point in intersections:
        x, y = point
        if 0 <= x < clean_rgb.shape[1] and 0 <= y < clean_rgb.shape[0]:
            cv2.circle(clean_rgb, (x, y), 3, (0, 255, 0), -1)

    return np.hstack((orig_rgb, clean_rgb))


# Test script
def process_road_sketch(input_path, output_path):
    # Read and process image
    sketch = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if sketch is None:
        raise ValueError(f"Could not read image at {input_path}")

    print(f"Processing image of size {sketch.shape}")

    cleaner = RoadNetworkCleaner()
    cleaned_network = cleaner.process_sketch(sketch)

    # Visualize and save
    comparison = visualize_cleanup(sketch, cleaned_network)
    cv2.imwrite(output_path, comparison)

    return cleaned_network


# Usage
def main():
    input_path = "image.png"
    output_path = "cleaned_network.png"

    try:
        cleaned_network = process_road_sketch(input_path, output_path)
        print("Processing complete. Check output at:", output_path)
    except Exception as e:
        print(f"Error processing road network: {e}")


if __name__ == "__main__":
    main()
