
from .apis.tts.coqui_tts import CoquiTTS
from .apis.tts.elevenlabs_tts import ElevenLabsTTS
from .apis.tts.fpt_tts import FptTTS


class TTSGenerator:
    TTS_CLASSES = {
        'coqui': CoquiTTS,
        'elevenlabs': ElevenLabsTTS,
        'fpt': FptTTS
    }

    def __init__(self, tts_provider, key: str):
        self.tts_provider = tts_provider
        self.key = key
        self.tts = self._create_tts_instance()

    def _create_tts_instance(self):
        TTSClass = self.TTS_CLASSES.get(self.tts_provider)
        if TTSClass is None:
            raise ValueError(f'Unsupported TTS provider: {self.tts_provider}')
        return TTSClass(key=self.key)

    def set_tts_provider(self, tts_provider):
        self.tts_provider = tts_provider
        self.tts = self._create_tts_instance()

    def generate_audio(self, text: str, **kwargs):
        self.tts.generate_audio(text, **kwargs)


# # Usage:
# import os
# from pathlib import Path
# # To use the TTSGenerator class, create an instance with your API key:
# tts1 = TTSGenerator('coqui', key=os.environ.get('COQUI_BEARER_TOKEN'))
# tts2 = TTSGenerator('elevenlabs', key=os.environ.get('ELEVENLABS_API_KEY'))
# tts3 = TTSGenerator('fpt', key=os.environ.get('FPT_API_KEY'))
# # Then, call the generate_audio method to generate audio from text:
# path = Path(Path.cwd()) / 'examples'
# tts1.generate_audio(text='Hello, world!', emotion='Angry', output_path=f'{path / "coqui_tts.wav"}')
# tts2.generate_audio(text='Hello, world!', stability=0.45, output_path=f'{path / "elevenlabs_tts.wav"}')
# tts3.generate_audio(text='Xin chào mọi người', speed=-3.0, output_path=f'{path / "fpt_tts.wav"}')
