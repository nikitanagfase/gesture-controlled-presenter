"""
gesture_classifier.py
-----------------------
Turns 21 raw hand landmarks into a named gesture.

Logic:
1. For each finger, check whether the tip is "extended" past its
   knuckle (finger up) or not (finger down), with a small margin so
   borderline/noisy landmark positions don't flip-flop between
   "up" and "down" every frame.
2. Combine the 5 up/down states into a gesture name.
3. Smooth over several frames so a single noisy frame can't trigger
   a false action (this is the "hold" / stability mechanism). Uses a
   majority vote rather than requiring every frame to match exactly,
   since some poses (e.g. ring finger up, pinky down) are naturally
   harder to hold perfectly still due to shared tendons between the
   ring and pinky fingers.
"""

from collections import deque

# MediaPipe hand landmark indices
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18

GESTURE_NAMES = ("open_palm", "fist", "two_fingers", "three_fingers", "index_only")

# Fraction of the history window that must agree for classify_stable to
# commit to a gesture. 1.0 == unanimous (the old, very strict behavior).
# 0.7 tolerates a couple of noisy/misread frames within the window.
STABILITY_THRESHOLD = 0.7

# Normalized-coordinate margin used when deciding if a finger is
# "extended". Without this, a finger sitting almost exactly at its PIP
# joint's y-level flickers between up/down every frame due to landmark
# jitter, which is what was causing two_fingers/three_fingers/index_only
# to mostly get classified as "unknown". Tune this if your fingers still
# don't register — try 0.01 (more sensitive) to 0.04 (more tolerant).
FINGER_MARGIN = 0.02


class GestureClassifier:
    def __init__(self, hold_frames: int = 8):
        self.hold_frames = hold_frames
        self._history = deque(maxlen=hold_frames)

    # ---------- low-level finger math ----------

    @staticmethod
    def _finger_states(landmarks):
        """Returns [thumb, index, middle, ring, pinky] as booleans (True = up)."""
        thumb_up = landmarks[THUMB_TIP][0] < landmarks[THUMB_IP][0]

        finger_pairs = [
            (INDEX_TIP, INDEX_PIP),
            (MIDDLE_TIP, MIDDLE_PIP),
            (RING_TIP, RING_PIP),
            (PINKY_TIP, PINKY_PIP),
        ]
        # Smaller y = higher up in the image = finger extended.
        # Margin makes "extended" require the tip to be clearly above the
        # PIP joint, not just barely, which kills a lot of frame-to-frame
        # flicker on borderline poses.
        others_up = [
            landmarks[tip][1] < (landmarks[pip][1] - FINGER_MARGIN)
            for tip, pip in finger_pairs
        ]

        return [thumb_up] + others_up

    # ---------- classification ----------

    def classify_frame(self, landmarks):
        """Classifies a single frame. Returns 'none' or 'unknown' if not confident."""
        if landmarks is None:
            return "none"

        thumb, index, middle, ring, pinky = self._finger_states(landmarks)
        up_count = sum([thumb, index, middle, ring, pinky])

        if up_count == 5:
            return "open_palm"
        if up_count == 0:
            return "fist"
        if index and middle and not ring and not pinky:
            return "two_fingers"
        if index and middle and ring and not pinky:
            return "three_fingers"
        if index and not middle and not ring and not pinky:
            return "index_only"

        return "unknown"

    def classify_stable(self, landmarks):
        """
        Feeds the current frame into a rolling window and returns a
        gesture once it accounts for at least STABILITY_THRESHOLD of the
        window, rather than requiring every single frame to match.
        """
        gesture = self.classify_frame(landmarks)
        self._history.append(gesture)

        if len(self._history) < self.hold_frames:
            return "none"

        counts = {name: self._history.count(name) for name in GESTURE_NAMES}
        best_gesture, best_count = max(counts.items(), key=lambda kv: kv[1])

        if best_count / len(self._history) >= STABILITY_THRESHOLD:
            return best_gesture

        return "none"

    def debug_frame(self, landmarks):
        """
        Returns raw finger states + up_count for one frame — useful to
        print/overlay on screen while tuning FINGER_MARGIN for your
        specific camera/lighting/hand size.
        """
        if landmarks is None:
            return None
        thumb, index, middle, ring, pinky = self._finger_states(landmarks)
        return {
            "thumb": thumb, "index": index, "middle": middle,
            "ring": ring, "pinky": pinky,
            "up_count": sum([thumb, index, middle, ring, pinky]),
            "classified_as": self.classify_frame(landmarks),
        }

    def reset(self):
        self._history.clear()