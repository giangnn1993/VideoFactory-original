class TextToSpeech:
    def __init__(self, provider, **auth_credentials):
        self.provider = provider
        self.auth_credentials = auth_credentials

    def generate_audio(self, text: str, **kwargs):
        raise NotImplementedError
