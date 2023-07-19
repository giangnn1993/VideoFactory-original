class TextToSpeech:
    def __init__(self, provider):
        self.provider = provider

    def generate_audio(self, text, **kwargs):
        raise NotImplementedError
