import os
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from pathlib import Path
from PIL import Image
import wandb
from diffusers import (
    ControlNetModel,
    AutoencoderKL,
    DDPMScheduler,
    UNet2DConditionModel,
)
from transformers import CLIPTextModel, CLIPTokenizer
from accelerate import Accelerator
from tqdm.auto import tqdm


class RoadNetworkDataset(Dataset):
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.control_dir = self.root_dir / "control"
        self.target_dir = self.root_dir / "target"
        self.samples = list(self.control_dir.glob("*.png"))

        # Updated transforms with proper normalization
        self.transform = transforms.Compose(
            [
                transforms.Resize(512),
                transforms.CenterCrop(512),
                transforms.ToTensor(),
                transforms.Normalize([0.5], [0.5]),  # Scale to [-1, 1]
            ]
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        control_path = self.samples[idx]
        target_path = self.target_dir / control_path.name

        return {
            "control": self.transform(Image.open(control_path).convert("RGB")),
            "target": self.transform(Image.open(target_path).convert("RGB")),
            "text": "a detailed road network map",
        }


def train_controlnet(
    dataset_path: str,
    output_dir: str,
    pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5",
    train_batch_size=1,
    num_train_epochs=100,
    gradient_accumulation_steps=4,
    learning_rate=1e-5,
):
    accelerator = Accelerator(
        gradient_accumulation_steps=gradient_accumulation_steps,
        mixed_precision="bf16",
    )
    # Initialize wandb
    wandb.init(project="netweave", name="controlnet-training")

    device = accelerator.device
    print(f"Using device: {device}")

    # Load models with correct initialization
    tokenizer = CLIPTokenizer.from_pretrained(
        pretrained_model_name_or_path, subfolder="tokenizer"
    )
    text_encoder = CLIPTextModel.from_pretrained(
        pretrained_model_name_or_path, subfolder="text_encoder"
    ).to(device)
    vae = AutoencoderKL.from_pretrained(
        pretrained_model_name_or_path, subfolder="vae"
    ).to(device)
    unet = UNet2DConditionModel.from_pretrained(
        pretrained_model_name_or_path, subfolder="unet"
    ).to(device)

    # Initialize ControlNet properly
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-scribble",
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
    ).to(device)

    noise_scheduler = DDPMScheduler.from_pretrained(
        pretrained_model_name_or_path, subfolder="scheduler"
    )

    # Freeze models
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    unet.requires_grad_(False)

    # Prepare dataset
    train_dataset = RoadNetworkDataset(dataset_path)
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=train_batch_size,
        shuffle=True,
        num_workers=4,
        persistent_workers=True,
    )

    # Optimizer
    optimizer = torch.optim.AdamW(
        controlnet.parameters(), lr=learning_rate, weight_decay=1e-2
    )

    # Prepare components with accelerator
    controlnet, optimizer, train_dataloader = accelerator.prepare(
        controlnet, optimizer, train_dataloader
    )

    # Training loop
    global_step = 0
    for epoch in range(num_train_epochs):
        controlnet.train()
        progress_bar = tqdm(train_dataloader, desc=f"Epoch {epoch}")

        for batch in progress_bar:
            with accelerator.accumulate(controlnet):
                # Process target images through VAE
                with torch.no_grad():
                    latents = vae.encode(batch["target"]).latent_dist.sample()
                    latents = latents * vae.config.scaling_factor

                # Keep control images in pixel space (3 channels)
                control_images = batch["control"]  # Already normalized to [-1, 1]

                # Sample noise
                noise = torch.randn_like(latents)
                timesteps = torch.randint(
                    0,
                    noise_scheduler.config.num_train_timesteps,
                    (latents.shape[0],),
                    device=device,
                )
                noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

                # Encode text
                text_inputs = tokenizer(
                    batch["text"],
                    padding="max_length",
                    max_length=tokenizer.model_max_length,
                    return_tensors="pt",
                    truncation=True,
                ).to(device)
                encoder_hidden_states = text_encoder(text_inputs.input_ids)[0]

                # Forward pass
                down_block_res_samples, mid_block_res_sample = controlnet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    controlnet_cond=control_images,
                    return_dict=False,
                )

                # UNet forward
                noise_pred = unet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    down_block_additional_residuals=down_block_res_samples,
                    mid_block_additional_residual=mid_block_res_sample,
                ).sample

                # Calculate loss
                loss = F.mse_loss(noise_pred.float(), noise.float(), reduction="mean")
                accelerator.backward(loss)

                if accelerator.sync_gradients:
                    accelerator.clip_grad_norm_(controlnet.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()

            # Logging
            if accelerator.is_main_process:
                wandb.log({"loss": loss.item(), "epoch": epoch, "step": global_step})
                global_step += 1

    # Save model
    accelerator.wait_for_everyone()
    if accelerator.is_main_process:
        controlnet.save_pretrained(os.path.join(output_dir, "controlnet"))

    wandb.finish()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    args = parser.parse_args()

    train_controlnet(
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )
