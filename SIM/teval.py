import torch
from transformers import CLIPTextModel, CLIPTokenizer
from diffusers import ControlNetModel
from PIL import Image
from diffusers import StableDiffusionControlNetPipeline

import numpy as np

device = "cuda"

# 1. Load the correct CLIP text encoder & tokenizer for SD1.x (768-dim)
tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
text_encoder = CLIPTextModel.from_pretrained("openai/clip-vit-large-patch14").to(device)

# 2. Tokenize and encode your prompt -> shape [batch_size, seq_len, 768]
prompt = "A non-photo-realistic road network map."
text_inputs = tokenizer(prompt, return_tensors="pt")
text_inputs = {k: v.to(device) for k, v in text_inputs.items()}

with torch.no_grad():
    encoder_hidden_states = text_encoder(text_inputs["input_ids"])[0]
    encoder_hidden_states = encoder_hidden_states.to(dtype=torch.float16)
    # encoder_hidden_states.shape == [1, seq_len, 768]

# 3. Load ControlNet
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-mlsd", torch_dtype=torch.float16
).to(device)
controlnet.eval()


# 4. Create or load your control image (3 channels). Must match model.dtype (float16).
def load_mlsd_image(path):
    img = Image.open(path).convert("RGB").resize((1024, 1024))
    img_arr = np.array(img).astype(np.float32) / 255.0
    tensor = torch.from_numpy(img_arr).permute(2, 0, 1).unsqueeze(0)
    return tensor


control_image = load_mlsd_image("dataset/val/control/Seoul_2.png")

control_image = control_image.to(device, dtype=torch.float16)

# 5. Prepare latents (example size)
latents = torch.randn((1, 4, 128, 128), device="cuda", dtype=torch.float16)

# 6. Forward pass with correct shapes
with torch.no_grad():
    down_block_res, mid_block_res = controlnet(
        sample=latents,
        timestep=torch.tensor([999], device=device),
        encoder_hidden_states=encoder_hidden_states,  # correct 768-dim text embeddings
        controlnet_cond=control_image,  # shape [1, 3, H, W]
        conditioning_scale=1.0,
    )

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-mlsd", torch_dtype=torch.float16
).to("cuda")

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch.float16
).to("cuda")

# Inference
image = pipe(
    "A non-photo-realistic road network map.",
    control_image=Image.open("dataset/val/control/Seoul_2.png").convert("RGB"),
    num_inference_steps=30,
    guidance_scale=7.5,
).images[0]

image.save("out.png")
# Now 'down_block_res' and 'mid_block_res' hold the ControlNet outputs
print("ControlNet forward pass successful!")
