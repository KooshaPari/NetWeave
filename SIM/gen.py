import torch
from PIL import Image
from diffusers import StableDiffusionControlNetImg2ImgPipeline, ControlNetModel

device = "cuda"

# 1) Load the ControlNet for MLSD (roads, lines, etc.) in float16
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-mlsd", torch_dtype=torch.float16
).to(device)

# 2) Load the corresponding Img2Img ControlNet pipeline
pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch.float16
).to(device)

# 3) Prepare your images
#    (a) The init image (rough sketch or actual photo you want to transform)
init_image = (
    Image.open("dataset/train/control/Cairo_1.png").convert("RGB").resize((512, 512))
)

#    (b) The control image (the "map" or line drawing for guidance)
control_image = (
    Image.open("dataset/train/control/Buenos Aires_0.png")
    .convert("RGB")
    .resize((512, 512))
)


# 4) Run the pipeline
prompt = "OpenStreetMap Satellite View Rendering of a City. Input: A fixed-sketch of the roads of the city, You must adhere and maintain this roadnetwork and not add or remove roads. Output: A map view of the city with space filled with elements like parks buildings and other city assets. Colors of Roads correspond to the type of road. Artistic Style: OpenStreetMap Satellite View Rendering of a City."
result = pipe(
    prompt=prompt,
    image=init_image,  # The init image
    control_image=control_image,  # The line-based or map-based guidance
    strength=0.7,  # How strongly to transform the init image
    num_inference_steps=600,
    guidance_scale=12,
)

# 5) Save or view the result
result.images[0].save("controlnet_img2img_output.png")
