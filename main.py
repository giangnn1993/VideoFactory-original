import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

from videofactory.workflows import WorkflowManager

# Load environment variables from .env file
load_dotenv()


def generate_single_talking_head_video(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        line = input('Enter the text to generate TTS from: ')
        if line.strip():  # Check if the input is not empty or only whitespace
            break
        else:
            print("Invalid input. Please enter the text to generate TTS from.")

    while True:
        thumbnail_line = input('Enter the text to generate thumbnail from: ')
        if thumbnail_line.strip():  # Check if the input is not empty or only whitespace
            break
        else:
            print("Invalid input. Please enter the text to generate thumbnail from.")

    while True:
        image_file = Path(input('Enter the path to the image: ').strip('"'))
        if image_file.is_file():
            break
        else:
            print("Invalid file path. Please enter a valid path to the image.")

    workflow_manager.generate_talking_head_video(line, thumbnail_line, image_file)


def generate_multiple_talking_head_videos(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        input_dir = Path(input('Enter the path to the directory containing "lines.txt", "thumbnail_lines.txt," and matching PNG files: ').strip('"')) # noqa
        if input_dir.is_dir():
            break
        else:
            print("Invalid directory path. Please enter a valid path to the directory.")

    workflow_manager.generate_multiple_talking_head_videos(input_dir)


def _batch_generate_talking_head_videos(workflow_manager: WorkflowManager):
    # Call methods to batch generate talking head videos
    # Prompt User Inputs for Workflow Options
    generate_quotes = input('Do you want to generate quotes? (y/n): ').lower() == 'y'
    generate_images = input('Do you want to generate images? (y/n): ').lower() == 'y'
    generate_talking_head_videos = input('Do you want to generate talking head videos? (y/n): ').lower() == 'y'
    edit_talking_head_videos = input('Do you want to edit generated talking head videos? (y/n): ').lower() == 'y'
    print()

    # region Step #1: GENERATE QUOTES -> GENERATE IMAGE PROMPTS -> GENERATE IMAGES
    if generate_quotes:
        quotes_file_path, shorts_file_path = workflow_manager.generate_quotes()

    csv_dir = None
    generated_images_dir = None

    if generate_images:
        if not generate_quotes:
            quotes_file_path = Path(input('Enter the path to the quotes file to generate images from: '))
        csv_dir = workflow_manager.generate_image_prompts_from_txt(input_file=quotes_file_path)
        generated_images_dir = workflow_manager.generate_images_from_csv(csv_dir, output_dir=quotes_file_path.parent)
    # endregion

    # region Step #2: GENERATE TALKING HEAD VIDEOS -> EDIT TALKING HEAD VIDEOS
    output_dir = None

    if generate_talking_head_videos:
        if generate_quotes and input('Do you want to use generated lines? (y/n): ').lower() == 'y':
            lines_file = quotes_file_path
            thumbnail_lines_file = shorts_file_path
        else:
            lines_file = Path(input('Enter the path to the lines file: '))
            thumbnail_lines_file = Path(input('Enter the path to the thumbnail lines file: '))

        if generate_images and input('Do you want to use generated images? (y/n): ').lower() == 'y':
            images_dir = generated_images_dir
        else:
            images_dir = Path(input('Enter the directory containing the images: '))

        output_dir = workflow_manager.generate_talking_head_videos
        (lines_file, thumbnail_lines_file, images_dir)
    else:
        output_dir = lines_file.parent / lines_file.stem

    if edit_talking_head_videos:
        workflow_manager.edit_talking_head_videos(thumbnail_lines_file, images_dir, output_dir)
    # endregion


def generate_quotes_and_images(workflow_manager: WorkflowManager):
    # Prompt User Inputs for Workflow Options
    while True:
        input_query = input('Enter a query to generate quotes from: ')
        if input_query.strip():  # Check if the input is not empty or only whitespace
            break
        else:
            print("Invalid input. Please enter the text to generate quotes from.")

    # Step #1: GENERATE QUOTES -> GENERATE IMAGE PROMPTS -> GENERATE IMAGES
    quotes_file_path, _ = workflow_manager.generate_quotes(input_query=input_query)
    csv_dir = workflow_manager.generate_image_prompts_from_txt(input_file=quotes_file_path)
    generated_images_dir = workflow_manager.generate_images_from_csv(csv_dir, output_dir=quotes_file_path.parent)

    # Step #2: GENERATE TALKING HEAD VIDEOS
    generate_videos = input('Do you want to generate talking head videos using generated lines and images? (y/n): ').lower()  # noqa
    if generate_videos == 'y':
        input_dir = generated_images_dir
        workflow_manager.generate_multiple_talking_head_videos(input_dir)
    else:
        generate_multiple_talking_head_videos()


def generate_single_talking_head_conversation_video(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        text_file = Path(input('Enter the path to the text file to generate TTS from: ').strip('"'))
        if text_file.is_file():
            break
        else:
            print("Invalid file path. Please enter a valid path to the text file.")

    while True:
        images_dir = Path(input('Enter the path to the images directory: ').strip('"'))
        if images_dir.is_dir():
            break
        else:
            print("Invalid directory path. Please enter a valid path to the images directory.")

    workflow_manager.generate_talking_head_conversation_video(text_file, images_dir)


def enhance_videos_with_ai(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        videos_dir = Path(input('Enter the path to the videos directory: ').strip('"'))
        if videos_dir.is_dir():
            break
        else:
            print("Invalid directory path. Please enter a valid path to the videos directory.")

    # # Prompt for the encoder choice
    # encoder = None
    # while True:
    #     encoder_choice = input("Select the encoder (p for prores, v for vp9): ").strip().lower()
    #     if encoder_choice == 'p':
    #         encoder = 'prores'
    #         break
    #     elif encoder_choice == 'v':
    #         encoder = 'vp9'
    #         break
    #     else:
    #         print("Invalid encoder choice. Please select either 'prores' or 'vp9'.")

    workflow_manager.enhance_videos_with_ai(videos_dir, encoder='prores')


def set_env_variables(input_string):
    # Split the input string by '&' to separate individual commands
    commands = input_string.split('&')

    for command in commands:
        # Remove leading/trailing spaces
        command = command.strip()

        # Extract variable and value from the command
        if command.startswith("set "):
            assignment = command[4:].split('=', 1)
            if len(assignment) == 2:
                var = assignment[0].strip().strip('"')
                value = assignment[1].strip().strip('"')
                os.environ[var] = value
                print(f'Environment variable "{var}" set to "{value}".')

    print()


def _generate_single_ai_video_from_image(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        image_file = Path(input('Enter the path to the image: ').strip('"'))
        if image_file.is_file():
            break
        else:
            print("Invalid file path. Please enter a valid path to the image.")

    workflow_manager.generate_video_from_image(image_file)


def generate_single_ai_video_from_image(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        image_file = Path(input('Enter the path to the image: ').strip('"'))
        if image_file.is_file():
            break
        else:
            print("Invalid file path. Please enter a valid path to the image.")

    while True:
        try:
            num_videos_to_generate = int(input("Enter the number of videos to generate (4 seconds long each): "))
            if num_videos_to_generate > 0:
                break
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    while True:
        same_seed_input = input("Do you want to keep the same seed across videos? (y/n): ").lower()
        if same_seed_input in ['y', 'n']:
            keep_same_seed = True if same_seed_input == 'y' else False
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    workflow_manager.generate_single_ai_video_from_image(image_file, num_videos_to_generate, keep_same_seed)


def generate_multiple_ai_videos_from_images(workflow_manager: WorkflowManager):
    # Call methods to generate talking head video
    # Prompt User Inputs for Workflow Options
    while True:
        input_dir = Path(input('Enter the path to the directory containing PNG files: ').strip('"'))
        if input_dir.is_dir():
            break
        else:
            print("Invalid directory path. Please enter a valid path to the directory.")

    workflow_manager.generate_multiple_ai_videos_from_images(input_dir)


def main(selected_option=None):
    # Create an instance of WorkflowManager
    workflow_manager = WorkflowManager()

    print("Welcome to VideoFactory!")

    while True:

        if selected_option is None:
            while True:
                print()
                print("Choose a workflow option:")
                print("1. Generate single talking head video")
                print("2. Generate multiple talking head videos")
                print("3. Generate quotes and images")
                print("4. Generate single talking head conversation video")
                print("5. Enhance videos with AI")
                print("6. Set Environment Variables")
                print("7. Generate single AI video from image")
                print("8. Generate multiple AI videos from images")
                print("9. Exit")
                print()
                while True:
                    try:
                        selected_option = int(input("Enter the number of the workflow option you want to execute: "))
                        if 1 <= selected_option <= 9:
                            break
                        else:
                            print("\033[91m" + "Invalid input. Please enter a number between 1 and 9." + "\033[0m")
                    except ValueError:
                        print("\033[91m" + "Invalid input. Please enter a valid number." + "\033[0m")
                break
        else:
            selected_option = int(selected_option)
            if 1 <= selected_option <= 7:
                print()
                break

        # Call methods from the WorkflowManager class as needed
        if selected_option == 1:
            print()
            print("\033[1;33m(Selected) 1. Generate single talking head video\033[0m")
            print('----------------------------------')
            print()
            generate_single_talking_head_video(workflow_manager)
        elif selected_option == 2:
            print()
            print("\033[1;33m(Selected) 2. Generate multiple talking head videos\033[0m")
            print('----------------------------------')
            print()
            generate_multiple_talking_head_videos(workflow_manager)
        elif selected_option == 3:
            print()
            print("\033[1;33m(Selected) 3. Generate quotes and images\033[0m")
            print('----------------------------------')
            print()
            generate_quotes_and_images(workflow_manager)
        elif selected_option == 4:
            print()
            print("\033[1;33m(Selected) 4. Generate single talking head conversation video\033[0m")
            print('----------------------------------')
            print()
            generate_single_talking_head_conversation_video(workflow_manager)
        elif selected_option == 5:
            print()
            print("\033[1;33m(Selected) 5. Enhance videos with AI\033[0m")
            print('----------------------------------')
            print()
            enhance_videos_with_ai(workflow_manager)
        elif selected_option == 6:
            print("\033[1;33m(Selected) 6. Set Environment Variables\033[0m")
            print('----------------------------------')
            print()
            user_input = input("Enter environment variable assignments: ")
            set_env_variables(user_input)
            selected_option = None
        elif selected_option == 7:
            print()
            print("\033[1;33m(Selected) 7. Generate single AI video from image\033[0m")
            print('----------------------------------')
            print()
            generate_single_ai_video_from_image(workflow_manager)
        elif selected_option == 8:
            print()
            print("\033[1;33m(Selected) 8. Generate multiple AI videos from images\033[0m")
            print('----------------------------------')
            print()
            generate_multiple_ai_videos_from_images(workflow_manager)
        elif selected_option == 9:
            print("Exiting VideoFactory. Goodbye!")
            break
        else:
            print("\033[91m" + "Invalid option selected. Please try again." + "\033[0m")

        selected_option = None  # Reset selected_option after each iteration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VideoFactory workflow options.")
    parser.add_argument("--option", help="Select a workflow option (1-7).")
    args = parser.parse_args()

    main(args.option)
