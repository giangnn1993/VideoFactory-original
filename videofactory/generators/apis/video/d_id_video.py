import os
import sys
import requests
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from video import VideoGenerator
except ImportError:
    # Handle the case where the module cannot be imported
    VideoGenerator = None
    # Log an error or raise an exception, as appropriate


class DidVideo(VideoGenerator):
    def __init__(self, key: str) -> None:
        super().__init__('d-id')
        self.key: str = key

    @staticmethod
    def download_video(token: str, url: str, output_path: str) -> None:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + token
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            res_data = response.json()
            if res_data['status'] == 'done':
                r = requests.get(res_data['result_url'])
                with open(output_path, 'wb') as file_handle:
                    file_handle.write(r.content)
                    print(f'Downloaded successfully: {output_path}')
            else:
                print("Status is not 'done'")
        else:
            print('Request failed.')

    def create_talk(
            self,
            audio_url: str,
            image_url: str) -> str:
        url = "https://api.d-id.com/talks"
        # Set the headers for the POST request
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + self.key
        }

        # Set the payload for the POST request
        payload = {
            "script": {
                "input": "text",
                "type": "audio",
                "subtitles": "false",
                "ssml": "false",
                "audio_url": audio_url
            },
            "config": {
                "stitch": "true",
                # "pad_audio": pad_audio
            },
            "source_url": image_url
        }

        # Make the API request
        response = requests.post(url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code == 201:
            # Load the response text into a JSON object
            json_response = json.loads(response.text)
            return json_response['id']
        else:
            print("Error: POST request was not successful")

    def get_talk(self, id: str, output_path: str = 'd_id_talk.mp4') -> None:
        url = f"https://api.d-id.com/talks/{id}"
        print('Talk Video URL:', url)
        self.download_video(self.key, url, output_path)

    def upload_image(self, image) -> str:
        try:
            url = "https://api.d-id.com/images"
            files = {"image": (image, open(image, "rb"), "image/png")}
            headers = {
                "accept": "application/json",
                "authorization": "Basic " + self.key
            }

            # Make the request
            response = requests.post(url, files=files, headers=headers)
            image_url = response.json()['url']
            # Print the image url
            print('Image URL:', image_url)
            return image_url
        except Exception as e:
            print(f"An error occurred in upload_image function: {str(e)}")

    def upload_audio(self, audio) -> str:
        try:
            url = "https://api.d-id.com/audios"
            files = {"audio": (audio, open(audio, "rb"), "audio/wav")}
            headers = {
                "accept": "application/json",
                "authorization": "Basic " + self.key
            }

            # Make the request
            response = requests.post(url, files=files, headers=headers)
            audio_url = response.json()['url']
            # Print the audio url
            print('Audio URL:', audio_url)

            return audio_url
        except Exception as e:
            print(f"An error occurred in upload_audio function: {str(e)}")

    def create_animation(
            self,
            image_url: str) -> str:
        url = "https://api.d-id.com/animations"
        # Set the headers for the POST request
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + self.key
        }
        # Set the payload for the POST request
        payload = {
            "script": {
                # bank://nostalgia	Gentle and slow movements
                # bank://fun	Funky movements with funny facial expressions
                # bank://dance	Dancing heads movements
                # bank://classics	Singing movements | make sure to set "mute": false
                # bank://subtle	Subtle movements | works best with multiple faces that are close to each other in a single image  # noqa
                # bank://stitch	Works best when "stitch": true
                "driver_url": "bank://subtle",
                "subtitles": "false",
                "ssml": "false",
            },
            "config": {
                "stitch": "true",
                "mute": "true"
            },
            "source_url": image_url
        }

        # Make the POST request
        response = requests.post(url, json=payload, headers=headers)
        # Check if the request was successful
        if response.status_code == 201:
            # Load the response text into a JSON object
            json_response = json.loads(response.text)
            return json_response['id']
        else:
            print("Error: POST request was not successful")

    def get_animation(self, id: str, output_path: str = 'd_id_animation.mp4') -> None:
        url = f"https://api.d-id.com/animations/{id}"
        print('Animation Video URL:', url)
        self.download_video(self.key, url, output_path)

    def get_credits(self):
        try:
            url = "https://api.d-id.com/credits"
            # Set the headers for the GET request
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": "Basic " + self.key
            }

            # Make the API request
            response = requests.get(url, headers=headers)
            remaining = response.json()['remaining']
            return remaining
        except Exception as e:
            print(f"An error occurred in get_credits function: {str(e)}")

# # Usage:
# # To use the DidVideo class, create an instance with your Basic token:
# vidgen = DidVideo(key=os.environ.get('D-ID_BASIC_TOKEN'))
# # Then, call the generate_audio method to generate audio from text:
# print(vidgen.get_credits())
