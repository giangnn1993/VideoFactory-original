from pathlib import Path
from videofactory.workflows import WorkflowManager


def main():
    # Create an instance of WorkflowManager
    workflow_manager = WorkflowManager()
    # Call methods from the WorkflowManager class as needed

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


if __name__ == "__main__":
    main()
