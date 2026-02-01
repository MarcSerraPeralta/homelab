import os
import pathlib
import shutil
import argparse
import ffmpeg

parser = argparse.ArgumentParser(description="Transcode video files to HEVC.")
parser.add_argument(
    "input_root",
    type=pathlib.Path,
    help="Root folder containing videos to process"
)
parser.add_argument(
    "--delete",
    action="store_true",
    help="Delete original files after processing (default: no deletion)"
)
args = parser.parse_args()

DELETE_FILES = args.delete
input_root = args.input_root
output_root = input_root.parent / "hevc"


def get_codec(file_path: str | pathlib.Path) -> str:
    info = ffmpeg.probe(file_path)
    video_stream = next(
        s for s in info["streams"] 
        if s["codec_type"] == "video"
    )
    return video_stream["codec_name"]


for input_path, subdirs, files in os.walk(input_root):
    input_path = pathlib.Path(input_path)

    rel_dir = os.path.relpath(input_path, input_root)
    output_path = output_root / rel_dir
    output_path.mkdir(exist_ok=True, parents=True)

    for name in files:
        print(rel_dir, name, end=" ", flush=True)
        input_file = input_path / name
        output_file = output_path / name

        if output_file in os.listdir(output_path):
            print("FILE ALREADY TRANSCODED")
            continue

        if get_codec(input_file).lower() in ["hevc"]:
            if DELETE_FILES:
                print("MOVING FILE...")
                shutil.move(input_file, output_file)
            else:
                print("COPYING FILE...")
                shutil.copy(input_file, output_file)

            continue

        # transcode to HEVC / H.265 8bit
        print("TRANSCODING...")
        (
            ffmpeg
            .input(str(input_file))
            .output(
                str(output_file),
                vcodec="libx264",
                preset="medium",
                crf=20,
                pix_fmt="yuv420p",
                acodec="aac",
                audio_bitrate="192k"
            )
            .global_args("-hide_banner", "-loglevel", "quiet")
            .run()
        )

        if DELETE_FILES:
            os.remove(input_file)
