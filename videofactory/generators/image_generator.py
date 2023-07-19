from apis.image.automatic1111_image import automaticImage


class ImageGenerator:
    IMAGE_GENERATOR_CLASSES = {
        'automatic1111': automaticImage,
    }

    def __init__(self, image_generator_provider):
        self.image_generator_provider = image_generator_provider
        self.image_generator = self._create_image_generator_instance()

    def _create_image_generator_instance(self):
        image_generator_class = self.IMAGE_GENERATOR_CLASSES.get(self.image_generator_provider)
        if image_generator_class is None:
            raise ValueError(f'Unsupported image generator: {self.image_generator_provider}')
        return image_generator_class()

    def generate_image_from_text(self, prompt, **kwargs):
        self.image_generator.generate_image_from_text(prompt, **kwargs)


# Usage:
# To use the ImageGenerator class, create an instance:
imggen1 = ImageGenerator('automatic1111')
# Then, call the generate_image_from_text function with a query:
query = "An old monk"
responses = imggen1.generate_image_from_text(prompt=query)
