from pathlib import Path
from videofactory.workflows import WorkflowManager


def generate_single_talking_head_video(workflow_manager: WorkflowManager):
    pass


def batch_generate_talking_head_videos(workflow_manager: WorkflowManager):
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
        generated_images_dir = workflow_manager.generate_images_from_csv(csv_dir)
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


def main():
    # Create an instance of WorkflowManager
    workflow_manager = WorkflowManager()
    # Call methods from the WorkflowManager class as needed

    print("Welcome to VideoFactory!")
    print("Choose a workflow option:")
    print("1. Generate single talking head video")
    print("2. Batch generate talking head videos")
    print()

    selected_option = int(input("Enter the number of the workflow option you want to execute: "))

    if selected_option == 1:
        print()
        print("\033[1;33m(Selected) 1. Generate single talking head video\033[0m")
        print('----------------------------------')
        print()
        generate_single_talking_head_video(workflow_manager)
    elif selected_option == 2:
        print()
        print("\033[1;33m(Selected) 2. Batch generate talking head videos\033[0m")
        print('----------------------------------')
        print()
        batch_generate_talking_head_videos(workflow_manager)
    else:
        print("Invalid option selected. Please try again.")
        return


if __name__ == "__main__":
    main()
