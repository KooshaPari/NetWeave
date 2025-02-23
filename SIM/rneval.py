import torch
import numpy as np
from pathlib import Path
from PIL import Image
import os
from torch.utils.data import DataLoader
from torchvision import transforms
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import safetensors.torch
from skimage.metrics import (
    structural_similarity as ssim,
    peak_signal_noise_ratio as psnr,
)

import torch.nn.functional as F


class TestDataset(torch.utils.data.Dataset):
    def __init__(self, control_dir: Path, target_dir: Path):
        self.control_dir = control_dir
        self.target_dir = target_dir
        self.samples = [
            f for f in os.listdir(control_dir) if f.endswith((".png", ".jpg"))
        ]
        print(f"Found {len(self.samples)} samples")

        # Common transform for both control and target
        self.transform = transforms.Compose(
            [
                transforms.Resize(512),
                # The `transforms` module in the code snippet is used to define a series of image transformations that will be applied to both the control and target images in the dataset before they are fed into the neural network model for evaluation.
                transforms.CenterCrop(512),
                transforms.ToTensor(),
                transforms.Normalize([0.5], [0.5]),  # For ControlNet
            ]
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample_name = self.samples[idx]

        # Load and transform control image
        control = Image.open(self.control_dir / sample_name).convert("RGB")
        control = self.transform(control)  # [3, 512, 512]

        # Load and transform target image
        target = Image.open(self.target_dir / sample_name).convert("RGB")
        target = self.transform(target)  # [3, 512, 512]

        return {"control": control, "target": target}


class ModelPaths:
    PROJECT_ROOT = Path("C:/Users/koosh/Dev/355/NetWeave/SIM")
    CONTROLNET_MODEL = (
        PROJECT_ROOT / "trained_model/controlnet/diffusion_pytorch_model.safetensors"
    )
    CONTROLNET_CONFIG = PROJECT_ROOT / "trained_model/controlnet/config.json"
    VAL_CONTROL = PROJECT_ROOT / "dataset/val/control"
    VAL_TARGET = PROJECT_ROOT / "dataset/val/target"


class RoadNetworkEvaluator:
    def __init__(self, model_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize with correct channel configuration
        self.controlnet = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-scribble",
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            use_safetensors=True,
        )

        # Load custom weights
        self.controlnet.load_state_dict(
            safetensors.torch.load_file(model_path), strict=False
        )
        self.controlnet.to(self.device).eval()

    @torch.no_grad()
    def evaluate_batch(self, val_loader):
        total_metrics = []

        for batch_idx, batch in enumerate(val_loader):
            print(f"\rEvaluating batch {batch_idx+1}/{len(val_loader)}", end="")

            control = batch["control"].to(self.device)
            target = batch["target"].to(self.device)

            # If using CUDA (which uses float16 for the model), convert inputs to half precision:
            if self.device.type == "cuda":
                control = control.half()
                target = target.half()  # Cast target as needed

            # Forward pass through ControlNet
            try:
                # Assume control is of shape [batch, channels, height, width]
                batch_size = control.shape[0]

                # Create a timestep tensor; here we use a constant value (e.g., 50) for all samples.
                # Ensure the timesteps are in the range expected by your diffusion process.
                timesteps = torch.full(
                    (batch_size,), 50, dtype=torch.long, device=self.device
                )

                # Create a control condition tensor (your example random noise).
                controlnet_cond = torch.randn_like(control)

                output = self.controlnet(
                    control,  # sample
                    timesteps,  # timestep
                    None,  # encoder_hidden_states
                    controlnet_cond,  # controlnet_cond
                    1.0,  # conditioning_scale
                    False,  # return_dict
                )
                # Get feature maps
                if isinstance(output, tuple):
                    down_block_res_samples, mid_block_res_sample = output
                    generated = down_block_res_samples[-1]  # Use last feature map
                else:
                    generated = output.sample  # If return_dict=True

                # Normalize to 0-1 range
                generated = (generated - generated.min()) / (
                    generated.max() - generated.min()
                )

                # Resize if needed
                if generated.shape != target.shape:
                    generated = F.interpolate(generated, size=target.shape[2:])

                # Compute metrics for each image in batch
                for i in range(len(control)):
                    metrics = self.compute_metrics(generated[i], target[i])
                    total_metrics.append(metrics)

            except Exception as e:
                print(f"\nError processing batch {batch_idx}: {e}")
                continue

        # Compute average metrics
        avg_metrics = {}
        for key in total_metrics[0].keys():
            avg_metrics[key] = np.mean([m[key] for m in total_metrics])

        return avg_metrics

    def compute_metrics(self, generated: torch.Tensor, target: torch.Tensor):
        """Compute multiple evaluation metrics"""
        generated = generated.cpu().numpy()
        target = target.cpu().numpy()

        metrics = {
            "ssim": ssim(generated, target, data_range=1.0),
            "psnr": psnr(target, generated, data_range=1.0),
            "mse": np.mean((generated - target) ** 2),
            "mae": np.mean(np.abs(generated - target)),
        }

        return metrics


def main():
    print("Starting evaluation...")

    # Create dataset and loader
    dataset = TestDataset(ModelPaths.VAL_CONTROL, ModelPaths.VAL_TARGET)
    val_loader = DataLoader(dataset, batch_size=4, shuffle=False)

    # Create evaluator
    evaluator = RoadNetworkEvaluator(
        str(ModelPaths.CONTROLNET_MODEL), str(ModelPaths.CONTROLNET_CONFIG)
    )

    # Run evaluation
    print("\nRunning evaluation...")
    metrics = evaluator.evaluate_batch(val_loader)

    # Print results
    print("\n\nEvaluation Results:")
    print("-" * 40)
    for metric, value in metrics.items():
        print(f"{metric:>10}: {value:.4f}")


if __name__ == "__main__":
    main()
