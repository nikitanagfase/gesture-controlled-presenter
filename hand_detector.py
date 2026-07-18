"""
hand_detector.py
-----------------
Wraps MediaPipe's Hand Landmarker so the rest of the app never has to
touch MediaPipe's API directly. Give it a frame, get back 21 (x, y)
landmark points (normalized 0-1) for the first detected hand.
"""

import os
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

DEFAULT_MODEL_PATH = os.path.join("models", "hand_landmarker.task")


class HandDetector:
    """Detects a single hand's landmarks in a BGR video frame."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH,
                 max_hands: int = 1, min_confidence: float = 0.6):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at '{model_path}'.\n"
                f"Run 'python setup_models.py' first to download it."
            )

        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands,
            min_hand_detection_confidence=min_confidence,
            min_hand_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence,
            # VIDEO mode enables MediaPipe's internal frame-to-frame tracking,
            # which makes landmark positions far more stable than IMAGE mode
            # (IMAGE mode treats every frame as a brand-new, unrelated photo).
            running_mode=vision.RunningMode.VIDEO,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

        # VIDEO mode requires a strictly increasing timestamp per frame.
        self._start_time = time.time()
        self._last_timestamp_ms = -1

    def detect(self, frame_bgr):
        """
        Runs detection on one frame.

        Returns:
            list[tuple[float, float]] | None:
                21 normalized (x, y) landmark points for the first hand
                found, or None if no hand is visible in the frame.
        """
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp_ms = int((time.time() - self._start_time) * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1  # guard against duplicates
        self._last_timestamp_ms = timestamp_ms

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return None

        first_hand = result.hand_landmarks[0]
        return [(lm.x, lm.y) for lm in first_hand]

    @staticmethod
    def draw_landmarks(frame_bgr, landmarks):
        """Draws small circles on the frame for each landmark (in place)."""
        if not landmarks:
            return frame_bgr
        h, w = frame_bgr.shape[:2]
        for x, y in landmarks:
            cv2.circle(frame_bgr, (int(x * w), int(y * h)), 4, (0, 220, 0), -1)
        return frame_bgr

    def close(self):
        self._landmarker.close()