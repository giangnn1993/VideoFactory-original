import subprocess
from pathlib import Path
from typing import List


class AudioEditor:
    def __init__(self, input_audio_file: Path = None, input_audio_files: List[Path] = None):
        self.input_audio_file = input_audio_file
        self.input_audio_files = input_audio_files

    @staticmethod
    def run_command(command):
        # Run the command with subprocess, using shell mode to execute the command as a string.
        # Set check=True to raise an exception if the command returns a non-zero exit code.
        # Redirect the standard output (stdout) and standard error (stderr) to /dev/null to suppress any output.
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")

    def merge_audios_with_padding(self, output_dir: Path, name: str = None,
                                  begin_end_delay: int = 500, between_delay: int = 1000) -> Path:
        # If the 'name' argument is not provided, set it to None
        name = name or output_dir.name
        # Create the base path by combining the 'output_dir' and the 'name'
        basepath = output_dir / name
        # Create the output path for the audio file
        output_path = f'{basepath}.wav'

        # Create the filter complex argument
        filter_complex_args = []
        for i, audio_file in enumerate(self.input_audio_files):
            if i == 0:
                filter_complex_args.append(f"[{i}:a]adelay={begin_end_delay}|{begin_end_delay}[a{i}];")
            else:
                filter_complex_args.append(f"[{i}:a]adelay={between_delay}|{between_delay}[a{i}];")

        # Append the concat argument to the filter complex argument
        filter_complex_args.append("[{}]concat=n={}:v=0:a=1[out]".format(']['.join(
                                    ['a'+str(i) for i in range(len(self.input_audio_files))]),
                                    len(self.input_audio_files)))
        filter_complex_arg = ''.join(filter_complex_args)

        # Create the input arguments
        input_args = []
        for audio_file in self.input_audio_files:
            input_args.append(f"-i \"{audio_file}\"")
        input_arg = ' '.join(input_args)

        # Create the command
        # command = f"ffmpeg {input_arg} -filter_complex \"{filter_complex_arg}\" -map \"[out]\" \"{output}.wav\""
        command = (
                    f'ffmpeg {input_arg} -filter_complex \"{filter_complex_arg}\" '
                    f'-map \"[out]\" \"{basepath}_temp.wav\" -y && '
                    f'ffmpeg -i \"{basepath}_temp.wav\" -af apad=pad_dur={begin_end_delay / 1000.0:.1f}s '
                    f'\"{output_path}\" -y && '
                    f'del \"{basepath}_temp.wav\"'
                )

        # Execute the command
        # print(command)
        self.run_command(command)
        print(f'Audio saved successfully to {output_path}')

        return Path(output_path)


# # USAGE
# # ------------------------------------

# # Usage #1:
# # To use the AudioEditor class, create an instance:
# audio_editor = AudioEditor()
# audio_editor.input_audio_files
# audios_dir = r'VideoFactory\data\output\processed\Something'
# wav_files = list(Path(audios_dir).glob('*.wav'))
# audio_editor.input_audio_files = wav_files
# audio_editor.merge_audios_with_padding(audios_dir=Path(audios_dir))
