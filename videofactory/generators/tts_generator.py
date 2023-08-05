
import re
import inspect
from pathlib import Path

from .apis.tts.coqui_tts import CoquiTTS
from .apis.tts.elevenlabs_tts import ElevenLabsTTS
from .apis.tts.fpt_tts import FptTTS
from ._utils import process_text


class TTSGenerator:
    TTS_CLASSES = {
        'coqui': CoquiTTS,
        'elevenlabs': ElevenLabsTTS,
        'fpt': FptTTS
    }

    def __init__(self, tts_provider='', key: str = None) -> None:
        self.tts_provider = tts_provider
        self.key = key
        self.tts = self._create_tts_instance()

    def _create_tts_instance(self) -> None:
        if not self.tts_provider:
            # If tts_provider is an empty string, return None
            return None

        TTSClass = self.TTS_CLASSES.get(self.tts_provider)
        if TTSClass is None:
            raise ValueError(f'Unsupported TTS provider: {self.tts_provider}')
        return TTSClass(key=self.key)

    def set_tts_provider(self, tts_provider) -> None:
        if self.tts_provider != tts_provider:
            self.tts_provider = tts_provider
            self.tts = self._create_tts_instance()

    def generate_audio(self, text: str, **kwargs) -> None:
        self.tts.generate_audio(text, **kwargs)

    def generate_audios_from_txt(self, input_file: str, output_dir: str = None, **kwargs) -> None:
        input_path = Path(input_file)

        # Prepare output directory path
        if output_dir is None:
            # Use the parent directory of input_file as the output directory
            output_dir = input_path.parent / input_path.stem

        # Create the output directory and its parent directories if they don't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read the contents of the txt file
        with input_file.open('r', encoding='utf8') as file:
            lines = file.readlines()

        # Find the maximum line number for zfill
        max_line_number = len(str(len(lines)))

        # List to store paths to audio files
        audio_files = []

        for i, line in enumerate(lines, start=1):
            # Prepare output path for the generated audio file
            filename = f'{str(i).zfill(max_line_number)}.wav'
            output_path = Path(output_dir) / filename

            # Find the content inside square brackets using regex
            match = re.search(r'\[(.*?)\]', line)
            if match:
                _, outside_text, config = process_text(line)
                # Check if the 'config' variable is not empty (evaluates to True).
                if bool(config):
                    # Update the kwargs directly with the config dictionary
                    kwargs.update(config)

                    # Check if the line contains the 'provider' pattern
                    if 'provider' in kwargs:
                        tts_provider = kwargs['provider']
                        self.set_tts_provider(tts_provider)

                    # Remove the 'provider' key from kwargs as it's no longer needed
                    kwargs.pop('provider', None)

                    # Filter out unsupported arguments for the generate_audio method
                    supported_args = set(inspect.signature(self.tts.generate_audio).parameters.keys())
                    kwargs_for_generate_audio = {k: v for k, v in kwargs.items() if k in supported_args}

                    # Generate audio for the current line using the current TTS provider and filtered kwargs
                    self.generate_audio(
                        outside_text,
                        output_path=output_path,
                        **kwargs_for_generate_audio
                        )
                # If the 'config' variable is empty (evaluates to False).
                else:
                    self.generate_audio(
                        outside_text,
                        output_path=output_path,
                        **kwargs
                        )
            else:
                self.generate_audio(
                    line,
                    output_path=output_path,
                    **kwargs
                    )

            # Append audio file to the list
            audio_files.append(Path(output_path))

        # Return the list of audio files
        return audio_files
# USAGE
# ------------------------------------

# # Usage #1:
# import os
# path = Path(Path.cwd()) / 'examples'
# # To use the TTSGenerator class, create an instance with your API key:
# tts1 = TTSGenerator('coqui', key=os.environ.get('COQUI_BEARER_TOKEN'))
# tts2 = TTSGenerator('elevenlabs', key=os.environ.get('ELEVENLABS_API_KEY'))
# tts3 = TTSGenerator('fpt', key=os.environ.get('FPT_API_KEY'))
# # Then, call the generate_audio method to generate audio from text:
# tts1.generate_audio(text='Hello, world!', emotion='Angry', output_path=f'{path / "coqui_tts.wav"}')
# tts2.generate_audio(text='Hello, world!', stability=0.45, output_path=f'{path / "elevenlabs_tts.wav"}')
# tts3.generate_audio(text='Xin chào mọi người', speed=-3.0, output_path=f'{path / "fpt_tts.wav"}')


# # Usage #2:
# tts2 = TTSGenerator()
# tts2.generate_audios_from_txt(input_file=r'lines_with_configs.txt')

# tts2.generate_audios_from_txt(
#     input_file=r'lines_with_configs.txt',
#     output_dir=r'data\output\processed')
