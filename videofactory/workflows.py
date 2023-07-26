import os
from pathlib import Path
import pandas as pd
import shutil

from .generators.text_generator import TextGenerator
from .generators.image_generator import ImageGenerator
from .generators.tts_generator import TTSGenerator
from .generators.video_generator import VideoGenerator
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
    parse_response_image
)

from .editors.video_editor import VideoEditor
from .editors.audio_editor import AudioEditor


class WorkflowManager:
    def __init__(self):
        self.text_generator = TextGenerator('g4f')  # Initialize ImageGenerator object
        self.image_generator = ImageGenerator('automatic1111')  # Initialize ImageGenerator object
        self.tts_generator = TTSGenerator()  # Initialize TTSGenerator object
        self.video_generator = VideoGenerator('d-id')  # Initialize VideoGenerator object
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
                if script_file.exists():
                    # Create a Path object for the audio file with the same
                    # name as the'script_folder' but with the extension '.wav'
                    audio_file = Path(script_folder.parent, f'{script_folder.name}.wav')

                    # Check if the audio file does not exist
                    if not audio_file.exists():
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
            if Path(no_watermark_mp4_file).exists():
                first_frame = self.thumbnail_generator.extract_first_frame(video_file=no_watermark_mp4_file)
                self.thumbnail_generator.generate_thumbnail_image(
                    input_filename=first_frame.name.split('_')[0],
                    input_image_path=first_frame,
                    text=outside_text)

                self.thumbnail_generator.generate_thumbnail_videos()  # Generate thumbnail videos

        # endregion

    def generate_quotes(self, input_query=None):
        if input_query is None:
            input_query = input('Enter a query to generate quotes from: ').strip()

        # Then, call the generate_chat_responses function with a query:
        prompt = self.text_generator.create_few_shot_prompt_template(
            query=input_query,
            examples=self.text_generator.examples_quote,
            prefix=self.text_generator.prefix_quote
        )
        responses = self.text_generator.generate_chat_responses(query=prompt)
        # Iterate over the responses and print the response and provider name
        if responses is not None:
            # Lists to capture all quote_list and short_list values
            all_quotes = []
            all_shorts = []

            basepath = self.text_generator.processed_dir / f'{input_query}'
            for response, provider_name in responses:
                print('+-----------------------------------------------------------------------------+')
                print(f' User: {input_query} ')
                print(f' {provider_name}: ')

                result_lists = parse_response_quote(input_query, provider_name, json_data=response)

                # Append quote_list and short_list to the respective all_quotes and all_shorts lists
                all_quotes.extend(result_lists[3])  # quote_list
                all_shorts.extend(result_lists[4])  # short_list

                df = pd.DataFrame(
                    {
                        "input_query": result_lists[0],  # input_query_list
                        "provider_name": result_lists[1],  # provider_name_list
                        "topic": result_lists[2],  # topic_list
                        "quote": result_lists[3],  # quote_list
                        "short": result_lists[4]  # short_list
                    }
                )

                # Save DataFrame to a CSV file
                csv_file_path = f'{basepath}_{provider_name}.csv'
                df.to_csv(csv_file_path, index=False)

            # Write all_quotes to a TXT file with zero-padded index numbers
            quotes_file_path = f'{basepath}_quotes.txt'
            with open(quotes_file_path, "w", encoding='utf-8') as f:
                for i, quote in enumerate(all_quotes, start=1):
                    # Calculate the zero-padding for the index number based on the maximum line number
                    max_line_number = len(str(len(all_quotes)))
                    f.write(f"[{str(i).zfill(max_line_number)}] {quote}\n")

            # Write all_shorts to a TXT file with zero-padded index numbers
            shorts_file_path = f'{basepath}_shorts.txt'
            with open(shorts_file_path, "w", encoding='utf-8') as f:
                for i, short in enumerate(all_shorts, start=1):
                    # Calculate the zero-padding for the index number based on the maximum line number
                    max_line_number = len(str(len(all_shorts)))
                    f.write(f"[{str(i).zfill(max_line_number)}] {short}\n")

            return quotes_file_path, shorts_file_path

        else:
            print('Error occurred while generating chat response')
            return

    def generate_image_prompts_from_txt(self, input_file, output_dir=None):
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
            output_dir = Path(self.text_generator.processed_dir / Path(input_file).stem)
            # Create the output directory if it doesn't exist
            output_dir.mkdir(exist_ok=True)
            # Extract the first part of the quote using the process_text function
            first_part, _, _ = process_text(quote)
            # Create the base path for the prompts file within the output directory
            basepath = output_dir / first_part
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

            else:
                print('Error occurred while generating chat response')
                with open(prompts_file_path, "w", encoding='utf-8') as f:
                    f.write(f"[{str(i).zfill(max_line_number)}]\n")
                # return

        return output_dir

    def generate_images_from_csv(self, csv_dir):
        # Convert csv_dir to a Path object
        csv_dir = Path(csv_dir)

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
                prompt = ','.join(row[['media', 'subject', 'describe', 'art']])

                # Assign 'output_path' as basename + '_' + value of column 'provider_name' + '.png'
                output_path = csv_dir / f"{basename}_{row['provider_name']}.png"

                print('+-----------------------------------------------------------------------------+')
                print(f'Generating image with prompt: {prompt}')
                print()
                print(f'Saving image to: {output_path}')
                self.image_generator.generate_image_from_text(prompt=prompt, output_path=output_path)
                print(f'Image saved successfully to {output_path}')
                print()

        return csv_dir

    def generate_talking_head_video(self, line: str, thumbnail_line: str, image_file: Path):

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

        if script_file.exists():
            audio_file = Path(script_folder.parent, f'{script_folder.name}.wav')
            if not audio_file.exists():
                print(f'Generating audio... ({line})')
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

        if tts_file:
            if not d_id_video.exists():
                print('Generating D-ID video...')
                keys = os.environ.get('D-ID_BASIC_TOKENS')
                self.video_generator.rotate_key(keys=keys)
                id = self.video_generator.create_talk_video(image=str(image_file), audio=str(tts_file))
                self.video_generator.get_talk(id=id, output_path=d_id_video)
            else:
                print(f'{d_id_video} already exists. Skipping...')
        else:
            print(f"{tts_file} doesn't exists. Exiting...")
            return
        # endregion

        # region Step 3: REMOVE D-ID WATERMARK
        # ------------------------------------
        if d_id_video.exists():
            print('Removing watermark in D-ID video...')
            self.video_editor.input_video = str(d_id_video)
            no_watermark_file = Path(self.video_editor.remove_d_id_watermark(
                                                input_image=str(image_file)))
        else:
            print(f"{d_id_video} doesn't exists. Exiting...")
            return
        # endregion

        # region Step 4: ADD SUBTITLE
        # ------------------------------------
        subtitled_video = Path(script_folder / (image_file.stem + '_no_watermark_subtitled.mp4'))

        if no_watermark_file.exists():
            if not subtitled_video.exists():
                print('Generating subtitle...')
                subtitle_file = self.subtitle_generator.generate_subtitle(input_video=no_watermark_file)
                modified_subtitle_file = self.subtitle_generator.modify_subtitle(subtitle_file)
                subtitled_video = Path(self.subtitle_generator.burn_subtitle(
                                    input_video=no_watermark_file,
                                    subtitle_file=modified_subtitle_file))
            else:
                print(f'{subtitled_video} already exists. Skipping...')
        else:
            print("Video with watermark removed doesn't exists. Exiting...")
            return
        # endregion

        # region Step 5: EDIT
        # ------------------------------------
        if subtitled_video.exists():
            # Add music
            print('Adding music...')
            self.video_editor.input_video = subtitled_video
            merged_video = Path(self.video_editor.merge_audio_files_with_fading_effects())

            # Add watermark text
            print('Adding watermark text...')
            if merged_video.exists():
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
        if no_watermark_file.exists():
            first_frame = self.thumbnail_generator.extract_first_frame(video_file=no_watermark_file)
            thumbnail_image = Path(self.thumbnail_generator.generate_thumbnail_image(
                input_filename=first_frame.name.split('_')[0],
                input_image_path=first_frame,
                text=thumbnail_line))
            if thumbnail_image.exists():
                print('Generating video with thumbnail...')
                thumbnail_video = Path(self.thumbnail_generator.generate_thumbnail_video(
                                                    thumbnail_image_name=thumbnail_image.name))
                if thumbnail_video.exists():
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

    def generate_talking_head_conversation_video(self, input_file: Path, image_dir: Path):
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
            image_file = image_dir / (f'{speaker}.png')
            if not image_file.exists():
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

            if script_file.exists():
                audio_file = Path(script_folder.parent, f'{script_folder.name}.wav')
                if not audio_file.exists():
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
                if not d_id_video.exists():
                    image_file = image_dir / (f'{speakers_list[i-1]}.png')
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
            if d_id_video.exists():
                no_watermark_file = Path(conversation_dir / (script_folder.name + '_no_watermark.mp4'))
                if not no_watermark_file.exists():
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
            if no_watermark_file.exists():
                if not subtitled_video.exists():
                    print('Generating subtitle...')
                    subtitle_file = self.subtitle_generator.generate_subtitle(input_video=no_watermark_file)
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

            if joined_video.exists():
                # Add music
                print('Adding music...')
                self.video_editor.input_video = joined_video
                merged_video = Path(self.video_editor.merge_audio_files_with_fading_effects(
                                    basename=input_file.stem))

                # Add watermark text
                print('Adding watermark text...')
                if merged_video.exists():
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
        if first_no_watermark_file.exists():
            first_frame = self.thumbnail_generator.extract_first_frame(video_file=first_no_watermark_file)
            thumbnail_image = Path(self.thumbnail_generator.generate_thumbnail_image(
                input_filename=input_file.stem,
                input_image_path=first_frame,
                text=input_file.stem))
            if thumbnail_image.exists():
                print('Generating video with thumbnail...')
                thumbnail_video = Path(self.thumbnail_generator.generate_thumbnail_video(
                                                    thumbnail_image_name=thumbnail_image.name))
                if thumbnail_video.exists():
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
