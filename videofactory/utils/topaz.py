import os
import subprocess
import time
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def temp_working_directory(new_working_directory):
    original_working_directory = os.getcwd()
    os.chdir(new_working_directory)
    try:
        yield
    finally:
        os.chdir(original_working_directory)


def delay_decorator(i, seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if (wrapper.counter + 1) % i == 0:
                time.sleep(seconds)
            wrapper.counter += 1
            return result
        wrapper.counter = 0
        return wrapper
    return decorator


def _enhance_video_with_ai(input_video: Path, output_path: Path = None, vram: float = 0.75,
                           width: int = 1080, height: int = 1920, fps: int = 60, encoder: str = 'prores') -> Path:

    if output_path is None:
        # Split the filename by '_' and take the first part
        basename = input_video.stem.split('_')[0]
        # Use different file extensions based on the encoder
        if encoder == 'prores':  # ProRes 422 LT
            output_filename = basename + '_prores.mov'
        elif encoder == 'vp9':  # VP9 Best
            output_filename = basename + '_vp9.mp4'
        else:
            raise ValueError(f"Unsupported encoder: {encoder}")
        # Form the full output path by joining the output filename with the parent directory of the input video
        output_dir = Path(input_video.parent / 'enhanced')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / output_filename

    if not output_path.is_file():
        if encoder == 'prores':  # ProRes 422 LT
            cmd_topaz = (
                f'ffmpeg "-hide_banner" "-nostdin" "-y" "-nostats" "-i" "{str(input_video)}" "-sws_flags" "spline+accurate_rnd+full_chroma_int" '
                f'"-color_trc" "2" "-colorspace" "2" "-color_primaries" "2" "-filter_complex" "tvai_fi=model=chf-3:slowmo=1:rdt=0.01:'
                f'fps={fps}:device=0:vram=0.75:instances=0,tvai_up=model=prob-3:scale=0:w={width}:h={height}:preblur=0:noise=0:details=0:halo=0:'
                f'blur=0:compression=0:estimate=20:device=0:vram=0.75:instances=0,scale=w={width}:h={height}:flags=lanczos:threads=0" "-c:v" '
                f'"prores_ks" "-profile:v" "1" "-vendor" "apl0" "-quant_mat" "lt" "-bits_per_mb" "525" "-pix_fmt" "yuv422p10le" "-map_metadata" '
                f'"0" "-movflags" "use_metadata_tags+write_colr " "-map_metadata:s:v" "0:s:v" "-map_metadata:s:a" "0:s:a" "-c:a" "copy" "-metadata" '
                f'"videoai=Slowmo 100% and framerate changed to {fps} using chf-3 ignoring duplicate frames. Enhanced using prob-3 auto with recover details at 0, '
                f'dehalo at 0, reduce noise at 0, sharpen at 0, revert compression at 0, and anti-alias/deblur at 0. Changed resolution to {width}x{height}" "{output_path}"'
            )
        elif encoder == 'vp9':  # VP9 Best
            cmd_topaz = (
                f'ffmpeg "-hide_banner" "-nostdin" "-y" "-nostats" "-i" "{input_video}" "-sws_flags" '
                f'"spline+accurate_rnd+full_chroma_int" "-color_trc" "2" "-colorspace" "2" "-color_primaries" '
                f'"2" "-filter_complex" "tvai_fi=model=chf-3:slowmo=1:rdt=0.01:fps=60:device=0:vram={vram}:'
                f'instances=0,tvai_up=model=prob-3:scale=0:w={width}:h={height}:preblur=0:noise=0:details=0:'
                f'halo=0:blur=0:compression=0:estimate=20:device=0:vram={vram}:instances=0,scale=w={width}:h={height}:'
                f'flags=lanczos:threads=0" "-strict" "-2" "-c:v" "libvpx-vp9" "-pix_fmt" "yuv420p" "-row-mt" "1" '
                f'"-deadline" "best" "-b:v" "0" "-map_metadata" "0" "-movflags" "use_metadata_tags+write_colr " '
                f'"-map_metadata:s:v" "0:s:v" "-map_metadata:s:a" "0:s:a" "-c:a" "copy" "-metadata" "videoai='
                f'Slowmo 100% and framerate changed to 60 using chf-3 ignoring duplicate frames. Enhanced using '
                f'prob-3 auto with recover details at 0, dehalo at 0, reduce noise at 0, sharpen at 0, revert '
                f'compression at 0, and anti-alias/deblur at 0. Changed resolution to '
                f'{width}x{height}" "{output_path}"'
            )
        else:
            raise ValueError(f"Unsupported encoder: {encoder}")

        try:
            print()
            print(f'Enhancing video... "{input_video.name}"')
            print(f'Width: {width}, Height: {height}, FPS: {fps}')
            print(f'Output path: "{output_path}"')
            print('Please wait...')

            start_time = time.time()  # Record the start time

            subprocess.run(cmd_topaz, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            end_time = time.time()  # Record the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time

            print(f'"{input_video.name}" enhancement completed in {elapsed_time:.2f} seconds.')
            print(f'Output saved to: "{output_path}"')

        except subprocess.CalledProcessError as e:
            print("###################################################################################################")
            print(f"Command failed: {e}")
            print("###################################################################################################")

    else:
        print(f'{output_path} already exists. Skipping...')

    return Path(output_path)


# Decorate the function and export it with the original name
enhance_video_with_ai = delay_decorator(i=1, seconds=90)(_enhance_video_with_ai)
