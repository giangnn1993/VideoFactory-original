import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

from .generators.text_generator import TextGenerator
from .generators.image_generator import ImageGenerator
from .generators.tts_generator import TTSGenerator
from .generators.video_generator import VideoGenerator, LastKeyReachedException
from .generators.subtitle_generator import SubtitleGenerator
from .generators.thumbnail_generator import ThumbnailGenerator

from ._utils import (
    read_lines,
    compare_lines_lists,
    process_text,
    get_basenames,
    create_images_and_audios_dict,
    create_script_folder,
    create_script_folders,
    parse_response_quote,
    parse_response_image,
    normalize_string,
    combine_csv_files,
    generate_line_files
)

from .editors.video_editor import VideoEditor
from .editors.audio_editor import AudioEditor

from .utils.topaz import temp_working_directory, enhance_video_with_ai


class WorkflowManager:
    def __init__(self):
        self.text_generator = TextGenerator('g4f')  # Initialize ImageGenerator object
        self.image_generator = ImageGenerator('automatic1111')  # Initialize ImageGenerator object
        self.tts_generator = TTSGenerator()  # Initialize TTSGenerator object
        self.video_generator = VideoGenerator()  # Initialize VideoGenerator object
        self.subtitle_generator = SubtitleGenerator()  # Initialize SubtitleGenerator object
        self.thumbnail_generator = ThumbnailGenerator()  # Initialize ThumbnailGenerator object

        self.video_editor = VideoEditor(width=540, height=960)  # Initialize VideoEditor object
        self.audio_editor = AudioEditor()  # Initialize AudioEditor object

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
            # Create script folders to store lines of text from 'lines_file' as separate files
            script_folders = create_script_folders(txt_file=lines_file, split_lines=True)

            for script_folder in script_folders:
                audio_files = []

                # Set the TTS provider to be used based on the environment variable 'TTS_PROVIDER'
                # The TTS provider will determine which Text-to-Speech engine or service to use.
                self.tts_generator.set_tts_provider(os.environ.get('TTS_PROVIDER'))

                # Generate audio files from the text in 'lines_file' using TTS generator
                # The output audio files will be saved in the 'script_folder' directory.

                # Construct the Path to the script text file
                script_file = script_folder / 'script.txt'

                # Check if the script file exists
                if script_file.is_file():
                    # Create a Path object for the audio file with the same
                    # name as the'script_folder' but with the extension '.wav'
                    audio_file = Path(script_folder.parent, f'{script_folder.name}.wav')

                    # Check if the audio file does not exist
                    if not audio_file.is_file():
                        audio_files = self.tts_generator.generate_audios_from_txt(
                                                                    input_file=script_file,
                                                                    output_dir=script_folder)

                        # Merge the generated audio files with padding to create a single audio file
                        # The merged audio file will be saved in the 'output_dir'.
                        self.audio_editor.input_audio_files = audio_files
                        self.audio_editor.merge_audios_with_padding(output_dir=output_dir,
                                                                    name=script_folder.name)
                    else:
                        print(f'{audio_file} already exists. Skipping...')
            # endregion

            # region Step 2: GENERATE D-ID VIDEOS
            # ------------------------------------
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
                audios_dir=output_dir)

            # Set the key for the video generator by rotating through a list of keys.
            # The video generator will use the provided key for generating videos.
            output_ids_file = self.video_generator.create_talk_videos_from_images_and_audios(
                images_and_audios_dict=images_and_audios_dict,
                output_dir=output_dir,
                keys=os.environ.get('D-ID_BASIC_TOKENS'))

            # # This line is only for debugging purposes.
            # output_ids_file = Path(output_dir) / 'd-id_output_ids.json'

            # Download generated videos
            self.video_generator.get_talks_from_json(output_ids_file=output_ids_file, output_dir=output_dir)
            # endregion

            return output_dir

    def edit_talking_head_videos(self, thumbnail_lines_file, images_dir, videos_dir):
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
            # subtitled_file = self.subtitle_generator.burn_subtitle(
            #                 input_video=no_watermark_mp4_file,
            #                 subtitle_file=modified_subtitle_file)
            self.subtitle_generator.burn_subtitle(
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
            # mp4_output_wm_filepath = self.video_editor.add_watermark_text()
            self.video_editor.add_watermark_text()
        # endregion

        # region Step 5: ADD THUMBNAILS
        thumbnail_lines = read_lines(thumbnail_lines_file)
        for thumbnail_line in thumbnail_lines:
            first_part, outside_text, _ = process_text(thumbnail_line)
            no_watermark_mp4_file = videos_dir / f'{first_part}_no_watermark.mp4'
            if Path(no_watermark_mp4_file).is_file():
                first_frame = self.thumbnail_generator.extract_first_frame(video_file=no_watermark_mp4_file)
                self.thumbnail_generator.generate_thumbnail_image(
                    input_filename=first_frame.name.split('_')[0],
                    input_image_path=first_frame,
                    text=outside_text)

                self.thumbnail_generator.generate_thumbnail_videos()  # Generate thumbnail videos

        # endregion

    def generate_quotes(self, input_query: str = None):
        input_query = normalize_string(input_query.strip())

        # Call the generate_chat_responses function with a query:
        prompt = self.text_generator.create_few_shot_prompt_template(
            query=input_query,
            examples=self.text_generator.examples_quote,
            prefix=self.text_generator.prefix_quote
        )
        responses = self.text_generator.generate_chat_responses(query=prompt)
        # Iterate over the responses and print the response and provider name
        if responses is not None:

            output_dir = Path(self.text_generator.processed_dir / input_query)
            output_dir.mkdir(exist_ok=True)
            csv_dir = Path(output_dir / 'csv')
            csv_dir.mkdir(exist_ok=True)

            for response, provider_name in responses:
                print('+-----------------------------------------------------------------------------+')
                print(f' User: {input_query} ')
                print(f' {provider_name}: ')

                result_lists = parse_response_quote(input_query, provider_name, json_data=response)

                df = pd.DataFrame(
                    {
                        "input_query": result_lists[0],  # input_query_list
                        "provider_name": result_lists[1],  # provider_name_list
                        "topic": result_lists[2],  # topic_list
                        "quote": result_lists[3],  # quote_list
                        "short": result_lists[4]  # short_list
                    }
                )

                # Add a new column "length" containing the length of the current value in the "short" column
                df["short_length"] = df["short"].apply(len)

                # Save DataFrame to a CSV file
                csv_file_path = csv_dir / f'{input_query}_{provider_name}.csv'
                df.to_csv(csv_file_path, index=False)

            output_path = Path(output_dir / f'{input_query}.csv')
            combined_csv_path = combine_csv_files(directory=csv_dir, output_path=output_path)

            quotes_file_path, shorts_file_path = generate_line_files(input_csv=combined_csv_path)

            return quotes_file_path, shorts_file_path

        else:
            print('Error occurred while generating chat response')
            return

    def generate_image_prompts_from_txt(self, input_file: Path, output_dir: Path = None) -> Path:
        quotes_list = read_lines(input_file)
        # Calculate the zero-padding for the index number based on the maximum line number
        max_line_number = len(str(len(quotes_list)))

        for i, quote in enumerate(quotes_list, start=1):
            prompt = self.text_generator.create_few_shot_prompt_template(
                query=quote,
                examples=self.text_generator.examples_image,
                prefix=self.text_generator.prefix_image
            )
            responses = self.text_generator.generate_chat_responses(query=prompt)

            # Get the output directory path based on the input file name
            csv_dir = Path(output_dir or self.text_generator.processed_dir / input_file.parent) / 'art_prompts'
            # Create the output directory if it doesn't exist
            csv_dir.mkdir(exist_ok=True)
            # Extract the first part of the quote using the process_text function
            first_part, _, _ = process_text(quote)
            # Create the base path for the prompts file within the output directory
            basepath = csv_dir / first_part
            # Generate the file path for the prompts file
            prompts_file_path = f'{basepath}_automatic1111.txt'

            # Iterate over the responses and print the response and provider name
            if responses is not None:
                # Lists to capture all quote_list and short_list values
                # all_topics = []
                all_prompts = []

                for response, provider_name in responses:
                    print('+-----------------------------------------------------------------------------+')
                    print(f' User: {quote} ')
                    print(f' {provider_name}: ')

                    result_lists = parse_response_image(quote, provider_name, json_data=response)
                    if (result_lists):
                        # Append values to the all_topic and all_prompts lists
                        # all_topics.extend(result_lists[2])  # topic_list

                        # Concatenate media, subject, describe, and art with commas
                        all_prompts.append(",".join(result_lists[3:7]))

                        df = pd.DataFrame(
                            {
                                "input_query": [result_lists[0]],  # input_query
                                "provider_name": [result_lists[1]],  # provider_name
                                "topic": result_lists[2],  # topic
                                "media": result_lists[3],  # media
                                "subject": result_lists[4],  # subject
                                "describe": result_lists[5],  # describe
                                "art": result_lists[6]  # art
                            }
                        )
                        # Save DataFrame to a CSV file
                        csv_file_path = f'{basepath}_{provider_name}_automatic1111.csv'
                        df.to_csv(csv_file_path, index=False)

                # Write all_prompts to a TXT file with zero-padded index numbers
                with open(prompts_file_path, "w", encoding='utf-8') as f:
                    for prompt in all_prompts:
                        # Calculate the zero-padding for the index number based on the maximum line number
                        f.write(f"[{str(i).zfill(max_line_number)}] {prompt}\n")

                # return prompts_file_path

                # Combine csv files in art_prompts directory
                combined_csv_path = csv_dir.parent / 'art_prompts.csv'
                combine_csv_files(directory=csv_dir, output_path=combined_csv_path)

            else:
                print('Error occurred while generating chat response')
                with open(prompts_file_path, "w", encoding='utf-8') as f:
                    f.write(f"[{str(i).zfill(max_line_number)}]\n")
                # return

        return Path(csv_dir)

    def generate_images_from_csv(self, csv_dir: Path, output_dir: Path = None) -> Path:
        # Scan csv_dir for csv files
        csv_files = csv_dir.glob('*.csv')

        # Loop through the csv files
        for csv_file in csv_files:
            # Assign 'basename' as the first part of the filename divided by "_"
            basename = csv_file.stem.split('_')[0]

            # Read the csv file using pandas
            df = pd.read_csv(csv_file)

            # Process each row in the DataFrame
            for _, row in df.iterrows():
                # Assign 'prompt' as a joined string of values for 4 columns: media, subject, describe, art
                prompt = ','.join(str(item) for item in row[['media', 'subject', 'describe', 'art']])

                output_dir = output_dir or csv_dir
                # Assign 'output_path' as basename + '_' + value of column 'provider_name' + '.png'
                output_path = output_dir / f"{basename}_{row['provider_name']}.png"

                print('+-----------------------------------------------------------------------------+')
                print(f'Generating image with prompt: {prompt}')
                print()
                print(f'Saving image to: {output_path}')
                self.image_generator.generate_image_from_text(prompt=prompt, output_path=output_path)
                print(f'Image saved successfully to {output_path}')
                print()

        return Path(output_dir)

    def generate_talking_head_video(self, line: str, thumbnail_line: str, image_file: Path):
        self.video_generator.set_vidgen_provider('d-id')

        # region Step 1: GENERATE AUDIO
        # ------------------------------------
        script_folder = Path(create_script_folder(text=line,
                                                  parent_dir=image_file.parent,
                                                  folder_name=image_file.stem))

        # Save 'line' and 'thumbnail_line' as text files
        (script_folder / f'line_{image_file.stem}.txt').write_text(line, encoding='utf-8')
        (script_folder / f'thumbnail_line_{image_file.stem}.txt').write_text(thumbnail_line, encoding='utf-8')

        audio_files = []
        self.tts_generator.set_tts_provider(os.environ.get('TTS_PROVIDER'))
        script_file = script_folder / 'script.txt'
        # output_dir = script_folder.parent
        tts_file = None

        if script_file.is_file():
            audio_file = Path(script_folder / f'{script_folder.name}.wav')
            if not audio_file.is_file():
                print(f'Generating audio... {line}')
                audio_files = self.tts_generator.generate_audios_from_txt(
                                                                    input_file=script_file,
                                                                    output_dir=script_folder)
                self.audio_editor.input_audio_files = audio_files
                tts_file = self.audio_editor.merge_audios_with_padding(
                                                output_dir=script_folder,
                                                name=script_folder.name)
            else:
                print(f'{audio_file} already exists. Skipping...')
                tts_file = audio_file
        # endregion

        # region Step 2: GENERATE D-ID VIDEO
        # ------------------------------------
        d_id_video = Path(script_folder / (image_file.stem + '_d_id.mp4'))

        # Check if the Text-to-Speech (TTS) file exists
        if tts_file.is_file():
            # Check if the D-ID video file does not exist
            if not d_id_video.is_file():
                print('Generating D-ID video...')
                # Get the D-ID Basic API tokens from environment variables
                keys = os.environ.get('D-ID_BASIC_TOKENS')
                # Rotate API keys to ensure a valid key is used for the video generation process
                self.video_generator.rotate_key(keys=keys)
                try:
                    # Create the D-ID talk video using the image and audio from the specified files
                    id = self.video_generator.create_talk_video(image=str(image_file), audio=str(tts_file))
                except Exception as e:
                    # If an error occurs during video generation, print the error and rotate the API keys
                    print(str(e))
                    self.video_generator.rotate_key(keys=keys)
                # Retrieve the generated talk video from D-ID using the generated ID and save it
                self.video_generator.get_talk(id=id, output_path=d_id_video)
            else:
                print(f'"{d_id_video}" already exists. Skipping...')
        else:
            print(f'"{tts_file}" doesn\'t exists. Exiting...')
            return
        # endregion

        # region Step 3: REMOVE D-ID WATERMARK
        # ------------------------------------
        no_watermark_video = Path(script_folder / (image_file.stem + '_no_watermark.mp4'))

        if d_id_video.is_file():
            if not no_watermark_video.is_file():
                print('Removing watermark in D-ID video...')
                self.video_editor.input_video = str(d_id_video)
                no_watermark_video = Path(self.video_editor.remove_d_id_watermark(
                                                    input_image=str(image_file)))
            else:
                print(f'"{no_watermark_video}" already exists. Skipping...')
        else:
            print(f'"{d_id_video}" doesn\'t exists. Exiting...')
            return
        # endregion

        # region Step 4: ADD SUBTITLE
        # ------------------------------------
        subtitled_video = Path(script_folder / (image_file.stem + '_no_watermark_subtitled.mp4'))

        if no_watermark_video.is_file():
            if not subtitled_video.is_file():
                print('Generating subtitle...')
                subtitle_file = self.subtitle_generator.generate_subtitle(input_video=no_watermark_video)
                modified_subtitle_file = self.subtitle_generator.modify_subtitle(subtitle_file)
                subtitled_video = Path(self.subtitle_generator.burn_subtitle(
                                    input_video=no_watermark_video,
                                    subtitle_file=modified_subtitle_file))
            else:
                print(f'"{subtitled_video}" already exists. Skipping...')
        else:
            print("Video with watermark removed doesn't exists. Exiting...")
            return
        # endregion

        # region Step 5: EDIT
        # ------------------------------------
        if subtitled_video.is_file():
            # Add music
            print('Adding music...')
            self.video_editor.input_video = subtitled_video
            merged_video = Path(self.video_editor.merge_audio_files_with_fading_effects())

            # Add watermark text
            print('Adding watermark text...')
            if merged_video.is_file():
                self.video_editor.input_video = merged_video
                self.video_editor.add_watermark_text()
            else:
                print("Video with added music doesn't exists. Exiting...")
                return
        else:
            print("Video with added subtitle doesn't exists. Exiting...")
            return
        # endregion

        # region Step 6: ADD THUMBNAIL
        # ------------------------------------
        thumbnail_line = process_text(thumbnail_line)[1]

        if no_watermark_video.is_file():
            first_frame = self.thumbnail_generator.extract_first_frame(video_file=no_watermark_video)
            thumbnail_image = Path(self.thumbnail_generator.generate_thumbnail_image(
                input_filename=first_frame.name.split('_')[0],
                input_image_path=first_frame,
                text=thumbnail_line))
            if thumbnail_image.is_file():
                print('Generating video with thumbnail...')
                thumbnail_video = Path(self.thumbnail_generator.generate_thumbnail_video(
                                                    thumbnail_image_name=thumbnail_image.name))
                if thumbnail_video.is_file():
                    final_video = Path(script_folder.parent / (f'{image_file.stem}.mp4'))
                    shutil.copy(thumbnail_video, final_video)
                    print(f'\033[92mFinal video with thumbnail saved to "{final_video}"\033[0m')
                    print()
            else:
                print("Thumbnail image doesn't exists. Exiting...")
                return
        else:
            print("Video with watermark removed doesn't exists. Exiting...")
            return
        # endregion

    def generate_multiple_talking_head_videos(self, input_dir: Path):
        self.video_generator.set_vidgen_provider('d-id')

        lines_file = input_dir / "lines.txt"
        thumbnail_lines_file = input_dir / "thumbnail_lines.txt"

        # if self.check_talking_head_videos_resources(lines_file, thumbnail_lines_file, input_dir):
        lines_list = read_lines(lines_file)
        thumbnail_lines_list = read_lines(thumbnail_lines_file)

        lines_first_parts = [process_text(line)[0] for line in lines_list]
        thumbnail_first_parts = [process_text(thumbnail_line)[0] for thumbnail_line in thumbnail_lines_list]

        for line, thumbnail_line, line_first_part, thumbnail_first_part in zip(
            lines_list,
            thumbnail_lines_list,
            lines_first_parts,
            thumbnail_first_parts
        ):
            thumbnail_line_outside_text = process_text(thumbnail_line)[1]

            # List of PNG files that start with line_first_part and end with .png in input_dir.
            png_files = list(input_dir.glob(f"{line_first_part}*.png"))

            for png_file in png_files:
                if line_first_part == thumbnail_first_part and png_file.is_file():
                    self.generate_talking_head_video(line=line,
                                                     thumbnail_line=thumbnail_line_outside_text,
                                                     image_file=png_file)

    def generate_talking_head_conversation_video(self, input_file: Path, images_dir: Path):
        self.video_generator.set_vidgen_provider('d-id')

        # region Step 1: VALIDATE
        # ------------------------------------
        conversation_lines_list = read_lines(input_file)

        unique_speakers = set()  # Set to store unique speakers
        speakers_list = []  # List to store the speakers for later use
        for conversation_line in conversation_lines_list:
            speaker, _, _ = process_text(conversation_line)
            unique_speakers.add(speaker)  # Add the speaker to the set of unique speakers
            speakers_list.append(speaker)  # Save the speaker to the speakers_list

        # Convert the set of unique speakers back to a list
        unique_speakers_list = list(unique_speakers)

        # Check if image_dir contains all items in unique_speakers_list along with the ".png" extension
        for speaker in unique_speakers_list:
            image_file = images_dir / (f'{speaker}.png')
            if not image_file.is_file():
                print(f'"{speaker}.png" not found. Exiting...')
                return

        conversation_dir = Path(input_file.parent / input_file.stem)
        conversation_dir.mkdir(exist_ok=True)
        # endregion

        # region Step 2: GENERATE
        # ------------------------------------
        # Generate audios
        max_line_number = len(str(len(conversation_lines_list)))
        subtitled_videos = []  # For later use
        for i, conversation_line in enumerate(conversation_lines_list, start=1):
            speaker, line, _ = process_text(conversation_line)
            script_folder = Path(create_script_folder(
                                text=conversation_line,
                                parent_dir=conversation_dir,
                                folder_name=str(i).zfill(max_line_number)))
            audio_files = []
            self.tts_generator.set_tts_provider(os.environ.get('TTS_PROVIDER'))
            script_file = script_folder / 'script.txt'
            tts_file = None

            if script_file.is_file():
                audio_file = Path(script_folder.parent, f'{script_folder.name}.wav')
                if not audio_file.is_file():
                    print(f'Generating audio... {[speaker]} {line}')
                    audio_files = self.tts_generator.generate_audios_from_txt(
                                                                        input_file=script_file,
                                                                        output_dir=script_folder)
                    self.audio_editor.input_audio_files = audio_files
                    tts_file = self.audio_editor.merge_audios_with_padding(
                                                    output_dir=conversation_dir,
                                                    name=script_folder.name)
                else:
                    print(f'"{audio_file}" already exists. Skipping...')
                    tts_file = audio_file

            # Generate D-ID videos
            d_id_video = Path(conversation_dir / (script_folder.name + '_d_id.mp4'))

            if tts_file:
                if not d_id_video.is_file():
                    image_file = images_dir / (f'{speakers_list[i-1]}.png')
                    print('Generating D-ID video...')
                    keys = os.environ.get('D-ID_BASIC_TOKENS')
                    self.video_generator.rotate_key(keys=keys)
                    id = self.video_generator.create_talk_video(image=str(image_file), audio=str(tts_file))
                    self.video_generator.get_talk(id=id, output_path=d_id_video)
                else:
                    print(f'"{d_id_video}" already exists. Skipping...')
            else:
                print(f'"{tts_file}" doesn\'t exists. Exiting...')
                return

            # Remove D-ID watermarks
            if d_id_video.is_file():
                no_watermark_file = Path(conversation_dir / (script_folder.name + '_no_watermark.mp4'))
                if not no_watermark_file.is_file():
                    print('Removing watermark in D-ID video...')
                    self.video_editor.input_video = str(d_id_video)
                    no_watermark_file = Path(self.video_editor.remove_d_id_watermark(
                                                    input_image=str(image_file)))
                else:
                    print(f'"{no_watermark_file}" already exists. Skipping...')
            else:
                print(f'"{d_id_video}" doesn\'t exists. Exiting...')
                return

            # Add subtitles
            subtitled_video = Path(conversation_dir / (script_folder.name + '_no_watermark_subtitled.mp4'))
            subtitle_file = Path(conversation_dir / (script_folder.name + '_no_watermark.ass'))
            modified_subtitle_file = Path(conversation_dir / (script_folder.name + '_no_watermark_modified.ass'))
            if no_watermark_file.is_file():
                if not subtitled_video.is_file():
                    if not subtitle_file.is_file():
                        print('Generating subtitle...')
                        subtitle_file = self.subtitle_generator.generate_subtitle(input_video=no_watermark_file)
                    if not modified_subtitle_file.is_file():
                        modified_subtitle_file = self.subtitle_generator.modify_subtitle(subtitle_file)
                    subtitled_video = Path(self.subtitle_generator.burn_subtitle(
                                        input_video=no_watermark_file,
                                        subtitle_file=modified_subtitle_file))
                else:
                    print(f'"{subtitled_video}" already exists. Skipping...')
            else:
                print("Video with watermark removed doesn't exists. Exiting...")
                return

            if subtitled_video.is_file():
                subtitled_videos.append(subtitled_video)
        # endregion

        # region Step 3: EDIT
        # ------------------------------------
        # Join subtitled videos
        if len(conversation_lines_list) == len(subtitled_videos):
            joined_video = conversation_dir / f"{script_folder.name}_joined.mp4"
            self.video_editor.join_videos(input_videos=subtitled_videos, output_filepath=joined_video)

            if joined_video.is_file():
                # Add music
                print('Adding music...')
                self.video_editor.input_video = joined_video
                merged_video = Path(self.video_editor.merge_audio_files_with_fading_effects(
                                    basename=input_file.stem))

                # Add watermark text
                print('Adding watermark text...')
                if merged_video.is_file():
                    self.video_editor.input_video = merged_video
                    self.video_editor.add_watermark_text(basename=input_file.stem)
                else:
                    print("Video with added music doesn't exists. Exiting...")
                    return
            else:
                print("Joined video doesn't exists. Exiting...")
                return
        else:
            print("Number of lines doesn't match number of subtitled videos. Exiting...")
            return

        # Add thumbnail
        first_no_watermark_file = Path(conversation_dir / (f'{str(1).zfill(max_line_number)}_no_watermark.mp4'))
        if first_no_watermark_file.is_file():
            first_frame = self.thumbnail_generator.extract_first_frame(video_file=first_no_watermark_file)
            thumbnail_image = Path(self.thumbnail_generator.generate_thumbnail_image(
                input_filename=input_file.stem,
                input_image_path=first_frame,
                text=input_file.stem))
            if thumbnail_image.is_file():
                print('Generating video with thumbnail...')
                thumbnail_video = Path(self.thumbnail_generator.generate_thumbnail_video(
                                                    thumbnail_image_name=thumbnail_image.name))
                if thumbnail_video.is_file():
                    final_video = Path(conversation_dir.parent / (f'{input_file.stem}.mp4'))
                    shutil.copy(thumbnail_video, final_video)
                    print(f'\033[92mFinal video with thumbnail saved to "{final_video}"\033[0m')
                    print()
            else:
                print("Thumbnail image doesn't exists. Exiting...")
                return
        else:
            print("First video with watermark removed doesn't exists. Exiting...")
            return
        # endregion

    @staticmethod
    def enhance_videos_with_ai(videos_dir: Path, encoder: str):
        # Set the working directory from the environment variable
        working_directory = os.getenv('TVAI_WORKING_DIR')

        try:
            # Process all mp4 and mov files in the directory
            for video_file in videos_dir.glob('*.[Mm][Pp][4Oo]'):

                # Split the filename by '_' and take the first part
                basename = video_file.stem.split('_')[0]
                output_h264_path = videos_dir / 'enhanced' / f'{basename}.mp4'

                if not output_h264_path.is_file():
                    with temp_working_directory(working_directory):
                        # Call the enhanced_video_with_ai function (decorated with delay_decorator)
                        output_path = enhance_video_with_ai(input_video=video_file, encoder=encoder)

                    if output_path.is_file():
                        print(f'Converting the video to H.264 codec... "{output_h264_path}"')
                        cmd_h264 = f'ffmpeg -i "{output_path}" -c:v libx264 -crf 23 -c:a aac -b:a 128k "{output_h264_path}"'  # noqa
                        # Run the ffmpeg command and suppress output
                        subprocess.run(cmd_h264, shell=True, check=True,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        # Delete the original enhanced video file (output_path)
                        os.remove(output_path)

                        print('\033[92m' + f'Final enhanced video saved to "{output_h264_path}"' + '\033[0m')
                else:
                    print(f'{output_h264_path} already exists. Skipping...')

        except subprocess.CalledProcessError as e:
            print("Command failed:", e)

    def generate_video_from_image(self, image_file: Path, output_dir=None, output_path=None, seed=None):
        self.video_generator.set_vidgen_provider('gen-2')

        print('Generating Gen-2 video...')
        # Get the Gen-2 Bearer API tokens from environment variables
        keys = os.environ.get('GEN_2_BEARER_TOKENS')
        # Rotate API keys to ensure a valid key is used for the video generation process
        try:
            username, _, _, _ = self.video_generator.rotate_key(keys=keys)
        except LastKeyReachedException:
            raise  # Re-raise the exception to propagate it

        if not username:
            print("Username is missing or empty. Aborting...")
            return
        # Upload the image and get the upload URLs
        upload_url, preview_upload_url = self.video_generator.upload_image(image_file)
        if not upload_url:
            print("Upload URL is missing or empty. Aborting...")
            return
        if not preview_upload_url:
            print("Preview Upload URL is missing or empty. Aborting...")
            return

        # Generate the video
        return self.video_generator.generate_video_from_image(image_file, username, upload_url, preview_upload_url,
                                                              output_dir, output_path, seed)

    def generate_multiple_ai_videos_from_images(self, images_dir: Path):
        self.video_generator.set_vidgen_provider('gen-2')
        error_occurred = False  # Flag to track if an error occurred

        def check_exception(future):
            nonlocal error_occurred  # To access the flag variable defined in the outer function
            if future.exception() is not None and isinstance(future.exception(), LastKeyReachedException):
                error_occurred = True

        def process_single_image(png_file):
            with ThreadPoolExecutor() as inner_executor:
                nonlocal error_occurred  # To access the flag variable defined in the outer function
                futures = []
                for repeat_index in range(1, num_repeats + 1):
                    print(f"Repeat: {repeat_index}/{num_repeats}")
                    future = inner_executor.submit(self.generate_video_from_image, png_file)
                    futures.append(future)

                # Check for exceptions
                for future in as_completed(futures):
                    check_exception(future)
                    if error_occurred:
                        break

        png_files = list(images_dir.glob("*.png"))
        if not png_files:
            print("No PNG files found in the folder.")
            return

        while True:
            try:
                num_repeats = int(input("Enter the number of times to process each image: "))
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

        if num_repeats == 1:
            while True:
                try:
                    images_at_a_time = int(input("Enter the number of images to process at a time: "))
                    if images_at_a_time <= 0:
                        print("Please enter a positive integer.")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")

            with ThreadPoolExecutor() as executor:
                futures = []
                for png_index, png_file in enumerate(png_files, start=1):
                    if error_occurred:  # Check if an error occurred before processing the image
                        break  # Exit the loop if error_occurred is True

                    print(f"\nProcessing: {png_file.name} (File {png_index}/{len(png_files)})")
                    future = executor.submit(process_single_image, png_file)
                    futures.append(future)

                    if png_index % images_at_a_time == 0:
                        for future in futures:
                            future.result()
                        futures = []

                    if error_occurred:  # Check if an error occurred before processing the image
                        break  # Exit the loop if error_occurred is True

                # Wait for any remaining tasks to complete
                for future in futures:
                    future.result()

        else:
            with ThreadPoolExecutor() as executor:
                for png_index, png_file in enumerate(png_files, start=1):
                    if error_occurred:  # Check if an error occurred before processing the image
                        break  # Exit the loop if error_occurred is True

                    print(f"\nProcessing: {png_file.name} (File {png_index}/{len(png_files)})")
                    process_single_image(png_file)

        if error_occurred:
            return

    def generate_single_ai_video_from_image(self, image_file: Path, num_videos_to_generate: int, keep_same_seed: bool):
        self.video_generator.set_vidgen_provider('gen-2')

        seed = self.video_generator.generate_random_seed()
        init_video_file = self.generate_video_from_image(image_file=image_file, seed=seed)
        input_videos = [str(init_video_file)]

        if num_videos_to_generate > 1:
            last_frame = init_video_file.with_name(f'{init_video_file.stem}_iteration_1_last_frame.png')
            last_frame = self.video_editor.extract_last_frame(video_file=init_video_file, output_path=last_frame)
            for i in range(2, num_videos_to_generate + 1):
                if not keep_same_seed:
                    seed = self.video_generator.generate_random_seed()
                video_file_name = f'{image_file.stem}_{seed}_iteration_{i}.mp4'
                video_file = init_video_file.with_name(video_file_name)
                self.generate_video_from_image(image_file=last_frame, seed=seed, output_path=video_file)

                input_videos.append(str(video_file))
                Path(last_frame).unlink()

                # Check if it's the final iteration
                if i == num_videos_to_generate:
                    break

                last_frame_name = f"{image_file.stem}_{seed}_iteration_{i}_last_frame.png"
                last_frame = init_video_file.with_name(last_frame_name)
                self.video_editor.extract_last_frame(video_file=video_file, output_path=last_frame)

            # Determine the base filename
            base_filename = f'{init_video_file.stem}_joined_{num_videos_to_generate}_iterations.mp4'
            # Update the base filename if keep_same_seed is False
            if not keep_same_seed:
                base_filename = f'{image_file.stem}_joined_{num_videos_to_generate}_iterations.mp4'
            # Generate the output_filepath using the base filename
            output_filepath = init_video_file.with_name(str(base_filename))
            print('\nJoining the videos...')
            joined_video = self.video_editor.join_videos_without_audio(input_videos=input_videos,
                                                                       output_filepath=output_filepath)
            print('\033[92m' + f'Videos successfully joined and saved to "{joined_video}"' + '\033[0m')
