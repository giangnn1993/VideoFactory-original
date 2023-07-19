from apis.video.d_id_video import DidVideo
import time


class VideoGenerator:
    VIDGEN_CLASSES = {
        'd-id': DidVideo
    }

    def __init__(self, vidgen_provider, key: str):
        self.vidgen_provider = vidgen_provider
        self.key = key
        self.vidgen = self._create_vidgen_instance()

    def _create_vidgen_instance(self):
        VidGenClass = self.VIDGEN_CLASSES.get(self.vidgen_provider)
        if VidGenClass is None:
            raise ValueError(f'Unsupported video generator: {self.vidgen_provider}')
        return VidGenClass(key=self.key)

    def create_talk_video(self, image, audio, **kwargs) -> str:
        # Upload an image and return the URL
        image_url = self.vidgen.upload_image(image=image)
        # Upload an audio file and return the URL
        audio_url = self.vidgen.upload_audio(audio=audio)
        # Use the returned URLs to create a talking head video and return its id
        id = self.vidgen.create_talk(image_url=image_url, audio_url=audio_url, **kwargs)
        return id

    def get_talk(self, id: str, **kwargs):
        self.vidgen.get_talk(id=id, **kwargs)

    def create_animation_video(self, image) -> str:
        # Upload an image and return the URL
        image_url = self.vidgen.upload_image(image=image)
        # Use the returned URL to create a live portrait video and return its id
        id = self.vidgen.create_animation(image_url=image_url)
        return id

    def get_animation(self, id: str, **kwargs):
        self.vidgen.get_animation(id=id, **kwargs)


# Usage:
# import os
# from pathlib import Path
# # To use the VideoGenerator class, create an instance:
# vidgen1 = VideoGenerator('d-id', key=os.environ.get('D-ID_BASIC_TOKEN'))
# # Then, call the create_talk_video function:
# path = Path(Path.cwd())
# image_path = str(path / 'assets' / 'images' / '01.png')
# audio_path = str(path / 'examples' / 'coqui_tts.mp3')
# output_path = path / 'examples' / 'coqui_tts_d_id_talk.mp4'
# id = vidgen1.create_talk_video(image=image_path, audio=audio_path, expression='serious')
# time.sleep(10)
# # Download the video
# vidgen1.get_talk(id=id, output_path=output_path)
