import os
import sys
import requests
from pathlib import Path

import uuid
import time
import random

import string


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from video import VideoGenerator
except ImportError:
    # Handle the case where the module cannot be imported
    VideoGenerator = None
    # Log an error or raise an exception, as appropriate


class Gen2Video(VideoGenerator):
    def __init__(self, key: str = None) -> None:
        super().__init__('gen-2')
        self.key: str = key or os.environ.get('GEN_2_BEARER_TOKEN', None)  # F12 > Local storage > RW_USER_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.key}",
            "Origin": "https://app.runwayml.com",
            "Referer": "https://app.runwayml.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sentry-Trace": ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16)),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188"  # noqa
        }

    @staticmethod
    def download_video(url: str, output_path: Path) -> None:
        response = requests.get(url, stream=True)
        success_status_codes = {200, 206}

        if response.status_code in success_status_codes:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print('\033[92m' + f'Video downloaded successfully to "{output_path}"' + '\033[0m')
        else:
            print(f'Failed to download video. Status code: {response.status_code}')

    @staticmethod
    def get_image_filename():
        image_filename = input("Enter the image filename or path: ")
        return image_filename

    def step_0_get_profile(self):
        url = "https://api.runwayml.com/v1/profile"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            username = data["user"]["username"]
            gpuCredits = data["user"]["gpuCredits"]
            gpuUsageLimit = data["user"]["gpuUsageLimit"]
            seconds_left = int(gpuCredits / gpuUsageLimit)
            return username, gpuCredits, gpuUsageLimit, seconds_left
        else:
            print(f"Failed to fetch profile. Status code: {response.status_code}, Error: {response.text}")

    # region 1: Upload image
    def step_1_upload_image(self, image_filename):
        url = 'https://api.runwayml.com/v1/uploads'
        payload = {
            "filename": image_filename,
            "numberOfParts": 1,
            "type": "DATASET"
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response_data = response.json()
        upload_id = response_data['id']
        upload_url = response_data['uploadUrls'][0]

        return upload_id, upload_url

    def step_2_put_image(self, upload_url, image_path):
        headers = {
            'Content-Type': 'image/png'
        }

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        response = requests.put(upload_url, data=image_data, headers=headers)
        etag = response.headers.get('ETag')

        return response.status_code, etag

    def step_3_complete_upload(self, upload_id, etag):
        url = f'https://api.runwayml.com/v1/uploads/{upload_id}/complete'
        payload = {
            "parts": [
                {
                    "PartNumber": 1,
                    "ETag": etag
                }
            ]
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response_data = response.json()
        complete_upload_url = response_data['url']

        return complete_upload_url

    def step_4_upload_preview_image(self, image_filename):
        url = 'https://api.runwayml.com/v1/uploads'
        payload = {
            "filename": image_filename,
            "numberOfParts": 1,
            "type": "DATASET_PREVIEW"
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response_data = response.json()
        preview_upload_id = response_data['id']
        preview_upload_url = response_data['uploadUrls'][0]

        return preview_upload_id, preview_upload_url

    def step_5_complete_upload_preview(self, preview_upload_id, etag):
        complete_preview_upload_url = self.step_3_complete_upload(preview_upload_id, etag)
        # print("Step 5: Upload completed successfully.")
        # print("Complete Preview Upload URL:", complete_preview_upload_url)
        return complete_preview_upload_url

    def _create_dataset(self, image_filename, upload_id, preview_upload_id):
        url = "https://api.runwayml.com/v1/datasets"
        payload = {
            "fileCount": 1,
            "name": image_filename,
            "uploadId": upload_id,
            "previewUploadIds": [preview_upload_id],
            "type": {
                "name": "image",
                "type": "image",
                "isDirectory": False
            }
        }

        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            dataset_data = response.json()["dataset"]
            dataset_id = dataset_data["id"]
            return dataset_id
        else:
            print("Failed to create dataset.")

    def step_6_complete_upload_preview(self, preview_upload_id, etag):
        complete_preview_upload_url = self.step_5_complete_upload_preview(preview_upload_id, etag)
        # print("Step 6: Upload completed successfully.")
        # print("Complete Preview Upload URL:", complete_preview_upload_url)
        return complete_preview_upload_url

    def step_7_create_dataset(self, image_filename, upload_id, preview_upload_id):
        dataset_id = self._create_dataset(image_filename, upload_id, preview_upload_id)
        # print("Step 7: Dataset created successfully.")
        # print("Dataset ID:", dataset_id)
        return dataset_id
    # endregion

    # region 2: Generate video from image
    @staticmethod
    # This static method generates a random seed value to be used with Gen-3.
    # The lower bound is set to 0 and the upper bound is set to 4294967295,
    # which is the maximum value of a 32-bit unsigned integer.
    # The returned value is an integer within the range of 0 to 4294967295 (inclusive).
    def generate_random_seed() -> int:
        return random.randint(0, 4294967295)

    def step_8_get_teams(self):
        url = "https://api.runwayml.com/v1/teams"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            team_id = response.json()["teams"][0]["id"]
            return team_id
        else:
            print("Failed to fetch teams data")

    def step_9_send_mp_user_event(self, username, seed, image_prompt, init_image, sessionId=None, interpolate=False):
        sessionId = sessionId or str(uuid.uuid4())

        url = "https://api.runwayml.com/v1/mp_user_events"
        payload = {
            "eventName": "Click -> Primary Button",
            "properties": {
                "sessionId": sessionId,
                "platform": "web",
                "device_type": "desktop",
                "$browser": "Microsoft Edge",
                "$browser_version": "115",
                "$current_url": f'https://app.runwayml.com/video-tools/teams/{username}/ai-tools/gen-2',
                "$os": "Windows",
                "$screen_height": 1080,
                "$screen_width": 1920,
                "event": "Click",
                "name": "Primary Button",
                "section": "AI Magic Tools",
                "toolId": "gen-2",
                "gen2EventId": "generate from prompt input",
                "options": {
                    "interpolate": interpolate,
                    "seed": seed,
                    "upscale": False,
                    "text_prompt": "",
                    "watermark": True,
                    "image_prompt": image_prompt,
                    "init_image": init_image
                },
                "generationMode": "creditsMode",
                "buttonText": "Generate"
            }
        }

        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            print("(Step 9) User event sent successfully.")
        else:
            print("(Step 9) Failed to send user event.")

    def step_10_create_task(self, team_id, seed, image_prompt, init_image, interpolate=False):
        url = "https://api.runwayml.com/v1/tasks"
        payload = {
            "taskType": "gen2",
            "internal": False,
            "options": {
                "seconds": 4,
                "gen2Options": {
                    "interpolate": interpolate,
                    "seed": seed,
                    "upscale": False,
                    "text_prompt": "",
                    "watermark": True,
                    "image_prompt": image_prompt,
                    "init_image": init_image,
                    "mode": "gen2"
                },
                "name": f"Gen-2, {seed}",
                "assetGroupName": "Gen-2",
                "exploreMode": False
            },
            "asTeamId": team_id
        }
        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 200:
            task_id = response.json()["task"]["id"]
            return task_id
        else:
            print("Failed to create task")

    def step_11_check_task_status(self, task_id, team_id):
        url = f"https://api.runwayml.com/v1/tasks/{task_id}?asTeamId={team_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            task_status = response.json()["task"]["status"]
            return task_status
        else:
            print("Failed to fetch task status")

    def step_12_perform_generation(self, task_id, image_prompt, init_image, seed, interpolate=False):
        url = "https://api.runwayml.com/v1/generations"
        id = str(uuid.uuid4())
        payload = {
            "toolId": "gen2",
            "prompt": image_prompt,
            "outputs": {"outputUrls": []},
            "settings": {
                "interpolate": interpolate,
                "seed": seed,
                "upscale": False,
                "watermark": True,
                "id": id,
                "taskId": task_id,
                "text_prompt": "",
                "image_prompt": image_prompt,
                "init_image": init_image
            }
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            generation_id = response.json()["id"]
            return generation_id
        else:
            print("Failed to perform generation")

    def step_13_check_task_status_and_get_url(self, task_id, team_id):
        url = f"https://api.runwayml.com/v1/tasks/{task_id}?asTeamId={team_id}"
        max_attempts = 60  # Maximum number of attempts to check task status (60 * 5 seconds = 5 minutes)

        for attempt in range(1, max_attempts + 1):
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                task_data = response.json()["task"]
                task_status = task_data["status"]
                task_artifacts = task_data["artifacts"]
                task_progressRatio = task_data["progressRatio"]

                print(f'Task status: {task_status}; Progress Ratio: {task_progressRatio}')

                if (task_status == "SUCCEEDED" and task_artifacts
                        and len(task_artifacts) > 0 and "url" in task_artifacts[0]):
                    return task_artifacts[0]["url"]
                elif task_status == "FAILED":
                    print(f'Task failed after {attempt} attempts.')
                    return

            time.sleep(5)  # Wait for 5 seconds before checking the task status again

        print('Maximum attempts reached. Task status remains unknown.')
        return
    # endregion


# # Example usage:
# def process_single_image(gen2_video: Gen2Video, image_path: Path):
#     # region: Step 0
#     username, gpuCredits, gpuUsageLimit, seconds_left = gen2_video.step_0_get_profile()
#     print(f"(Step 0) Username: {username}\n"
#           f"         GPU Credits: {gpuCredits}\n"
#           f"         GPU Usage Limit: {gpuUsageLimit}\n"
#           f"         Seconds Left: {seconds_left}s")
#     # endregion

#     # region 1: Upload image

#     # image_path = Path(gen2_video.get_image_filename())
#     if not image_path.is_file() or not image_path.suffix.lower() == ".png":
#         print("Invalid PNG file path. Please enter a valid PNG file path.")
#         return

#     image_filename = image_path.name

#     # region: Step 1
#     upload_id, upload_url = gen2_video.step_1_upload_image(image_filename)
#     # print('upload_id', upload_id)
#     # print('upload_url', upload_url)
#     print("(Step 1) Image uploaded successfully.")
#     # endregion

#     # region: Step 2
#     status_code, etag = gen2_video.step_2_put_image(upload_url, image_path)
#     print("(Step 2) PUT request status code:", status_code)
#     # endregion

#     # region: Step 3
#     complete_upload_url = gen2_video.step_3_complete_upload(upload_id, etag)
#     print("(Step 3) Upload completed successfully.")
#     # print("Complete Upload URL:", complete_upload_url)
#     # endregion

#     # region: Step 4
#     preview_upload_id, preview_upload_url = gen2_video.step_4_upload_preview_image(image_filename)
#     # print('preview_upload_id', preview_upload_id)
#     # print('preview_upload_url', preview_upload_url)
#     print("(Step 4) Preview image uploaded successfully.")
#     # endregion

#     # region: Step 5
#     status_code, etag = gen2_video.step_2_put_image(preview_upload_url, image_path)
#     print("(Step 5) PUT request status code:", status_code)
#     # endregion

#     # region: Step 6
#     complete_preview_upload_url = gen2_video.step_6_complete_upload_preview(preview_upload_id, etag)
#     print("(Step 6) Upload completed successfully.")
#     # print("Complete Preview Upload URL:", complete_preview_upload_url)
#     # endregion

#     # region: Step 7
#     dataset_id = gen2_video.step_7_create_dataset(image_filename, upload_id, preview_upload_id)
#     print("(Step 7) Dataset created:", dataset_id)
#     # print("Dataset ID:", dataset_id)
#     # endregion

#     # endregion

#     # time.sleep(5)

#     # region 2: Generate video from image

#     seed = gen2_video.generate_random_seed()

#     # Step 1: Get the team ID
#     team_id = gen2_video.step_8_get_teams()
#     print(f'(Step 8) Team ID: {team_id}')

#     image_prompt = init_image = complete_preview_upload_url
#     gen2_video.step_9_send_mp_user_event(username, seed, image_prompt, init_image)

#     # Step 2: Create a task
#     task_id = gen2_video.step_10_create_task(team_id, seed, image_prompt, init_image)
#     print(f'(Step 10) Task ID: {task_id}')
#     task_status = gen2_video.step_11_check_task_status(task_id, team_id)
#     print(f'(Step 11) Task status: {task_status}')

#     image_prompt = init_image = complete_upload_url
#     # Step 4: Perform generation
#     generation_id = gen2_video.step_12_perform_generation(task_id, image_prompt, init_image, seed)
#     print(f'(Step 12) Generation ID: {generation_id}')
#     print(f'Seed: {seed}')

#     # Step 5: Check task status and get the generated video URL
#     generated_video_url = gen2_video.step_13_check_task_status_and_get_url(task_id, team_id)
#     print(f'(Step 13) Generated video URL: {generated_video_url}')

#     # Step 6: Download the video
#     output_path = image_path.with_name(f"{image_path.stem}_{seed}.mp4")
#     gen2_video.download_video(generated_video_url, output_path)

#     # endregion


# if __name__ == "__main__":
#     gen2_video = Gen2Video()
#     folder_path = input("Enter the folder path containing PNG files: ")
#     folder_path = Path(folder_path)

#     if not folder_path.is_dir():
#         print("Invalid folder path. Please enter a valid folder path.")
#     else:
#         png_files = list(folder_path.glob("*.png"))
#         if not png_files:
#             print("No PNG files found in the folder.")
#         else:
#             # for png_file in png_files:
#             #     print(f"Processing: {png_file}")
#             #     process_single_image(gen2_video, png_file)
#             num_repeats = int(input("Enter the number of times to process each image: "))
#             for png_file in png_files:
#                 print(f"Processing: {png_file}")
#                 for _ in range(num_repeats):
#                     process_single_image(gen2_video, png_file)
