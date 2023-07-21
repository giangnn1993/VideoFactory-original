from .apis.image.automatic1111_image import AutomaticImage


class ImageGenerator:
    IMGGEN_CLASSES = {
        'automatic1111': AutomaticImage,
    }

    def __init__(self, imggen_provider):
        self.imggen_provider = imggen_provider
        self.imggen = self._create_imggen_instance()

    def _create_imggen_instance(self):
        ImgGenClass = self.IMGGEN_CLASSES.get(self.imggen_provider)
        if ImgGenClass is None:
            raise ValueError(f'Unsupported image generator: {self.imggen_provider}')
        return ImgGenClass()

    def generate_image_from_text(self, prompt: str, output_path: str = None, **kwargs) -> str:
        return self.imggen.generate_image_from_text(prompt=prompt, output_path=output_path, **kwargs)


# # Usage:
# # To use the ImageGenerator class, create an instance:
# imggen1 = ImageGenerator('automatic1111')
# # Then, call the generate_image_from_text function with a query:
# query = "An old monk"
# image_path = imggen1.generate_image_from_text(prompt=query, output_path=f'{query}.png')
# print(image_path)
