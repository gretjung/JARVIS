import subprocess
import uuid

from pathlib import Path

import requests

from PIL import Image, ImageDraw

from config import (
    IMAGE_DIR,
    VIDEO_DIR,
    FFMPEG,
    COMFYUI_URL
)


def create_placeholder_image(
    prompt
):

    filename = (
        f"jarvis_"
        f"{uuid.uuid4().hex[:8]}"
        f".png"
    )

    output = (
        IMAGE_DIR /
        filename
    )


    image = Image.new(
        "RGB",
        (1024, 1024),
        "black"
    )


    draw = ImageDraw.Draw(
        image
    )


    draw.text(
        (50, 50),
        "JARVIS IMAGE ENGINE",
        fill="white"
    )


    draw.text(
        (50, 100),
        prompt[:180],
        fill="white"
    )


    image.save(
        output
    )


    return output


def make_video_from_image(
    image_path,
    seconds=8,
    fps=30
):

    image_path = Path(
        image_path
    )


    output = (
        VIDEO_DIR /
        f"jarvis_"
        f"{uuid.uuid4().hex[:8]}"
        f".mp4"
    )


    frames = int(
        seconds * fps
    )


    filter_complex = (

        "zoompan="

        "z='min(zoom+0.0008,1.06)':"

        "x='iw/2-(iw/zoom/2)':"

        "y='ih/2-(ih/zoom/2)':"

        f"d={frames}:"

        "s=1920x1080:"

        f"fps={fps},"

        "format=yuv420p"

    )


    subprocess.run(

        [

            FFMPEG,

            "-y",

            "-loop",
            "1",

            "-i",
            str(image_path),

            "-vf",
            filter_complex,

            "-t",
            str(seconds),

            "-r",
            str(fps),

            "-c:v",
            "libx264",

            "-pix_fmt",
            "yuv420p",

            str(output)

        ],

        check=True

    )


    return output


def comfyui_available():

    try:

        response = requests.get(

            f"{COMFYUI_URL}/system_stats",

            timeout=3

        )

        return response.ok

    except Exception:

        return False