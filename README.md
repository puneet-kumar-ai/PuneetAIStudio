# 🎬 Puneet AI Studio

**Create cinematic reels from your photographs and stories using Python and Streamlit.**

Puneet AI Studio is a Python-based application designed to turn photographs and written stories into short cinematic videos. It combines image processing, automated video creation, and scene planning in one simple interface.

## ✨ Features

### 1. Cinematic Reel Creator
- Upload multiple photographs in story order.
- Add a story or narration.
- Control the duration of each photograph.
- Adjust cinematic zoom effects.
- Generate vertical MP4 videos.
- Download the finished reel.

### 2. AI Script-to-Scene Planner
- Convert a written story into individual scenes.
- Generate narration for each scene.
- Create visual directions.
- Generate scene-specific animation directions.

### 3. LTX AI Video Integration (Currently Disabled)
- Dedicated image-to-video workflow.
- Motion prompt and video-duration controls.
- LTX API integration prepared in the codebase.
- Generation and API-check buttons are currently disabled for safety.

## 🛠️ Technologies Used

- Python
- Streamlit
- Pillow (PIL)
- FFmpeg / imageio-ffmpeg
- Requests

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/puneet-kumar-ai/PuneetAIStudio.git
cd PuneetAIStudio
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment (Windows)

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the application

```bash
python -m streamlit run app.py
```

Open the local URL displayed in your terminal.

## 🔐 Security

- API keys and credentials should never be committed to GitHub.
- Store private credentials in Streamlit secrets or environment variables.
- The `.streamlit/secrets.toml` file is excluded through `.gitignore`.
- LTX generation is currently disabled.

## 🚀 Project Status

The core photo-to-reel creation workflow and script-to-scene planner are implemented and locally tested.

Further development is planned for AI video generation, improved scene planning, and additional cinematic editing features.

## 👨‍💻 Developer

**Puneet Kumar**

GitHub: [@puneet-kumar-ai](https://github.com/puneet-kumar-ai)

---

*Puneet AI Studio — Turning stories and photographs into cinematic experiences.*
