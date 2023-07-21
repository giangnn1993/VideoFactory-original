import os
import sys
import json
import webuiapi

from PIL import PngImagePlugin

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from image import ImageGenerator
except ImportError:
    # Handle the case where the module cannot be imported
    ImageGenerator = None
    # Log an error or raise an exception, as appropriate


class AutomaticImage(ImageGenerator):
    def __init__(self) -> None:
        super().__init__('automatic1111')

    def generate_image_from_text(
            self,
            prompt: str,
            negative_prompt: str = None,
            sd_model_checkpoint: str = None,
            CLIP_stop_at_last_layers: int = 1,
            output_path: str = 'automatic1111_image.png',
            ) -> str:

        if negative_prompt is None:
            negative_prompt = "people in the background, nipple, wearing facemask, sketches, (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, bad anatomy,(long hair:1.4),DeepNegative,(fat:1.2),facing away, looking away,tilted head, lowres,bad anatomy,bad hands, text, error, missing fingers,extra digit, fewer digits, cropped, worstquality, low quality, normal quality,jpegartifacts,signature, watermark, username,blurry,bad feet,cropped,poorly drawn hands,poorly drawn face,mutation,deformed,worst quality,low quality,normal quality,jpeg artifacts,signature,watermark,extra fingers,fewer digits,extra limbs,extra arms,extra legs,malformed limbs,fused fingers,too many fingers,long neck,cross-eyed,mutated hands,polar lowres,bad body,bad proportions,gross proportions,text,error,missing fingers,missing arms,missing legs,extra digit, extra arms, extra leg, extra foot,bhands-neg, ([bad-hands-5:0.6]:1.331), bhands:0.5"  # noqa
        if sd_model_checkpoint is None:
            sd_model_checkpoint = "juggernaut_final.safetensors [88967f03f2]"

        # create API client
        api = webuiapi.WebUIApi()
        result1 = api.txt2img(
            prompt=prompt,
            negative_prompt=negative_prompt,
            denoising_strength=0.3,
            seed=-1,
            cfg_scale=7,
            sampler_name='DPM++ 2M Karras',
            steps=25,
            batch_size=1,
            width=540,
            height=960,
            enable_hr=True,
            hr_scale=1,
            hr_upscaler=webuiapi.HiResUpscaler.Latent,
            # hr_second_pass_steps=20,
            # hr_resize_x=1080,
            # hr_resize_y=1920,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "CLIP_stop_at_last_layers": CLIP_stop_at_last_layers
            }
        )
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", json.dumps(result1.info))
        result1.image.save(output_path, pnginfo=pnginfo)

        return output_path


# # Usage:
# # To use the automaticImage class, create an instance:
# image_generator = automaticImage()
# # Then, call the generate_image_from_text method to generate image from text:
# image_generator.generate_image_from_text(prompt='An old monk')
