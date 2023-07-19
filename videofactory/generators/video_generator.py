from apis.video.d_id_video import DidVideo
import time


class VideoGenerator:
    Video_CLASSES = {
        'd-id': DidVideo
    }

    def __init__(self, video_generator_provider, key: str):
        self.video_generator_provider = video_generator_provider
        self.key = key
        self.video_generator = self._create_video_generator_instance()

    def _create_video_generator_instance(self):
        VidGenClass = self.Video_CLASSES.get(self.video_generator_provider)
        if VidGenClass is None:
            raise ValueError(f'Unsupported video generator: {self.video_generator_provider}')
        return VidGenClass(key=self.key)

    def create_talk_video(self, image, audio, **kwargs) -> None:
        # Upload an image and return the URL
        image_url = self.video_generator.upload_image(image=image)
        # Upload an audio file and return the URL
        audio_url = self.video_generator.upload_audio(audio=audio)
        # Use the returned URLs to create a talking head video and return its id
        id = self.video_generator.create_talk(image_url=image_url, audio_url=audio_url)
        time.sleep(10)
        # Download the video
        self.video_generator.get_talk(id=id, **kwargs)


# # Usage:
# import os
# from pathlib import Path
# # To use the VideoGenerator class, create an instance:
# vidgen1 = VideoGenerator('d-id', key=os.environ.get('D-ID_BASIC_TOKEN'))
# # Then, call the create_talk_video function:
# path = Path(Path.cwd())
# image_path = str(path / 'assets' / 'images' / '01.png')
# audio_path = str(path / 'examples' / 'coqui_tts.mp3')
# output_path = path / 'examples' / 'coqui_tts_d_id_talk.mp4'
# vidgen1.create_talk_video(image=image_path, audio=audio_path, output_path=output_path)
