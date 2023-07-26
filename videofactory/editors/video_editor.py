import subprocess
import os
import configparser
from pathlib import Path


class VideoEditor:
    def __init__(self, width, height,
                 input_video=None, input_dir=None,
                 processed_dir=None, temp_dir=None, audio_dir=None,
                 processed_videos_dir=None, assets_dir=None,
                 watermark_text=None):

        self.input_video = input_video
        self.width = width
        self.height = height

        # Get the path of the current script (absolute path)
        current_script_path = Path(__file__).resolve()
        # Get the project folder (VideoFactory)
        project_folder = current_script_path.parent.parent.parent
        # Construct the path to config.ini in the parent folder
        config_path = project_folder / "config.ini"
        # Read the configuration file
        config = configparser.ConfigParser()
        config.read(config_path)

        # Use Path concatenation for input_dir, processed_dir, temp_dir, audio_dir, and processed_videos_dir
        self.input_dir = input_video or project_folder / config.get('paths', 'input_dir')
        self.processed_dir = processed_dir or project_folder / config.get('paths', 'processed_dir')
        self.temp_dir = temp_dir or project_folder / config.get('paths', 'temp_dir')
        self.audio_dir = audio_dir or project_folder / config.get('paths', 'audio_dir')
        self.processed_videos_dir = processed_videos_dir or project_folder / config.get('paths', 'processed_videos_dir')
        self.assets_dir = assets_dir or project_folder / config.get('paths', 'assets_dir')

        self.watermark_text = watermark_text or os.environ.get('WATERMARK_TEXT', '@YourChannel')

    @staticmethod
    def run_command(command):
        # Run the command with subprocess, using shell mode to execute the command as a string.
        # Set check=True to raise an exception if the command returns a non-zero exit code.
        # Redirect the standard output (stdout) and standard error (stderr) to /dev/null to suppress any output.
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")

    @staticmethod
    def find_closest_audio_match(mp4_file, videos_dir=None):
        # Get the project folder (VideoFactory)
        project_folder = Path(__file__).resolve().parent.parent.parent

        # Read the configuration file
        config = configparser.ConfigParser()
        config_path = project_folder / "config.ini"
        config.read(config_path)

        # Use Path concatenation for audio_dir, and processed_dir
        audio_dir = Path(project_folder / config.get('paths', 'audio_dir'))
        processed_dir = Path(project_folder / config.get('paths', 'processed_dir'))
        # print(processed_dir)

        if videos_dir is None:
            videos_dir = processed_dir

        audio_files = []

        # Scan all mp3 files in the "audio" directory and append their names and lengths to the audio_files list
        for file in os.listdir(audio_dir):
            if file.endswith(".mp3"):
                mp3_filepath = os.path.join(audio_dir, file).replace("\\", "/")  # Use forward slash instead of backslash
                length = int(round(float(subprocess.check_output(f'ffprobe -i "{mp3_filepath}" -show_entries format=duration -v quiet -of csv="p=0"', shell=True).decode())))

                audio_files.append({"name": file, "length": length})

        mp4_filepath = os.path.join(videos_dir, mp4_file).replace("\\", "/")  # Use forward slash instead of backslash
        mp4_duration = int(round(float(subprocess.check_output(f'ffprobe -i "{mp4_filepath}" -show_entries format=duration -v quiet -of csv="p=0"', shell=True).decode())))

        equal_match = None
        longest_match = None
        shortest_match = None
        min_difference = float('inf')

        for audio_file in audio_files:
            diff = audio_file["length"] - mp4_duration
            if diff == 0:  # If the audio file is the same length as the video file, choose it immediately
                equal_match = audio_file["name"]
                break
            elif diff > 0:  # If the audio file is longer than the video file
                if not shortest_match or audio_file['length'] < shortest_match['length']:
                    shortest_match = audio_file
                    continue
                elif not longest_match or audio_file['length'] > longest_match['length']:
                    longest_match = audio_file
            else:  # Choose the audio file that is closest in duration to the video file
                abs_diff = abs(mp4_duration - audio_file["length"])
                if abs_diff < min_difference:
                    closest_match = audio_file["name"]
                    min_difference = abs_diff

        if equal_match:
            closest_match = equal_match
        # If the longest audio file is still shorter in length than the video file, choose the longest audio file that is shorter than the video file
        elif longest_match and longest_match['length'] < mp4_duration:
            closest_match = longest_match['name']
        # Choose the shortest audio file that is greater in length than the video file
        elif shortest_match:
            closest_match = shortest_match['name']
        else:
            closest_match = min(audio_files, key=lambda x: abs(x['length'] - mp4_duration))['name']

        # print(f"The closest match is {closest_match}")
        # print(closest_match)
        # print(f"{mp4_file} ({mp4_duration}s) - {closest_match}")
        return closest_match

    def remove_d_id_watermark(self, input_image, output_video=None):
        output_video = output_video or self.input_video.replace("_d_id.mp4", "_no_watermark.mp4")

        # Resize video
        cmd_resize_video = (
            f'ffmpeg -i \"{self.input_video}\" -vf scale={self.width}:{self.height} '
            f'\"{self.input_video.replace(".mp4", "_resized.mp4")}\" -y'
        )
        self.run_command(cmd_resize_video)

        # Crop top portion of video
        crop_height = self.height * (862/960)
        cmd_crop_top_video = (
            f'ffmpeg -i \"{self.input_video.replace(".mp4", "_resized.mp4")}\" '
            f'-filter:v "crop=in_w:{crop_height}:0:0" '
            f'\"{self.input_video.replace(".mp4", "_cropped_top.mp4")}\" -y'
        )
        self.run_command(cmd_crop_top_video)

        # Resize image
        cmd_resize_png = (
            f'ffmpeg -i \"{input_image}\" -vf scale={self.width}:{self.height} '
            f'\"{input_image.replace(".png", "_resized.png")}\" -y'
        )
        self.run_command(cmd_resize_png)

        # Crop bottom portion of image
        crop_height = self.height * (98/960)
        cmd_crop_bottom_png = (
            f'ffmpeg -i \"{input_image.replace(".png", "_resized.png")}\" '
            f'-filter:v "crop=in_w:{crop_height}:0:{self.height}" '
            f'\"{input_image.replace(".png", "_cropped_bottom.png")}\" -y'
        )
        self.run_command(cmd_crop_bottom_png)

        # Combine top portion of the video with bottom portion of the image
        cmd_vstack_videos = (
            f'ffmpeg -i \"{self.input_video.replace(".mp4", "_cropped_top.mp4")}\" '
            f'-i \"{input_image.replace(".png", "_cropped_bottom.png")}\" '
            f'-filter_complex vstack=inputs=2 '
            f'\"{output_video}\" -y'
        )
        self.run_command(cmd_vstack_videos)

        # Deleting temporary files (For Unix-based systems: Use the 'rm' command)
        self.run_command(f'del \"{self.input_video.replace(".mp4", "_resized.mp4")}\"')
        self.run_command(f'del \"{self.input_video.replace(".mp4", "_cropped_top.mp4")}\"')
        self.run_command(f'del \"{input_image.replace(".png", "_resized.png")}\"')
        self.run_command(f'del \"{input_image.replace(".png", "_cropped_bottom.png")}\"')

        return output_video

    def merge_audio_files_with_fading_effects(self, basename=None):

        if not self.temp_dir.exists():  # Check if temp directory does not exist
            self.temp_dir.mkdir()  # Create temp directory
        if basename is None:
            basename = Path(self.input_video).stem.split("_")[0]

        audio_filename = Path(self.find_closest_audio_match(self.input_video)).stem

        # Merge audio files (narration from the video & music) with fading effects and color correction
        mp4_volume_temp_filepath = self.temp_dir / f"{basename}_volume_temp.mp4"
        audio_filepath = self.audio_dir / f"{audio_filename}.mp3"
        audio_volume_temp_filepath = self.temp_dir / f"{audio_filename}_volume_temp.mp3"
        merged_audio_temp_filepath = self.temp_dir / f"{basename}_merged_audio_temp.mp3"
        merged_audio_faded_temp_filepath = self.temp_dir / f"{basename}_merged_audio_faded_temp.mp3"
        mp4_shortest_temp_filepath = self.temp_dir / f"{basename}_shortest_temp.mp4"
        mp4_output_filepath = self.processed_videos_dir / f"{basename}_output.mp4"

        cmd_merge_audio_files_with_fading_effects = (
            f'ffmpeg -i "{self.input_video}" -af "volume=12dB" -c:v copy "{mp4_volume_temp_filepath}" -y && '
            f'ffmpeg -i "{audio_filepath}" -af "volume=-18.5dB" "{audio_volume_temp_filepath}" -y && '
            f'ffmpeg -i "{mp4_volume_temp_filepath}" -i "{audio_volume_temp_filepath}" '
            f'-filter_complex amix=inputs=2:duration=first "{merged_audio_temp_filepath}" -y && '
            f'ffmpeg -i "{merged_audio_temp_filepath}" -filter_complex "afade=d=0.3, areverse, afade=d=0.3, areverse" '
            f'"{merged_audio_faded_temp_filepath}" -y && '
            f'ffmpeg -i "{merged_audio_faded_temp_filepath}" -i "{mp4_volume_temp_filepath}" -map 0:a -map 1:v '
            f'-c:v copy -shortest "{mp4_shortest_temp_filepath}" -y && '
            f'ffmpeg -i "{mp4_shortest_temp_filepath}" -c:v libx264 -crf 18 -preset slow -profile:v high -level:v 4.1 '
            f'-pix_fmt yuv420p -colorspace bt709 -color_trc bt709 -color_primaries bt709 -c:a copy "{mp4_output_filepath}" -y'
        )
        # print("#######################################################################################################")
        # print('cmd_merge_audio_files_with_fading_effects')
        # print(cmd_merge_audio_files_with_fading_effects)
        # print("#######################################################################################################")
        self.run_command(cmd_merge_audio_files_with_fading_effects)

        # Remove temporary files
        mp4_volume_temp_filepath.unlink()
        audio_volume_temp_filepath.unlink()
        merged_audio_temp_filepath.unlink()
        merged_audio_faded_temp_filepath.unlink()
        mp4_shortest_temp_filepath.unlink()

        return mp4_output_filepath

    def add_watermark_text(self, basename=None):
        if not os.path.exists(self.temp_dir):  # Check if temp directory does not exist
            os.mkdir(self.temp_dir)  # Create temp directory
        if basename is None:
            basename = Path(self.input_video).stem.split("_")[0]

        # Add watermark text
        fontfile_filepath = os.path.join(self.assets_dir, 'fonts', 'Anton-Regular.ttf').replace("\\", "/").replace(":", "\\\\:")
        mp4_output_wm_filepath = os.path.join(self.processed_videos_dir, f'{basename}_output_wm.mp4').replace("\\", "/")
        cmd_add_watermark_text = (
            f'ffmpeg -i \"{self.input_video}\" -vf "drawtext=fontfile=\"{fontfile_filepath}\": text=\'{self.watermark_text}\': fontcolor=white@0.7: '
            f'fontsize=18: x=(w-text_w)/2: y=(h-text_h)*0.78" -codec:a copy \"{mp4_output_wm_filepath}\" -y && '
            f'rmdir /q \"{self.temp_dir}\"'
        )
        # print("#######################################################################################################")
        # print('cmd_add_watermark_text')
        # print(cmd_add_watermark_text)
        # print("#######################################################################################################")
        self.run_command(cmd_add_watermark_text)

        return mp4_output_wm_filepath

    def join_videos(self, input_videos, output_filepath=None):
        # Create a string of input options for FFmpeg
        input_options = ""
        for input_video in input_videos:
            input_options += f'-i "{input_video}" '

        # Construct the FFmpeg command to join the videos
        filter_complex = ""
        stream_concatenation = ""

        for i in range(len(input_videos)):
            filter_complex += f"[{i}:v:0]setsar=1[sar{i}];"
            stream_concatenation += f"[sar{i}][{i}:a:0]"

        command = (
            f'ffmpeg {input_options}-filter_complex '
            f'"{filter_complex}{stream_concatenation}concat=n={len(input_videos)}:v=1:a=1[outv][outa]" '
            f'-map "[outv]" -map "[outa]" \"{output_filepath}\" -y'
        )

        # Execute the FFmpeg command using os.system
        # print(command)
        self.run_command(command)

        return output_filepath
