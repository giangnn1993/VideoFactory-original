import os


def read_lines(file_path):
    with open(file_path, 'r') as file:
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


def create_images_and_audios_list(basenames, images_dir, audios_dir):
    # Initialize an empty list to store the dictionaries
    result_list = []

    # Iterate through the wav_basenames list
    for basename in basenames:
        # Create a dictionary for each basename
        data_dict = {
            'image': os.path.join(images_dir, basename + '.png'),
            'audio': os.path.join(audios_dir, basename + '.wav')
        }

        # Append the dictionary to the result_list
        result_list.append(data_dict)

    return result_list


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
