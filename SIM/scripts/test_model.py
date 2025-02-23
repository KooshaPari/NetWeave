import torch
from PIL import Image
import numpy as np
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from diffusers import UniPCMultistepScheduler


def load_image(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    image = np.array(image)
    image = torch.from_numpy(image).float() / 127.5 - 1
    return image.permute(2, 0, 1).unsqueeze(0)


def test_model(
    checkpoint_path: str,
    test_image_path: str,
    output_path: str,
    prompt: str = "detailed road map",
):
    # Load ControlNet
    controlnet = ControlNetModel.from_pretrained(
        checkpoint_path, torch_dtype=torch.float16
    )

    # Load pipeline
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
    )

    # Use efficient attention
    pipe.enable_xformers_memory_efficient_attention()

    # Use better scheduler
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    # Move to GPU
    pipe.to("cuda")

    # Load and process test image
    control_image = load_image(test_image_path)

    # Generate image
    output_image = pipe(
        prompt, control_image, num_inference_steps=30, guidance_scale=9.0
    ).images[0]

    # Save output
    output_image.save(output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--test-image", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--prompt", type=str, default="detailed road map")
    args = parser.parse_args()

    test_model(args.checkpoint, args.test_image, args.output, args.prompt)
