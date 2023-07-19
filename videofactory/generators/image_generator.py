from apis.image.automatic1111_image import AutomaticImage


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

    def generate_image_from_text(self, prompt: str, **kwargs):
        self.imggen.generate_image_from_text(prompt, **kwargs)


# Usage:
# To use the ImageGenerator class, create an instance:
imggen1 = ImageGenerator('automatic1111')
# Then, call the generate_image_from_text function with a query:
query = "An old monk"
responses = imggen1.generate_image_from_text(prompt=query)
