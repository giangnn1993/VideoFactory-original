import os
from pathlib import Path

from generators.text_generator import TextGenerator
from generators.image_generator import ImageGenerator
from generators.tts_generator import TTSGenerator
from generators.video_generator import VideoGenerator
from generators.subtitle_generator import SubtitleGenerator

from _utils import read_lines, compare_lines_lists, process_text, get_basenames, create_images_and_audios_dict

from editors.video_editor import VideoEditor


class WorkflowManager:
    def __init__(self):
        self.text_generator = TextGenerator('g4f')  # Initialize ImageGenerator object
        self.image_generator = ImageGenerator('automatic1111')  # Initialize ImageGenerator object
        self.tts_generator = TTSGenerator()  # Initialize TTSGenerator object
        self.video_generator = VideoGenerator('d-id')  # Initialize VideoGenerator object
        self.subtitle_generator = SubtitleGenerator()  # Initialize SubtitleGenerator object

        self.video_editor = VideoEditor(width=540, height=960)  # Initialize VideoEditor object

    def check_talking_head_videos_resources(self, lines_file, thumbnail_lines_file, images_dir):
        try:
            # Read the content of the lines_file and thumbnail_lines_file
            lines_list = read_lines(lines_file)
            thumbnail_lines_list = read_lines(thumbnail_lines_file)

            # Compare if the number of lines in both files are equal, if not exit
            if not compare_lines_lists(lines_list, thumbnail_lines_list):
                print("Error: The number of lines in the files does not match.")
                return False

            # Process each line in both files to get the strings
            lines_first_parts = [process_text(line)[0] for line in lines_list]
            thumbnail_lines_first_parts = [process_text(thumbnail_line)[0] for thumbnail_line in thumbnail_lines_list]

            # Compare the two lists containing strings of first_line, if they are not the same exit
            if lines_first_parts != thumbnail_lines_first_parts:
                print("Error: The first parts (in square brackets) in both files do not match.")
                return False

            # Get the basenames of files in the images_dir with the specified file_extension
            file_extension = '.png'
            basenames = get_basenames(images_dir, file_extension)

            # Compare the basenames of files with the earlier list
            if not set(basenames).issuperset(set(lines_first_parts)):
                print("Error: The basenames of files in the images_dir do not include all items from the earlier list.")
                return False

        except FileNotFoundError as e:
            print(f"Error: {e.filename} not found.")
            return False
        except IOError as e:
            print(f"Error: I/O error occurred - {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

        # If all steps are passed without any errors, return True
        return True

    def generate_talking_head_videos(self, lines_file, thumbnail_lines_file, images_dir) -> Path:
        # Check if the necessary resources are available using check_talking_head_videos_resources
        if self.check_talking_head_videos_resources(lines_file, thumbnail_lines_file, images_dir):
            # Define the output directory path for generated audio files based on the input 'lines_file'
            output_dir = Path(lines_file).parent / Path(lines_file).stem

            # region Step 1: GENERATE AUDIOS
            # ------------------------------------
            # Set the TTS provider to be used based on the environment variable 'TTS_PROVIDER'
            # The TTS provider will determine which Text-to-Speech engine or service to use.
            self.tts_generator.set_tts_provider(os.environ.get('TTS_PROVIDER'))

            # Generate audio files from the text in 'lines_file' using TTS generator
            # The output audio files will be saved in the 'output_dir' directory.
            self.tts_generator.generate_audios_from_txt(input_file=lines_file,
                                                        output_dir=output_dir)
            # endregion

            # region Step 2: GENERATE D-ID VIDEOS
            # ------------------------------------
            self.video_generator.key = os.environ.get('D-ID_BASIC_TOKEN')

            # Get the basenames of files in the output_dir with the specified file_extension
            png_basenames = get_basenames(images_dir, '.png')
            wav_basenames = get_basenames(output_dir, '.wav')

            # Compare png_basenames with wav_basenames
            if not set(png_basenames).issuperset(set(wav_basenames)):
                print(f"""Error: png_basenames in
                        {images_dir}
                        do not include all items in wav_basenames in
                        {output_dir}.""")
                return False

            images_and_audios_dict = create_images_and_audios_dict(
                basenames=wav_basenames,
                images_dir=images_dir,
                d_id_videos_dir=output_dir)

            output_ids_file = self.video_generator.create_talk_videos_from_images_and_audios(
                images_and_audios_dict=images_and_audios_dict,
                output_dir=output_dir)

            # output_ids_file = Path(output_dir) / 'd-id_output_ids.json' # For debugging purposes
            self.video_generator.get_talks_from_json(output_ids_file=output_ids_file, output_dir=output_dir)
            # endregion

            return output_dir

    def edit_talking_head_videos(self, images_dir, videos_dir):
        # region Step 1: VALIDATE RESOURCES
        # ------------------------------------
        basenames = get_basenames(videos_dir, '_d_id.mp4')
        d_id_mp4_basenames = [file.replace('_d_id', '') for file in basenames]
        png_basenames = get_basenames(images_dir, '.png')

        # Compare the basenames of files with the earlier list
        if not set(png_basenames).issuperset(set(d_id_mp4_basenames)):
            print("Error: The basenames of files in the images_dir do not include all items from the videos_dir.")
            return False
        # endregion

        # region Step 2: REMOVE D-ID WATERMARKS
        # ------------------------------------
        # Get all files in the videos_dir directory with the extension '_d_id.mp4'
        d_id_mp4_files = list(videos_dir.glob('*_d_id.mp4'))
        for d_id_mp4_file in d_id_mp4_files:
            input_image = str(Path(images_dir) / (d_id_mp4_file.stem.replace('_d_id', '') + '.png'))
            self.video_editor.input_video = str(d_id_mp4_file)
            self.video_editor.remove_d_id_watermark(input_image=input_image)
        # endregion

        # region Step 3: ADD SUBTITLES
        # Get all files in the videos_dir directory with the extension '_d_id.mp4'
        no_watermark_mp4_files = list(videos_dir.glob('*_no_watermark.mp4'))
        for no_watermark_mp4_file in no_watermark_mp4_files:
            # Generate subtitle
            subtitle_file = self.subtitle_generator.generate_subtitle(input_video=no_watermark_mp4_file)
            # Modify subtitle with styles
            modified_subtitle_file = self.subtitle_generator.modify_subtitle(subtitle_file)
            # Burn subtitle
            subtitled_file = self.subtitle_generator.burn_subtitle(
                            input_video=no_watermark_mp4_file,
                            subtitle_file=modified_subtitle_file)
        # endregion

        # region Step 4: EDIT
        # Get all files in the videos_dir directory with the extension '_d_id.mp4'
        subtitled_mp4_files = list(videos_dir.glob('*_subtitled.mp4'))
        for subtitled_mp4_file in subtitled_mp4_files:
            # Add music
            self.video_editor.input_video = subtitled_mp4_file
            mp4_output_filepath = self.video_editor.merge_audio_files_with_fading_effects()

            # Add watermark text
            self.video_editor.input_video = mp4_output_filepath
            mp4_output_wm_filepath = self.video_editor.add_watermark_text()

            # Add thumbnail

        # endregion


# Example usage:
lines_file = r"D:\Projects\Python\VideoFactory\data\output\processed\anecdotes about friendship_DeepAi\lines_anecdotes about friendship_DeepAi.txt"
thumbnail_lines_file = r"D:\Projects\Python\VideoFactory\data\output\processed\anecdotes about friendship_DeepAi\thumbnail_lines_anecdotes about friendship_DeepAi.txt"
images_dir = r"D:\Projects\Python\VideoFactory\data\output\processed\anecdotes about friendship_DeepAi"
workflow_manager = WorkflowManager()  # Create an instance of WorkflowManager
# workflow_manager.generate_talking_head_videos(lines_file, thumbnail_lines_file, images_dir)
output_dir = Path(lines_file).parent / Path(lines_file).stem
workflow_manager.edit_talking_head_videos(images_dir=images_dir, videos_dir=output_dir)
