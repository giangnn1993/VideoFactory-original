import os
import json
import re
import subprocess
import stable_whisper
import pysubs2
import configparser
from pathlib import Path


class SubtitleGenerator:
    def __init__(self,
                 model=None,
                 assets_dir=None,
                 input_dir=None,
                 processed_dir=None):

        self.model = model or stable_whisper.load_model('base')

        # Get the project folder (VideoFactory)
        project_folder = Path(__file__).resolve().parent.parent.parent

        # Read the configuration file
        config = configparser.ConfigParser()
        config_path = project_folder / "config.ini"
        config.read(config_path)

        # Use Path concatenation for assets_dir, input_dir, and processed_dir
        self.assets_dir = assets_dir or (project_folder / config.get('paths', 'assets_dir'))
        self.input_dir = input_dir or (project_folder / config.get('paths', 'input_dir'))
        self.processed_dir = Path(processed_dir or (project_folder / config.get('paths', 'processed_dir')))

    def modify_text(self, subtitle_file, videos_dir=None, case=None):
        videos_dir = Path(videos_dir or self.processed_dir)

        # Load the subtitle file
        subs = pysubs2.load(str(videos_dir / subtitle_file))

        # Define a regular expression pattern for tags
        TAG_PATTERN = r'{[^{}]*}'

        # Loop over all the subtitles in the file
        for sub in subs:
            # Split the text into tag groups and non-tag groups
            tag_groups = re.findall(TAG_PATTERN, sub.text)
            non_tag_groups = re.split(TAG_PATTERN, sub.text)

            case = case or os.environ.get("SUBTITLE_CASE", None)

            if case is not None:
                case = case.lower()

            # Define mapping of case values to string methods
            case_mapping = {
                'uppercase': str.upper,
                'lowercase': str.lower,
                'titlecase': lambda x: re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                                              lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), x),
            }

            # Convert non-tag groups based on the specified case
            if case in case_mapping:
                non_tag_groups = [case_mapping[case](group) for group in non_tag_groups]

            # Merge the tag groups and non-tag groups back together
            merged_text = ''.join(a + (b or '') for a, b in zip(non_tag_groups, tag_groups + [None]))

            # Update the subtitle text with the modified text
            sub.text = merged_text

        # Save the modified subtitle file
        subs.save(os.path.join(videos_dir, subtitle_file))

    def prepend_string_to_subtitle(self, subtitle_file, prepend_string=None, videos_dir=None):
        # Load subtitle styling parameters
        prepend_string = prepend_string or os.environ.get("SUBTITLE_PREPEND_STRING", None)
        print('Subtitle prepend string:', prepend_string)
        videos_dir = videos_dir or self.processed_dir

        with open(self.assets_dir / 'subtitle-styles.json', 'r') as f:
            prepend_strings = json.load(f)['prepend_strings']

        # Check if option is present in the provided options dictionary
        if prepend_string in prepend_strings:
            # Open the subtitle file for reading
            subs = pysubs2.load(videos_dir / subtitle_file)
            # Iterate over each line in the subtitle file
            for line in subs:
                # Prepend the required string to the current line text
                line.text = prepend_strings[prepend_string] + line.text
            # Save the modified subtitle file
            subs.save(videos_dir / subtitle_file)
        else:
            print("Subtitle modified without prepend string.")

    def get_video_dimensions(self, input_file):
        # Get the size of the video using ffprobe
        ffprobe_cmd = (f'ffprobe -v error -select_streams v:0 -show_entries stream=width,'
                       f'height -of csv=s=x:p=0 "{input_file}"')
        video_size = subprocess.check_output(ffprobe_cmd, shell=True).decode().strip().split("x")
        play_res_x = video_size[0]
        play_res_y = video_size[1]
        print(f'Video Resolution: {play_res_x}x{play_res_y}')
        return play_res_x, play_res_y

    def generate_subtitles(self, style=None, videos_dir=None):
        videos_dir = videos_dir or self.processed_dir
        # Load subtitle styling parameters from JSON file
        with open(self.assets_dir / 'subtitle-styles.json', 'r') as f:
            subtitle_style = json.load(f)["styles"][style]
            gap_split_value = subtitle_style['gap_split_value']
            gap_merge_value = subtitle_style['gap_merge_value']
            max_words_in_merge = subtitle_style['max_words_in_merge']

        videos_dir_path = Path(videos_dir)
        for f in videos_dir_path.iterdir():
            if f.endswith(('_no_watermark')):
                input_filepath = videos_dir_path / f.name
                subtitle_file = f'{f.stem}.ass'
                subtitle_filepath = videos_dir_path / subtitle_file
                output_file = f'{f.stem}_subtitled.mp4'
                output_filepath = videos_dir_path / output_file

                transcription_output = self.model.transcribe(input_filepath, regroup=False)
                (
                    transcription_output
                    .split_by_punctuation([('.', ' '), '。', '?', '？', ',', '，'])
                    .split_by_gap(gap_split_value)
                    .merge_by_gap(gap_merge_value, max_words=max_words_in_merge)
                    .split_by_punctuation([('.', ' '), '。', '?', '？'])
                    .split_by_length(max_words=subtitle_style['length_max_words'],
                                     max_chars=subtitle_style['length_max_chars'])
                )

                transcription_output.to_ass(
                        filepath=subtitle_filepath,
                        font_size=subtitle_style['kwargs']['Fontsize'],
                        highlight_color=subtitle_style['kwargs']['PrimaryColour'],
                        strip=True, karaoke=subtitle_style['karaoke_enable'],
                        **subtitle_style['kwargs']
                    )

                # Check if the variable 'style' ends with '_ko':
                if style.endswith('_ko'):
                    # Read the .ass file and replace all instances of "{\\k" with "{\\ko":
                    with open(subtitle_filepath, 'r', encoding='utf-8') as file:
                        text = file.read().replace(r"{\k", r"{\ko")
                    with open(subtitle_filepath, 'w', encoding='utf-8') as file:
                        file.write(text)

                # Call modify_text to change the case of the subtitle, default to None
                self.modify_text(subtitle_file, videos_dir)
                # Call prepend_string_to_subtitles to prepend_string to the subtitle, default to None
                self.prepend_string_to_subtitle(subtitle_file, videos_dir)
                # Get video dimensions
                play_res_x, play_res_y = self.get_video_dimensions(input_filepath)

                # Burn subtitle into the video file
                # Use forward slash instead of backslash and additional escaping for colon
                normalized_input_filepath = input_filepath.replace("\\", "/")
                normalized_subtitle_filepath = subtitle_filepath.replace("\\", "/").replace(":", "\\\\:")
                normalized_output_filepath = output_filepath.replace("\\", "/")

                ffmpeg_cmd = (
                    f'ffmpeg -i "{normalized_input_filepath}" -vf "subtitles={normalized_subtitle_filepath}:'
                    f'force_style=\'PlayResX={play_res_x},PlayResY={play_res_y}\'" -c:a copy '
                    f'"{normalized_output_filepath}" -y'
                )
                # print(ffmpeg_cmd)
                # Execute the ffmpeg command
                subprocess.call(ffmpeg_cmd, shell=True, check=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def generate_subtitle(self, input_video, style=None):
        input_video_path = Path(input_video)
        subtitle_file = f'{input_video_path.stem}.ass'
        subtitle_filepath = input_video_path.parent / subtitle_file
        # output_file = f'{input_video_path.stem}_subtitled.mp4'
        # output_filepath = input_video_path.parent / output_file

        # Load subtitle styling parameters
        style = style or os.environ.get("SUBTITLE_STYLE", "default")
        print('Subtitle style:', style)

        with open(self.assets_dir / 'subtitle-styles.json', 'r') as f:
            subtitle_style = json.load(f)["styles"][style]
            gap_split_value = subtitle_style['gap_split_value']
            gap_merge_value = subtitle_style['gap_merge_value']
            max_words_in_merge = subtitle_style['max_words_in_merge']

        transcription_output = self.model.transcribe(str(input_video), regroup=False)
        (
            transcription_output
            .split_by_punctuation([('.', ' '), '。', '?', '？', ',', '，'])
            .split_by_gap(gap_split_value)
            .merge_by_gap(gap_merge_value, max_words=max_words_in_merge)
            .split_by_punctuation([('.', ' '), '。', '?', '？'])
            .split_by_length(max_words=subtitle_style['length_max_words'],
                             max_chars=subtitle_style['length_max_chars'])
        )

        transcription_output.to_ass(
                filepath=str(subtitle_filepath),
                font_size=subtitle_style['kwargs']['Fontsize'],
                highlight_color=subtitle_style['kwargs']['PrimaryColour'],
                strip=True, karaoke=subtitle_style['karaoke_enable'],
                **subtitle_style['kwargs']
            )

        return str(subtitle_filepath)

    def modify_subtitle(self, subtitle_file, style=None):
        # Load subtitle styling parameters
        style = style or os.environ.get("SUBTITLE_STYLE", "default")

        with open(subtitle_file, 'r', encoding='utf-8') as file:
            text = file.read()
            # Check if the variable 'style' ends with '_ko':
            if style.endswith('_ko'):
                # Read the .ass file and replace all instances of "{\\k" with "{\\ko":
                text = text.replace(r"{\k", r"{\ko")

            modified_subtitle_file = Path(subtitle_file).with_name(f"{Path(subtitle_file).stem}_modified.ass")
            with open(modified_subtitle_file, 'w', encoding='utf-8') as file:
                file.write(text)

            # Call modify_text to change the case of the subtitle, default to None
            self.modify_text(str(modified_subtitle_file), Path(subtitle_file).parent)
            # Call prepend_string_to_subtitles to prepend_string to the subtitle, default to None
            self.prepend_string_to_subtitle(subtitle_file=str(modified_subtitle_file),
                                            videos_dir=Path(subtitle_file).parent)

            return modified_subtitle_file

    def burn_subtitle(self, input_video, subtitle_file):

        # Get video dimensions
        play_res_x, play_res_y = self.get_video_dimensions(input_video)

        output_file = f'{input_video.stem}_subtitled.mp4'
        output_filepath = input_video.parent / output_file
        # Burn subtitle into the video file
        # Use forward slash instead of backslash and additional escaping for colon
        normalized_input_filepath = str(input_video).replace("\\", "/")
        normalized_subtitle_filepath = str(subtitle_file).replace("\\", "/").replace(":", "\\\\:")
        normalized_output_filepath = str(output_filepath).replace("\\", "/")

        ffmpeg_cmd = (
            f'ffmpeg -i "{normalized_input_filepath}" -vf "subtitles={normalized_subtitle_filepath}:'
            f'force_style=\'PlayResX={play_res_x},PlayResY={play_res_y}\'" -c:a copy "{normalized_output_filepath}" -y'
        )
        # print(ffmpeg_cmd)
        # Execute the ffmpeg command
        subprocess.call(ffmpeg_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return output_filepath
