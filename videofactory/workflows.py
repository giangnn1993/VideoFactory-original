import os
from pathlib import Path

from generators.text_generator import TextGenerator
from generators.image_generator import ImageGenerator
from generators.tts_generator import TTSGenerator
from generators.video_generator import VideoGenerator


class WorkflowManager:
    def __init__(self):
        self.text_generator = TextGenerator('g4f')  # Initialize ImageGenerator object
        self.image_generator = ImageGenerator('automatic1111')  # Initialize ImageGenerator object
        self.tts_generator = TTSGenerator('coqui', key='')  # Initialize TTSGenerator object
        self.video_generator = VideoGenerator('d-id', key='')  # Initialize VideoGenerator object
