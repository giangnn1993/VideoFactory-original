import os
import subprocess
from pathlib import Path
import configparser
from PIL import Image, ImageDraw, ImageFont


# self.fonts_dir = os.path.join(self.assets_dir, 'fonts')
# self.images_dir = os.path.join(self.assets_dir, 'images')
# self.thumbnail_overlays_dir = os.path.join(self.assets_dir, 'thumbnail_overlays')
# self.output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'output'))


class ThumbnailGenerator:
    def __init__(self, overlay=None, font=None, assets_dir=None, input_dir=None,
                 processed_dir=None, temp_dir=None, audio_dir=None, processed_videos_dir=None,
                 fonts_dir=None, images_dir=None, thumbnail_overlays_dir=None, output_dir=None):
        self.overlay = overlay or os.environ.get('THUMBNAIL_OVERLAY', 'glitch')
        self.font = font or os.environ.get('THUMBNAIL_FONT', 'Anton-Regular')

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
        self.input_dir = input_dir or project_folder / config.get('paths', 'input_dir')
        self.processed_dir = processed_dir or project_folder / config.get('paths', 'processed_dir')
        self.temp_dir = temp_dir or project_folder / config.get('paths', 'temp_dir')
        self.audio_dir = audio_dir or project_folder / config.get('paths', 'audio_dir')
        self.processed_videos_dir = processed_videos_dir or project_folder / config.get('paths', 'processed_videos_dir')
        self.assets_dir = assets_dir or project_folder / config.get('paths', 'assets_dir')
        self.fonts_dir = self.assets_dir / 'fonts'
        self.images_dir = self.assets_dir / 'images'
        self.thumbnail_overlays_dir = self.assets_dir / 'thumbnail_overlays'
        self.output_dir = project_folder / 'data' / 'output'

        # Convert all paths to Path objects
        self.assets_dir = Path(self.assets_dir)
        self.input_dir = Path(self.input_dir)
        self.processed_dir = Path(self.processed_dir)
        self.temp_dir = Path(self.temp_dir)
        self.audio_dir = Path(self.audio_dir)
        self.processed_videos_dir = Path(self.processed_videos_dir)

    @staticmethod
    def run_command(command):
        # Run the command with subprocess, using shell mode to execute the command as a string.
        # Set check=True to raise an exception if the command returns a non-zero exit code.
        # Redirect the standard output (stdout) and standard error (stderr) to /dev/null to suppress any output.
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")

    def extract_first_frame(self, video_file, output_path=None):
        if output_path is None:
            output_path = Path(video_file).parent / Path(video_file).stem

        # Use pathlib for paths and avoid string formatting
        output_path = Path(output_path)
        video_file = Path(video_file)

        command = [
            'ffmpeg',
            '-i', str(video_file),
            '-vframes', '1',
            str(output_path.with_suffix('.png')),
            '-y'
        ]

        # Execute the command
        self.run_command(command)

        # Return the output path
        return output_path.with_suffix('.png')

    def merge_images(self, input_filename, overlay_filename, text,
                     output_filename=None, input_image_path=None):

        # Open the input and overlay images
        if input_image_path is None:
            input_image_path = Image.open(os.path.join(self.images_dir, input_filename))

        input_image = Image.open(input_image_path)
        overlay_image = Image.open(os.path.join(self.thumbnail_overlays_dir, overlay_filename))

        # Resize the input image to 540x960
        input_image = input_image.resize((540, 960))

        # Resize the overlay image to match the size of the input image
        overlay_image = overlay_image.resize(input_image.size)

        # Create a new blank image with the same size as the input image
        merged_image = Image.new("RGBA", input_image.size, (0, 0, 0, 0))

        # Paste the input image onto the blank image
        merged_image.paste(input_image, (0, 0))

        # Paste the overlay image onto the merged image, using the alpha channel of the overlay image for transparency
        merged_image.alpha_composite(overlay_image)

        # Add text to the image within the specified area
        draw = ImageDraw.Draw(merged_image)
        font_name = ImageFont.truetype(os.path.join(self.fonts_dir, self.font + '.ttf'), 40)
        max_width = 366
        words = text.split()
        lines = []
        line = ''
        for word in words:
            if draw.textsize(line + ' ' + word, font=font_name)[0] <= max_width:
                line += ' ' + word if line else word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)

        # Limit the number of lines to 2
        if len(lines) > 2:
            lines = lines[:2]

        if len(lines) == 2:
            y = 585
        elif len(lines) == 1:
            y = 620

        for line in lines:
            text_width, text_height = draw.textsize(line.strip(), font=font_name)
            x = (merged_image.width - text_width) // 2
            if self.overlay in ['tint', 'skew']:
                draw.text((x, y), line.strip(), font=font_name, fill=(0, 0, 0))  # black
            elif self.overlay == 'glitch':
                draw.text((x, y), line.strip(), font=font_name, fill=(255, 255, 255))  # white
            y += text_height

        # Save the result to a file
        if output_filename is None:
            output_filename = input_filename[:-4]
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)

        output_path = os.path.join(self.temp_dir, output_filename + "_thumbnail.png")
        merged_image.save(os.path.join(self.temp_dir, output_filename + "_thumbnail.png"))

        return output_path

    def generate_thumbnail_images(self):
        # Read the file
        if os.path.exists(os.path.join(self.input_dir, 'thumbnail_lines.txt')):
            with open(os.path.join(self.input_dir, 'thumbnail_lines.txt'), 'r') as f:
                lines = f.readlines()
                line_number = 1
                for line in lines:
                    if line:  # Check if line is not empty
                        if '[' in line and ']' in line:  # Check if line contains [ and ]
                            input_filename = line[line.find('[')+1:line.find(']')] + '.png'
                            overlay_filename = self.overlay + '.png'
                            text = line[line.find(']')+1:]
                            self.merge_images(input_filename, overlay_filename, text)
                        else:
                            print("Line " + str(line_number) + " does not contain the characters")
                    line_number += 1
        else:
            print("File not found")

    def generate_thumbnail_image(self, input_filename, text, output_filename=None, input_image_path=None):
        input_filename = input_filename + '.png'
        overlay_filename = self.overlay + '.png'
        text = text
        output_path = self.merge_images(input_filename, overlay_filename, text, output_filename, input_image_path)

        return output_path

    def generate_thumbnail_videos(self):
        # Get all files in temp directory
        files = os.listdir(self.temp_dir)

        # Iterate through each file
        for file in files:
            # Check if the file ends with '_thumbnail.png'
            if file.endswith('_thumbnail.png'):
                thumbnail_file = file
                self.generate_thumbnail_video(thumbnail_file)

    def generate_thumbnail_video(self, thumbnail_image_name):
        # Get the part before _
        name = thumbnail_image_name.split('_')[0]

        # Look for the mp4 file in the 'processed_videos' folder
        mp4_filepath = self.processed_videos_dir / (name + '_output_wm.mp4')

        # All paths use forward slash instead of backslash
        thumbnail_filepath = self.temp_dir / thumbnail_image_name
        thumbnail_resized_filepath = self.temp_dir / (name + '_thumbnail_resized.png')
        mp4_thumbnail_filepath = self.temp_dir / (name + '_thumbnail.mp4')
        mp4_output_wm_cover_filepath = self.processed_videos_dir / (name + '_output_wm_thumbnail.mp4')

        command = (
            # Resize the thumbnail image to 540x960
            f'ffmpeg -i "{thumbnail_filepath}" -s 540x960 "{thumbnail_resized_filepath}" -y && '
            # Generate a loop video from the thumbnail image with a duration of 0.5s
            f'ffmpeg -loop 1 -i "{thumbnail_resized_filepath}" -f lavfi -i '
            f'anullsrc=channel_layout=stereo:sample_rate=44100 -c:v libx264 '
            f'-t 0.5 -r 30 -pix_fmt yuv420p -c:a aac -shortest "{mp4_thumbnail_filepath}" -y && '
            # Concatenate the thumbnail loop video with the watermarked video
            f'ffmpeg -i "{mp4_thumbnail_filepath}" -i "{mp4_filepath}" -filter_complex '
            f'"[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1" -c:v libx264 -preset veryfast '
            f'-crf 23 -c:a aac -b:a 128k "{mp4_output_wm_cover_filepath}" -y && '
            # Delete temporary files
            f'del "{thumbnail_filepath}" '
            f'"{thumbnail_resized_filepath}" '
            f'"{mp4_thumbnail_filepath}" && '
            f'rmdir /q "{self.temp_dir}"'
        )
        # print(command)
        # Run the command
        self.run_command(command)
        return mp4_output_wm_cover_filepath
