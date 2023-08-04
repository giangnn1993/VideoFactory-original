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


class CoquiTTS(TextToSpeech):

    def __init__(self, key: str = None) -> None:
        super().__init__('coqui')
        self.key: str = key or os.environ.get('COQUI_BEARER_TOKEN', None)

    def generate_audio(
        self,
        text: str,
        voice_id: str = None,
        emotion: str = None,
        speed: float = None,
        output_path: str = 'coqui_tts.mp3'
    ) -> None:
        # Check if the arguments are provided, if not, fetch from environment variables or use defaults
        if voice_id is None:
            voice_id = os.environ.get('COQUI_VOICE_ID', '6720d486-5d43-4d92-8893-57a1b58b334d')  # Default voice: 'Dionisio Schuyler'  # noqa
        if emotion is None:
            emotion = os.environ.get('COQUI_VOICE_EMOTION', 'Neutral')
        if speed is None:
            speed = float(os.environ.get('COQUI_VOICE_SPEED', 0.85))

        url: str = 'https://app.coqui.ai/api/v2/samples'
        headers: dict = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'authorization': 'Bearer ' + self.key
        }
        payload: dict = {
            'emotion': emotion,
            'speed': speed,
            'text': text,
            'voice_id': voice_id,
        }

        # Make the API request
        response = requests.post(url, headers=headers, json=payload)

        # Get the response data
        data = response.json()

        try:
            audio_url = data['audio_url']
            r = requests.get(audio_url)
        except (KeyError, requests.exceptions.RequestException) as e:
            print("Error occurred while accessing the audio data:")
            print(e)
            print("Data:", data)
            print("voice_id:", voice_id)

        if response.status_code == 201:
            # Save the response to a file
            with open(output_path, 'wb') as f:
                f.write(r.content)
        else:
            print(f'Error: ({os.path.basename(output_path)})', response.status_code)


# # Usage:
# # To use the CoquiTTS class, create an instance with your API key:
# tts = CoquiTTS(key=os.environ.get('COQUI_BEARER_TOKEN'))
# # Then, call the generate_audio method to generate audio from text:
# tts.generate_audio(text='Hello, world!')
