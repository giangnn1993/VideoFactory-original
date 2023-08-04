import json
from collections import defaultdict
from typing import Dict
from pathlib import Path

from .apis.video.d_id_video import DidVideo
from .apis.video.gen_2_video import Gen2Video


class VideoGenerator:
    VIDGEN_CLASSES = {
        'd-id': DidVideo,
        'gen-2': Gen2Video
    }

    def __init__(self, vidgen_provider='', key: str = None) -> None:
        self.vidgen_provider = vidgen_provider
        self.key = key
        self.vidgen = self._create_vidgen_instance()

    def _create_vidgen_instance(self):
        if not self.vidgen_provider:
            # If vidgen_provider is an empty string, return None
            return None

        VidGenClass = self.VIDGEN_CLASSES.get(self.vidgen_provider)
        if VidGenClass is None:
            raise ValueError(f'Unsupported video generator: {self.vidgen_provider}')
        return VidGenClass(key=self.key)

    def set_vidgen_provider(self, vidgen_provider) -> None:
        self.vidgen_provider = vidgen_provider
        self.vidgen = self._create_vidgen_instance()

    def _required_vidgen_provider(vidgen_provider):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                if self.vidgen_provider != vidgen_provider:
                    raise ValueError(f"Method is not available for {self.vidgen_provider}")
                return func(self, *args, **kwargs)
            return wrapper
        return decorator

    def rotate_key(self, keys, limit=1, delimiter=','):
        # Split the keys string into a list using the specified delimiter
        keys = keys.split(delimiter)

        # If the provided key is in the list of keys, set the current_index to its index
        # Otherwise, set the current_index to 0 (the first key in the list)
        current_index = keys.index(self.vidgen.key) if self.vidgen.key in keys else 0

        self.vidgen.key = keys[current_index]

        if self.vidgen_provider == 'd-id':
            self.rotate_key_for_d_id(keys, limit)
        elif self.vidgen_provider == 'gen-2':
            username, gpuCredits, gpuUsageLimit, seconds_left = self.rotate_key_for_gen_2(keys, limit)
            return username, gpuCredits, gpuUsageLimit, seconds_left
        else:
            raise ValueError(f'Unsupported video generator: {self.vidgen_provider}')

    # region: Exclusive methods for 'd-id' only
    @_required_vidgen_provider('d-id')
    def rotate_key_for_d_id(self, keys, limit=1):
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

    @_required_vidgen_provider('d-id')
    def create_talk_video(self, image, audio, max_retries=3, **kwargs) -> str:
        # Attempt to upload the image and audio multiple times (max_retries)
        for retry in range(max_retries):
            # Upload an image and return the URL
            image_url = self.vidgen.upload_image(image=image)
            # Upload an audio file and return the URL
            audio_url = self.vidgen.upload_audio(audio=audio)

            # Check if image_url and audio_url are None (uploads were unsuccessful)
            if image_url is None or audio_url is None:
                print(f"Upload failed for image or audio. Retry {retry+1}/{max_retries}")
                continue  # Retry the upload

            # Use the returned URLs to create a talking head video and return its id
            video_id = self.vidgen.create_talk(image_url=image_url, audio_url=audio_url, **kwargs)
            return video_id

    @_required_vidgen_provider('d-id')
    def get_talk(self, id: str, **kwargs):
        self.vidgen.get_talk(id=id, **kwargs)

    @_required_vidgen_provider('d-id')
    def create_animation_video(self, image, **kwargs) -> str:
        # Upload an image and return the URL
        image_url = self.vidgen.upload_image(image=image)
        # Use the returned URL to create a live portrait video and return its id
        id = self.vidgen.create_animation(image_url=image_url, **kwargs)
        return id

    @_required_vidgen_provider('d-id')
    def get_animation(self, id: str, **kwargs):
        self.vidgen.get_animation(id=id, **kwargs)

    @_required_vidgen_provider('d-id')
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

    @_required_vidgen_provider('d-id')
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
    # endregion

    # region: Exclusive methods for 'gen-2' only
    @_required_vidgen_provider('gen-2')
    def rotate_key_for_gen_2(self, keys, limit=4):
        self.vidgen.headers["Authorization"] = f"Bearer {self.vidgen.key}"
        username, gpuCredits, gpuUsageLimit, seconds_left = self.get_profile()

        while gpuCredits == gpuUsageLimit or (gpuCredits > 0 and seconds_left < limit):  # 1s left or seconds_left<limit
            # Find the index of the current key
            current_index = keys.index(self.vidgen.key)
            # Check if not already at last key
            if current_index < len(keys) - 1:
                self.vidgen.key = keys[current_index + 1]
            self.vidgen.headers["Authorization"] = f"Bearer {self.vidgen.key}"
            username, gpuCredits, gpuUsageLimit, seconds_left = self.get_profile()
            print('┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓')
            print(f"Current token: {self.vidgen.key}")
            print(f"Current token index: {current_index+1}/{len(keys)}")
            print(f"REMAINING CREDITS: {gpuCredits} ({seconds_left} seconds left)")
            print('┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛')

        return username, gpuCredits, gpuUsageLimit, seconds_left

    @_required_vidgen_provider('gen-2')
    def get_profile(self):
        username, gpuCredits, gpuUsageLimit, seconds_left = self.vidgen.step_0_get_profile()
        print(f"(Step 0) Username: {username}\n"
              f"         GPU Credits: {gpuCredits}\n"
              f"         GPU Usage Limit: {gpuUsageLimit}\n"
              f"         Seconds Left: {seconds_left}s")
        return username, gpuCredits, gpuUsageLimit, seconds_left

    @_required_vidgen_provider('gen-2')
    def upload_image(self, image_path: Path):
        if not image_path.is_file() or not image_path.suffix.lower() == ".png":
            print("Invalid PNG file path. Please enter a valid PNG file path.")
            return

        image_filename = image_path.name

        # region: Step 1
        upload_id, upload_url = self.vidgen.step_1_upload_image(image_filename)
        # print('upload_id', upload_id)
        # print('upload_url', upload_url)
        print("(Step 1) Image uploaded successfully.")
        # endregion

        # region: Step 2
        status_code, etag = self.vidgen.step_2_put_image(upload_url, image_path)
        print("(Step 2) PUT request status code:", status_code)
        # endregion

        # region: Step 3
        complete_upload_url = self.vidgen.step_3_complete_upload(upload_id, etag)
        print("(Step 3) Upload completed successfully.")
        # print("Complete Upload URL:", complete_upload_url)
        # endregion

        # region: Step 4
        preview_upload_id, preview_upload_url = self.vidgen.step_4_upload_preview_image(image_filename)
        # print('preview_upload_id', preview_upload_id)
        # print('preview_upload_url', preview_upload_url)
        print("(Step 4) Preview image uploaded successfully.")
        # endregion

        # region: Step 5
        status_code, etag = self.vidgen.step_2_put_image(preview_upload_url, image_path)
        print("(Step 5) PUT request status code:", status_code)
        # endregion

        # region: Step 6
        complete_preview_upload_url = self.vidgen.step_6_complete_upload_preview(preview_upload_id, etag)
        print("(Step 6) Upload completed successfully.")
        # print("Complete Preview Upload URL:", complete_preview_upload_url)
        # endregion

        # region: Step 7
        dataset_id = self.vidgen.step_7_create_dataset(image_filename, upload_id, preview_upload_id)
        print("(Step 7) Dataset created:", dataset_id)
        # print("Dataset ID:", dataset_id)

        return complete_upload_url, complete_preview_upload_url
        # endregion

    @_required_vidgen_provider('gen-2')
    def generate_video_from_image(self, image_path: Path, username: str,
                                  upload_url: str, preview_upload_url: str,
                                  output_dir: str = None, seed=None):
        seed = seed or self.vidgen.generate_random_seed()

        # Step 1: Get the team ID
        team_id = self.vidgen.step_8_get_teams()
        print(f'(Step 8) Team ID: {team_id}')

        image_prompt = init_image = preview_upload_url
        self.vidgen.step_9_send_mp_user_event(username, seed, image_prompt, init_image)

        # Step 2: Create a task
        task_id = self.vidgen.step_10_create_task(team_id, seed, image_prompt, init_image)
        print(f'(Step 10) Task ID: {task_id}')
        task_status = self.vidgen.step_11_check_task_status(task_id, team_id)
        print(f'(Step 11) Task status: {task_status}')

        image_prompt = init_image = upload_url
        # Step 4: Perform generation
        generation_id = self.vidgen.step_12_perform_generation(task_id, image_prompt, init_image, seed)
        print(f'(Step 12) Generation ID: {generation_id}')
        print(f'Seed: {seed}')

        # Step 5: Check task status and get the generated video URL
        generated_video_url = self.vidgen.step_13_check_task_status_and_get_url(task_id, team_id)
        print(f'(Step 13) Generated video URL: {generated_video_url}')

        # Step 6: Download the video
        output_dir = output_dir or image_path.parent
        output_path = output_dir / f"{image_path.stem}_{seed}.mp4"
        self.vidgen.download_video(generated_video_url, output_path)
    # endregion


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
