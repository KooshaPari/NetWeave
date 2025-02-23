import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T
from typing import Dict, List, Tuple
import os


class RoadNetworkInference:
    def __init__(self, model_path: str):
        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available() else "cpu"
        )
        self.model = torch.load(model_path, map_location=self.device)
        self.model.eval()

        self.transform = T.Compose(
            [T.Resize((256, 256)), T.ToTensor(), T.Normalize(mean=[0.5], std=[0.5])]
        )

    def preprocess_sketch(self, sketch_path: str) -> torch.Tensor:
        """Convert image to tensor"""
        img = Image.open(sketch_path).convert("L")  # Convert to grayscale
        tensor = self.transform(img).unsqueeze(0)
        return tensor.to(self.device)

    def generate_road_network(self, sketch_tensor: torch.Tensor) -> torch.Tensor:
        """Generate road network from sketch tensor"""
        with torch.no_grad():
            output = self.model(sketch_tensor)
        return output

    def postprocess_output(self, output_tensor: torch.Tensor) -> Dict[str, List[Dict]]:
        """Convert model output to road network structure"""
        road_map = (output_tensor > 0.5).float().cpu().numpy()[0, 0]
        roads = self._extract_road_segments(road_map)
        return self._convert_to_paperjs_format(roads)

def main():
    # Example usage
    inference = RoadNetworkInference("path_to_your_model.pth")

    # Process a test image
    sketch_tensor = inference.preprocess_sketch("path_to_test_sketch.png")
    output = inference.generate_road_network(sketch_tensor)
    road_network = inference.postprocess_output(output)

    print("Generated Road Network Structure:")
    print(f"Number of segments: {len(road_network['segments'])}")
    print(f"Number of junctions: {len(road_network['junctions'])}")


if __name__ == "__main__":
    main()
