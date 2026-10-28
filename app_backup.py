

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import subprocess
import tempfile
import textwrap
import os
from pathlib import Path

st.set_page_config(
    page_title="Puneet AI Studio",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Puneet AI Studio")
st.subheader("Create cinematic motivational Reels")

st.write("Turn your photographs and story into a vertical MP4 video.")

story = st.text_area(
    "1. Enter your story or narration",
    value=(
        "More than a century ago, Edwin C. Barnes arrived "
        "in Orange, New Jersey, with a dream."
    ),
    height=140
)

photos = st.file_uploader(
    "2. Upload photographs in story order",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

seconds = st.slider(
    "3. Seconds per photograph",
    min_value=3,
    max_value=15,
    value=6
)

zoom = st.slider(
    "4. Cinematic zoom strength",
    min_value=1.02,
    max_value=1.15,
    value=1.07,
    step=0.01
)

def get_font(size):
    font_path = r"C:\Windows\Fonts\georgia.ttf"

    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)

    return ImageFont.truetype(
        r"C:\Windows\Fonts\arial.ttf", size
    )

def create_caption(text, path):
    canvas = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    font = get_font(48)
    lines = textwrap.wrap(text, width=32)[:3]

    line_height = 64
    box_height = len(lines) * line_height + 40
    y = 1920 - box_height - 180

    draw.rounded_rectangle(
        (55, y, 1025, y + box_height),
        radius=25,
        fill=(0, 0, 0, 175)
    )

    y += 20

    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=font)
        width = bounds[2] - bounds[0]

        draw.text(
            ((1080 - width) // 2, y),
            line,
            font=font,
            fill="white"
        )

        y += line_height

    canvas.save(path)

def run_ffmpeg(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:])

if st.button("🎞️ Create my Reel", type="primary"):
    if not photos:
        st.error("Please upload at least one photograph.")
        st.stop()

    if not story.strip():
        st.error("Please enter your story.")
        st.stop()

    captions = [
        line.strip()
        for line in story.replace("\n", " ").split(".")
        if line.strip()
    ]

    while len(captions) < len(photos):
        captions.extend([""] * (len(photos) - len(captions)))

    captions = captions[:len(photos)]

    st.info("Rendering your video. Please wait...")

    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            clips = []

            fps = 30
            frames = seconds * fps
            zoom_step = (zoom - 1.0) / frames

            for i, photo in enumerate(photos):
                image = Image.open(photo).convert("RGB")
                iw, ih = image.size

                # Crop to a vertical 9:16 composition.
                if iw / ih > 9 / 16:
                    new_width = int(ih * 9 / 16)
                    left = (iw - new_width) // 2
                    image = image.crop(
                        (left, 0, left + new_width, ih)
                    )
                else:
                    new_height = int(iw * 16 / 9)
                    top = (ih - new_height) // 2
                    image = image.crop(
                        (0, top, iw, top + new_height)
                    )

                image = image.resize(
                    (1080, 1920),
                    Image.Resampling.LANCZOS
                )

                image_path = folder / f"photo_{i}.png"
                caption_path = folder / f"caption_{i}.png"
                clip_path = folder / f"scene_{i}.mp4"

                image.save(image_path)
                create_caption(captions[i], caption_path)

                video_filter = (
                    f"zoompan=z='min(zoom+{zoom_step:.8f},{zoom})':"
                    f"x='iw/2-(iw/zoom/2)':"
                    f"y='ih/2-(ih/zoom/2)':"
                    f"d={frames}:s=1080x1920:fps={fps},"
                    f"format=yuv420p"
                )

                command = [
                    ffmpeg, "-y",
                    "-loop", "1", "-i", str(image_path),
                    "-loop", "1", "-i", str(caption_path),
                    "-filter_complex",
                    f"[0:v]{video_filter}[base];"
                    f"[base][1:v]overlay=0:0:format=auto[v]",
                    "-map", "[v]",
                    "-t", str(seconds),
                    "-r", str(fps),
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    str(clip_path)
                ]

                run_ffmpeg(command)
                clips.append(clip_path)

            concat_file = folder / "clips.txt"
            concat_file.write_text(
                "".join(
                    f"file '{clip.as_posix()}'\n"
                    for clip in clips
                ),
                encoding="utf-8"
            )

            output = folder / "puneet_reel.mp4"

            run_ffmpeg([
                ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output)
            ])

            video_bytes = output.read_bytes()

        st.success("Your Reel has been created!")
        st.video(video_bytes)

        st.download_button(
            "⬇️ Download your Reel",
            data=video_bytes,
            file_name="puneet_reel.mp4",
            mime="video/mp4"
        )

    except Exception as error:
        st.error("Something went wrong while creating the video.")
        st.code(str(error))



# ==========================================
# NEW FEATURE: AUTOMATIC SCRIPT SCENE PLANNER
# ==========================================

import re

st.divider()
st.header("🎬 AI Script-to-Scene Planner")
st.write(
    "Turn your story into a scene-by-scene plan "
    "for cinematic video generation."
)

if st.button("Plan My Scenes", key="plan_scenes"):
    if not story or not story.strip():
        st.warning("Please enter your story in the narration box above.")
    else:
        # Split the story into sentences.
        sentences = re.split(r'(?<=[.!?])\s+', story.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        # Group sentences into short cinematic scenes.
        scene_size = 2
        scenes = [
            sentences[i:i + scene_size]
            for i in range(0, len(sentences), scene_size)
        ]

        st.session_state["planned_scenes"] = scenes

if "planned_scenes" in st.session_state:
    scenes = st.session_state["planned_scenes"]

    st.success(f"Your story has been divided into {len(scenes)} scenes.")

    for index, sentences_in_scene in enumerate(scenes, start=1):
        narration = " ".join(sentences_in_scene)

        with st.expander(f"Scene {index}", expanded=(index == 1)):
            st.markdown("**Narration**")
            st.write(narration)

            st.markdown("**Visual direction**")
            st.write(
                "Create a cinematic historical scene illustrating: "
                + narration
            )

            st.markdown("**Animation direction**")
            st.write(
                "Use natural subject movement, subtle camera motion, "
                "realistic lighting, and historically consistent details. "
                "Avoid distorted faces, hands, and objects."
            )

