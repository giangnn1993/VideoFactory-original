import json
from collections import defaultdict
from typing import Dict
from pathlib import Path

from .apis.video.d_id_video import DidVideo


class VideoGenerator:
    VIDGEN_CLASSES = {
        'd-id': DidVideo
    }

    def __init__(self, vidgen_provider, key: str = None):
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

    def create_animation_video(self, image, **kwargs) -> str:
        # Upload an image and return the URL
        image_url = self.vidgen.upload_image(image=image)
        # Use the returned URL to create a live portrait video and return its id
        id = self.vidgen.create_animation(image_url=image_url, **kwargs)
        return id

    def get_animation(self, id: str, **kwargs):
        self.vidgen.get_animation(id=id, **kwargs)

    def create_talk_videos_from_images_and_audios(self,
                                                  images_and_audios_dict: Dict, output_dir: str,
                                                  keys: str = None, **kwargs) -> Path:
        output_ids_file = Path(output_dir) / 'd-id_output_ids.json'

        for basename, data_dict in images_and_audios_dict.items():
            # If keys argument is provided, call rotate_key with the provided keys
            if keys is not None:
                self.rotate_key(keys=keys)

            # Get the paths of the image and audio files from the dictionary
            image_path = data_dict["image"]
            audio_path = data_dict["audio"]

            # Path to the generated D-ID talk video file
            d_id_file = Path(output_dir) / f'{basename}_d_id.mp4'
            #
            #  Check if the output IDs file does not exist
            if not d_id_file.exists():
                # Create the D-ID talk video
                id = self.create_talk_video(image=image_path, audio=audio_path, **kwargs)

                # Check if the output IDs file does not exist
                if not output_ids_file.exists():
                    # Create d-id_output_ids.json with empty dictionary content if it does not exist
                    with open(output_ids_file, 'w') as outfile:
                        json.dump({}, outfile)

                # Read the existing json data from d-id_output_ids.json
                with open(output_ids_file, 'r') as infile:
                    json_object = json.load(infile)

                # Use a defaultdict to initialize missing sub-dictionaries
                json_object = defaultdict(dict, json_object)

                # Add new key-value pair to the dictionary
                print(f"D-ID: {id}")
                print()
                json_object[self.vidgen.key][basename] = id

                # Write the updated dictionary to d-id_output_ids.json in the output_dir
                with open(output_ids_file, 'w') as outfile:
                    json.dump(json_object, outfile)
            else:
                # The D-ID talk video file already exists, skip creating it
                print(f'{d_id_file} already exists. Skipping...')

        # Return the path of the d-id_output_ids.json file
        return output_ids_file

    def get_talks_from_json(self, output_ids_file: Path, output_dir: str) -> None:
        # Save the current key value to be restored later
        current_key = self.vidgen.key
        # Open the JSON file
        with open(output_ids_file, 'r') as infile:
            json_data = json.load(infile)

        # Loop through the JSON data by keys
        for key, data_dict in json_data.items():
            # Loop through the dicts
            for key_in_dict, id_value in data_dict.items():
                if key_in_dict is not None and id_value is not None:
                    # Temporarily set the class attribute self.vidgen.key to the current key
                    # This ensures that the subsequent call to self.vidgen.get_talk()
                    # uses the correct self.vidgen.key value
                    self.vidgen.key = key

                    # Get the 'id' and 'output_path' for self.vidgen.get_talk()
                    id = id_value
                    output_path = Path(output_dir) / (key_in_dict + '_d_id.mp4')

                    # Call the function self.vidgen.get_talk() with the 'id' and 'output_path'
                    self.vidgen.get_talk(id, output_path)

        # Restore the original key value after processing all the data
        self.vidgen.key = current_key

    def rotate_key(self, keys: str,
                   limit: int = 2,  delimiter: str = ',') -> None:
        # Split the keys string into a list using the specified delimiter
        keys = keys.split(delimiter)

        # If the provided key is in the list of keys, set the current_index to its index
        # Otherwise, set the current_index to 0 (the first key in the list)
        current_index = keys.index(self.vidgen.key) if self.vidgen.key in keys else 0

        self.vidgen.key = keys[current_index]

        # Get the remaining credits for the current key using the get_credits() method
        remaining_credits = self.vidgen.get_credits()

        # This while loop runs as long as variable "remaining" satisfies the limit condition
        while remaining_credits < limit:
            # Find the index of the current key
            current_index = keys.index(self.vidgen.key)
            # Check if not already at last key
            if current_index < len(keys) - 1:
                self.vidgen.key = keys[current_index + 1]
            remaining_credits = self.vidgen.get_credits()
            print('┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓')
            print(f"Current token: {self.vidgen.key}")
            print(f"Current token index: {current_index+1}/{len(keys)}")
            print(f"REMAINING CREDITS: {remaining_credits}")
            print('┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛')

# USAGE
# ------------------------------------

# # Usage #1:
# import os
# import time
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


# # Usage #2:
# import os
# import time
# from pathlib import Path
# # To use the VideoGenerator class, create an instance:
# vidgen2 = VideoGenerator('d-id', key=os.environ.get('D-ID_BASIC_TOKEN'))
# # Then, call the create_talk_video function:
# path = Path(Path.cwd())
# image_path = str(path / 'assets' / 'images' / '01.png')
# output_path = path / 'examples' / 'coqui_tts_d_id_animation.mp4'
# id = vidgen2.create_animation_video(image=image_path, driver='subtle')
# time.sleep(10)
# # Download the video
# vidgen2.get_animation(id=id, output_path=output_path)
