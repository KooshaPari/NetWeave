import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.graph import route_through_array


class RoadNetworkCleaner:
    def __init__(self):
        self.min_road_length = 20
        self.intersection_radius = 5
        self.height = None
        self.width = None

    def process_sketch(self, sketch_img):
        print(f"Processing sketch with initial shape: {sketch_img.shape}")

        # Convert to binary if needed and set dimensions
        if len(sketch_img.shape) > 2:
            sketch_img = cv2.cvtColor(sketch_img, cv2.COLOR_BGR2GRAY)
        self.height, self.width = sketch_img.shape
        print(f"Working with dimensions: {self.width}x{self.height}")

        # Create binary image
        _, binary = cv2.threshold(sketch_img, 127, 255, cv2.THRESH_BINARY)
        print("Binary conversion complete")

        # Get skeleton
        skeleton = skeletonize(binary > 0)
        print("Skeletonization complete")

        # Find network points
        endpoints, intersections = self.find_network_points(skeleton)
        print(
            f"Found {len(endpoints)} endpoints and {len(intersections)} intersections"
        )

        # Remove spurious roads
        cleaned_network = self.remove_spurious_roads(skeleton, endpoints, intersections)
        print("Spurious road removal complete")

        return cleaned_network


def visualize_cleanup(original, cleaned):
    """Helper to visualize the cleaning process"""
    # Convert to RGB
    orig_rgb = cv2.cvtColor(original, cv2.COLOR_GRAY2RGB)
    clean_rgb = cv2.cvtColor((cleaned * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)

    # Draw endpoints and intersections on cleaned
    endpoints, intersections = RoadNetworkCleaner().find_network_points(cleaned)

    for point in endpoints:
        cv2.circle(clean_rgb, point, 3, (255, 0, 0), -1)  # Red for endpoints

    for point in intersections:
        cv2.circle(clean_rgb, point, 3, (0, 255, 0), -1)  # Green for intersections

    return np.hstack((orig_rgb, clean_rgb))


def process_road_sketch(input_path, output_path):
    print(f"\nProcessing road sketch from: {input_path}")

    # Read image
    sketch = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if sketch is None:
        raise ValueError(f"Could not read image at {input_path}")

    print(f"Loaded image with shape: {sketch.shape}")

    # Process
    cleaner = RoadNetworkCleaner()
    cleaned_network = cleaner.process_sketch(sketch)

    # Save result
    comparison = visualize_cleanup(sketch, cleaned_network)
    cv2.imwrite(output_path, comparison)
    print(f"Saved output to: {output_path}")

    return cleaned_network


def main():
    input_path = "dataset/val/control/example1.png"
    output_path = "cleaned_network.png"

    try:
        cleaned_network = process_road_sketch(input_path, output_path)
        print("\nProcessing complete!")
        print(f"Final network shape: {cleaned_network.shape}")
    except Exception as e:
        print(f"\nError processing road network:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        raise


if __name__ == "__main__":
    main()
