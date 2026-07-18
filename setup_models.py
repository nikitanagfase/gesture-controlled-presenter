"""
setup_models.py
------------------
One-time setup script. Downloads MediaPipe's pretrained Hand Landmarker
model into models/hand_landmarker.task.

Run this once, before the first `streamlit run app.py`:
    python setup_models.py
"""

import os
import urllib.request

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "hand_landmarker.task")


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(MODEL_PATH):
        print(f"✅ Model already exists at '{MODEL_PATH}'. Nothing to do.")
        return

    print("⬇️  Downloading hand_landmarker.task ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    except Exception as err:
        print(f"❌ Download failed: {err}")
        print(f"   You can manually download it from:\n   {MODEL_URL}")
        print(f"   and place it at: {MODEL_PATH}")
        raise SystemExit(1)

    print(f"✅ Model downloaded to '{MODEL_PATH}'")


if __name__ == "__main__":
    main()
