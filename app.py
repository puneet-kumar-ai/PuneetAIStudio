

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
st.subheader("Create Cinematic Reels")

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



# --- LTX API connection check ---
st.divider()
st.header("🎬 LTX AI Video Generator")

ltx_api_key = st.secrets.get("LTX_API_KEY", "")

if ltx_api_key:
    st.success("LTX API key loaded successfully. Your key is hidden.")
else:
    st.error(
        "API key not found. Check .streamlit/secrets.toml "
        "and make sure the key is saved correctly."
    )


# --- LTX image-to-video controls ---
st.subheader("Generate a real AI video")

uploaded_image = st.file_uploader(
    "Upload one starting image",
    type=["png", "jpg", "jpeg"],
    key="ltx_starting_image",
)

motion_prompt = st.text_area(
    "Describe how the image should move",
    value=(
        "The steam locomotive slowly moves forward as thick white "
        "steam billows into the air. The camera gently tracks alongside "
        "the train. Preserve the original train and composition."
    ),
    key="ltx_motion_prompt",
)

ltx_duration = st.selectbox(
    "Video duration",
    options=[6, 8, 10],
    index=0,
    format_func=lambda seconds: f"{seconds} seconds",
    key="ltx_duration",
)


# --- LTX API helper functions ---
# These functions are only defined here.
# They do not run until explicitly called.


def upload_image_to_ltx(image_bytes, filename, mime_type, api_key):
    """Upload an image to LTX storage and return its storage URI."""
    import requests

    if not image_bytes:
        raise ValueError("The uploaded image is empty.")

    headers = {"Authorization": f"Bearer {api_key}"}

    upload_response = requests.post(
        "https://api.ltx.io/v1/upload",
        headers=headers,
        timeout=30,
    )
    upload_response.raise_for_status()

    upload_info = upload_response.json()

    required_fields = ("upload_url", "storage_uri")
    for field in required_fields:
        if not upload_info.get(field):
            raise ValueError(
                f"LTX upload response is missing '{field}'."
            )

    upload_headers = dict(
        upload_info.get("required_headers") or {}
    )
    upload_headers.setdefault(
        "Content-Type",
        mime_type or "application/octet-stream",
    )

    file_response = requests.put(
        upload_info["upload_url"],
        headers=upload_headers,
        data=image_bytes,
        timeout=120,
    )
    file_response.raise_for_status()

    return upload_info["storage_uri"]


def submit_ltx_video_job(image_uri, prompt, duration_seconds, api_key):
    """Submit an image-to-video job to LTX and return its job ID."""
    import requests

    if not image_uri:
        raise ValueError("The LTX image URI is missing.")

    if not prompt or not prompt.strip():
        raise ValueError("Please enter a motion prompt.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "image_uri": image_uri,
        "prompt": prompt.strip(),
        "model": "ltx-2-3-fast",
        "duration": duration_seconds,
        "resolution": "720x1280",
    }

    response = requests.post(
        "https://api.ltx.io/v2/image-to-video",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    job_data = response.json()
    job_id = job_data.get("id")

    if not job_id:
        raise ValueError(
            "LTX accepted no identifiable job ID. "
            "Review the API response before retrying."
        )

    return job_id


def get_ltx_video_status(job_id, api_key):
    """Check the status of an existing LTX video job."""
    import requests

    response = requests.get(
        f"https://api.ltx.io/v2/image-to-video/{job_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()

    return response.json()


def download_ltx_video(video_url):
    """Download a completed LTX video and return its bytes."""
    import requests

    response = requests.get(video_url, timeout=120)
    response.raise_for_status()

    video_bytes = response.content

    if not video_bytes:
        raise ValueError("The downloaded video file is empty.")

    return video_bytes




# --- LTX image-to-video workflow ---
if st.button(
    "🎬 AI video generation temporarily disabled",
    key="ltx_generate",
    disabled=True,
):
    if not ltx_api_key:
        st.error("Please configure your LTX API key first.")
    elif uploaded_image is None:
        st.warning("Please upload a starting image.")
    elif not motion_prompt.strip():
        st.warning("Please enter a motion prompt.")
    else:
        st.session_state["ltx_inputs_validated"] = True

if st.session_state.get("ltx_inputs_validated", False):
    st.success("Your image and motion prompt are ready.")

    confirm_paid_test = st.checkbox(
        "I understand that submitting an LTX job may use paid credits.",
        key="ltx_paid_confirmation",
    )

    if confirm_paid_test:
        st.warning(
            "The next button will contact LTX and may incur charges. "
            "Do not use it until you are ready to submit a real job."
        )


# --- Check LTX API access without generating a video ---
if st.button(
    "🔎 LTX API check temporarily disabled",
    key="ltx_check_api",
    disabled=True,
):
    if not ltx_api_key:
        st.error("LTX API key is missing.")
    else:
        try:
            import requests

            st.button(
                "AI video generation temporarily disabled",
                key="ltx_submit_paid",
                disabled=True,
            )
            if False:
                import time
                import requests

                try:
                    st.info("Uploading your image to LTX...")

                    image_uri = upload_image_to_ltx(
                        image_bytes=uploaded_image.getvalue(),
                        filename=uploaded_image.name,
                        mime_type=uploaded_image.type or "image/jpeg",
                        api_key=ltx_api_key,
                    )

                    st.info("Submitting your video-generation job...")

                    job_id = submit_ltx_video_job(
                        image_uri=image_uri,
                        prompt=motion_prompt.strip(),
                        duration_seconds=ltx_duration,
                        api_key=ltx_api_key,
                    )

                    st.success(f"LTX accepted the job. Job ID: {job_id}")

                    progress = st.progress(0)
                    status_message = st.empty()
                    deadline = time.monotonic() + 600
                    completed = False

                    for attempt in range(120):
                        time.sleep(5)

                        job_status = get_ltx_video_status(
                            job_id=job_id,
                            api_key=ltx_api_key,
                        )

                        status = str(
                            job_status.get("status", "unknown")
                        ).lower()

                        status_message.info(
                            f"Video status: {status}. "
                            "Please keep this page open."
                        )
                        progress.progress(min((attempt + 1) / 120, 1.0))

                        if status == "completed":
                            result = job_status.get("result") or {}
                            video_url = (
                                result.get("video_url")
                                if isinstance(result, dict)
                                else None
                            )

                            if not video_url:
                                video_url = job_status.get("video_url")

                            if not video_url:
                                st.error(
                                    "The job completed, but the response "
                                    "did not contain a video URL. "
                                    "Please inspect the returned job status."
                                )
                                st.json(job_status)
                                break

                            st.info("Downloading your completed video...")

                            video_bytes = download_ltx_video(video_url)

                            st.success("Your AI video is ready!")
                            st.video(video_bytes)

                            st.download_button(
                                "⬇️ Download AI Video",
                                data=video_bytes,
                                file_name="puneet_ai_video.mp4",
                                mime="video/mp4",
                                key="ltx_download_video",
                            )

                            completed = True
                            break

                        if status in ("failed", "error", "cancelled"):
                            st.error("LTX could not complete the video job.")
                            st.json(job_status)
                            break

                        if time.monotonic() >= deadline:
                            st.warning(
                                "The wait limit was reached. Your job may "
                                "still be processing. Check its status before "
                                "submitting another job."
                            )
                            break

                    if not completed and time.monotonic() < deadline:
                        if status not in ("failed", "error", "cancelled", "completed"):
                            st.info(
                                "The status checks have ended. "
                                "Check the job status before retrying."
                            )

                except requests.HTTPError as error:
                    status_code = (
                        error.response.status_code
                        if error.response is not None
                        else None
                    )

                    if status_code == 402:
                        st.error(
                            "LTX requires payment or credits. "
                            "No completed video was returned. "
                            "Check your billing page before retrying."
                        )
                    elif status_code == 401:
                        st.error(
                            "LTX rejected the API key. Check your saved secret."
                        )
                    else:
                        st.error(
                            f"LTX returned HTTP {status_code}. "
                            "Review the error before retrying."
                        )

                except requests.RequestException as error:
                    st.error(f"Network error while contacting LTX: {error}")

                except Exception as error:
                    st.error("Something went wrong in the LTX workflow.")
                    st.code(str(error))

            response = requests.post(
                "https://api.ltx.io/v1/upload",
                headers={
                    "Authorization": f"Bearer {ltx_api_key}"
                },
                timeout=20,
            )

            if response.status_code == 200:
                st.success(
                    "LTX accepted the API key and returned an upload URL. "
                    "No video generation was requested."
                )
            elif response.status_code == 401:
                st.error(
                    "LTX rejected the API key. Check your saved secret."
                )
            elif response.status_code == 402:
                st.warning(
                    "LTX requires payment or credits for this request. "
                    "No video was generated. Check the Billing page."
                )
            else:
                st.warning(
                    f"LTX returned HTTP {response.status_code}. "
                    "No video-generation request was sent."
                )

        except requests.RequestException as error:
            st.error(
                f"Could not reach LTX: {error}. "
                "No video-generation request was sent."
            )

