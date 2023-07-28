import os
import sys
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from tts import TextToSpeech
except ImportError:
    # Handle the case where the module cannot be imported
    TextToSpeech = None
    # Log an error or raise an exception, as appropriate


class ElevenLabsTTS(TextToSpeech):
    BASE_URL: str = 'https://api.elevenlabs.io/v1/text-to-speech'

    def __init__(self, key: str = None) -> None:
        super().__init__('elevenlabs')
        self.key: str = key or os.environ.get('ELEVENLABS_API_KEY', None)

    def _get_url(self, voice_id: str) -> str:
        return f'{self.BASE_URL}/{voice_id}?optimize_streaming_latency=0'

    def generate_audio(
        self,
        text: str,
        voice_id: str = None,
        stability: float = None,
        similarity_boost: float = None,
        output_path: str = 'elevenlabs_tts.mp3'
    ) -> None:
        # Check if the arguments are provided, if not, fetch from environment variables or use defaults
        if voice_id is None:
            voice_id = os.environ.get('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Default voice: 'Adam'
        if stability is None:
            stability = float(os.environ.get('ELEVENLABS_STABILITY', 0.5))
        if similarity_boost is None:
            similarity_boost = float(os.environ.get('ELEVENLABS_SIMILARITY_BOOST', 0.75))

        url: str = self._get_url(voice_id)
        headers: dict = {
            'accept': 'audio/mpeg',
            'xi-api-key': self.key,
            'Content-Type': 'application/json'
        }
        payload: dict = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': stability,
                'similarity_boost': similarity_boost
            }
        }

        # Make the API request
        response = requests.post(url, headers=headers, json=payload)

        # Save the response to a file
        with open(output_path, 'wb') as f:
            f.write(response.content)


# # Usage:
# # To use the ElevenLabsTTS class, create an instance with your API key:
# tts = ElevenLabsTTS(key=os.environ.get('ELEVENLABS_API_KEY'))
# # Then, call the generate_audio method to generate audio from text:
# tts.generate_audio(text='Hello, world!')
