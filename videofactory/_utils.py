import os
from pathlib import Path
from typing import List
import json


def read_lines(file_path):
    with open(file_path, 'r', encoding='utf8') as file:
        lines_list = file.readlines()
    return lines_list


def compare_lines_lists(list1, list2):
    if len(list1) != len(list2):
        return False
    return True


def get_basenames(dir_path, file_extension):
    files = [file for file in os.listdir(dir_path) if file.lower().endswith(file_extension)]
    basenames = [os.path.splitext(file)[0] for file in files]
    return basenames


def process_text(text):
    # Create a config object
    config = {}

    # Extracting the text enclosed in square brackets
    start_index = text.find("[") + 1
    end_index = text.find("]")
    bracket_text = text[start_index:end_index]

    # Splitting the bracket text by "|"
    items = bracket_text.split("|")

    first_part = items[0].strip()

    # Setting the rest of the items as environmental variables
    for item in items[1:]:
        key, value = item.split("=")
        config[key.strip()] = value.strip()

    outside_text = (text[:start_index-1] + text[end_index+1:]).strip()

    return first_part, outside_text, config


def create_images_and_audios_dict(basenames, images_dir, audios_dir):
    # Initialize an empty dictionary to store the data
    result_dict = {}

    # Iterate through the basenames list
    for basename in basenames:
        # Create a dictionary for each basename
        data_dict = {
            'image': os.path.join(images_dir, basename + '.png'),
            'audio': os.path.join(audios_dir, basename + '.wav')
        }

        # Add the data_dict to the result_dict with basename as the key
        result_dict[basename] = data_dict

    return result_dict


def create_script_folders(txt_file: str, split_lines=False, delimiter: str = '.') -> List[Path]:
    # Convert the input txt_file_path to a Path object
    txt_file = Path(txt_file)

    # Read the contents of the txt file
    with txt_file.open('r', encoding='utf8') as file:
        lines = file.readlines()

    # Find the maximum line number for zfill
    max_line_number = len(str(len(lines)))

    # List to store folder paths
    folder_paths = []

    # Process each line and create folders and files
    for i, line in enumerate(lines, start=1):
        line = line.strip()

        # Extract text inside and outside square brackets
        start_index = line.find("[") + 1
        end_index = line.find("]")
        text_inside_brackets = line[start_index:end_index]
        text_outside_brackets = (line[:start_index-1] + line[end_index+1:]).strip()

        # Create a folder for each line
        folder_name = f"{str(i).zfill(max_line_number)}"
        folder_path = txt_file.parent / txt_file.stem / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        # Append folder_path to the list
        folder_paths.append(folder_path)

        # Create the 'script.txt' file inside each folder
        script_file_path = folder_path / "script.txt"
        with script_file_path.open('w', encoding='utf8') as script_file:
            if split_lines:
                # Split text_outside_brackets by the delimiter and write to 'script.txt'
                count_non_empty_items = len([item for item in text_outside_brackets.split(delimiter) if item])
                for index, item in enumerate(text_outside_brackets.split(delimiter)):
                    # Only write to 'script.txt' if the item is not empty
                    if item:
                        # Write the item wrapped in square brackets and stripped
                        script_file.write(f'[{text_inside_brackets}]{item.strip()}')
                        # Add a new line character '\n' after each item, except for the last item
                        if index < count_non_empty_items - 1:
                            script_file.write('\n')
            else:
                # Write the entire line to 'script.txt'
                script_file.write(line)

    # Return the list of folder paths
    return folder_paths


def parse_response_quote(input_query: str, provider_name, json_data):
    try:
        # Parse the JSON data
        parsed_data = json.loads(json_data)

        # Check if the required fields are present in the JSON data
        required_fields = ["topic", "quotes"]
        for field in required_fields:
            if field not in parsed_data:
                print(f"Invalid JSON format: '{field}' field is required.")
                return

        # Check if the 'quotes' field is a list
        if not isinstance(parsed_data["quotes"], list):
            print("Invalid JSON format: 'quotes' field should be a list.")
            return

        # Access the values in the parsed JSON data
        topic = parsed_data["topic"]
        quotes = parsed_data["quotes"]

        topic_list = []
        quote_list = []
        short_list = []
        input_query_list = [input_query] * len(quotes)
        provider_name_list = [provider_name] * len(quotes)

        for quote in quotes:
            # Check if the required keys ('quote' and 'short') are present in each quote dictionary
            required_quote_keys = ["quote", "short"]
            for quote_key in required_quote_keys:
                if quote_key not in quote:
                    print(f"Invalid JSON format: '{quote_key}' key is missing in a quote.")
                    return

            topic_list.append(topic)
            quote_list.append(quote["quote"])
            short_list.append(quote["short"])

        return input_query_list, provider_name_list, topic_list, quote_list, short_list

    except json.JSONDecodeError:
        print("Invalid JSON format: Unable to parse the provided JSON data.")
        return


def parse_response_image(input_query: str, provider_name, json_data):
    try:
        # Parse the JSON data
        parsed_data = json.loads(json_data)
        print(parsed_data)

        # Check if the required fields are present in the JSON data
        required_fields = ["topic", "prompt"]
        for field in required_fields:
            if field not in parsed_data:
                print(f"Invalid JSON format: '{field}' field is required.")
                return

        # Check if the 'prompt' field is a dictionary
        if not isinstance(parsed_data["prompt"], dict):
            print("Invalid JSON format: 'prompt' field should be a dictionary.")
            return

        # Access the values in the parsed JSON data
        topic = parsed_data["topic"]
        prompts = parsed_data["prompt"]

        # Check if all the keys
        # ('media', 'subject', 'describe', 'art')
        # are present in the 'prompt' dictionary
        required_prompt_keys = ["media", "subject", "describe", "art"]
        for prompt_key in required_prompt_keys:
            if prompt_key not in prompts:
                print(f"Invalid JSON format: '{prompt_key}' key is missing in 'prompt' dictionary.")
                return

        media = prompts["media"]
        subject = prompts["subject"]
        describe = prompts["describe"]
        art = prompts["art"]

        return input_query, provider_name, topic, media, subject, describe, art

    except json.JSONDecodeError:
        print("Invalid JSON format: Unable to parse the provided JSON data.")
        return
