"""
app.py
--------
Streamlit frontend for Gesture Control Presenter.

Run with:
    streamlit run app.py
"""

import json
import time
import collections

import cv2
import streamlit as st

from hand_detector import HandDetector
from gesture_classifier import GestureClassifier
from action_controller import ActionController

st.set_page_config(page_title="Gesture Control Presenter", page_icon="🖐️", layout="wide")

GESTURE_EMOJI = {
    "open_palm": "✋",
    "fist": "✊",
    "two_fingers": "✌️",
    "three_fingers": "🤟",
    "index_only": "☝️",
    "none": "—",
}

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
    /* Tighten default page padding so the dashboard feels intentional, not accidental */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Sidebar: give it a real panel look instead of the bare default */
    section[data-testid="stSidebar"] {
        background-color: #14161a;
        border-right: 1px solid #2a2d34;
        padding-top: 0.5rem;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }

    /* Header bar */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.25rem;
        border-radius: 14px;
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #2a2d34;
        margin-bottom: 1rem;
    }
    .app-header h1 {
        font-size: 1.4rem;
        margin: 0;
    }
    .status-pill {
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-live {
        background-color: #16341f;
        color: #4ade80;
        border: 1px solid #22c55e;
    }
    .status-off {
        background-color: #34211f;
        color: #f87171;
        border: 1px solid #ef4444;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #17191d;
        border: 1px solid #2a2d34;
        border-radius: 12px;
        padding: 0.9rem 1rem;
    }
    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
    }

    /* Video panel frame */
    .video-frame {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #2a2d34;
        background-color: #0d0e10;
        padding: 0.4rem;
    }

    /* Action log */
    .action-log {
        background-color: #17191d;
        border: 1px solid #2a2d34;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        max-height: 260px;
        overflow-y: auto;
        font-size: 0.9rem;
        line-height: 1.9rem;
    }
    .action-log-empty {
        color: #6b7280;
        font-style: italic;
    }

    div[data-testid="stSidebar"] button {
        border-radius: 8px !important;
    }
</style>
"""


@st.cache_resource
def load_config():
    with open("config.json") as f:
        return json.load(f)


def init_session_state():
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("history", collections.deque(maxlen=8))


def render_sidebar(config):
    with st.sidebar:
        st.markdown("### ⚙️ Controls")

        start_col, stop_col = st.columns(2)
        start_clicked = start_col.button("▶️ Start", width="stretch",
                                          disabled=st.session_state.running, type="primary")
        stop_clicked = stop_col.button("⏹️ Stop", width="stretch",
                                        disabled=not st.session_state.running)

        if start_clicked:
            st.session_state.running = True
        if stop_clicked:
            st.session_state.running = False

        st.divider()

        cooldown = st.slider("Gesture Cooldown (seconds)", 0.3, 2.0,
                              config["cooldown_seconds"], 0.1,
                              help="How long to wait before the same gesture can trigger again.")
        hold_frames = st.slider("Stability (frames to confirm gesture)", 3, 15,
                                 config["hold_frames"], 1,
                                 help="Higher = fewer false triggers, but slightly slower response.")
        pointer_mode = st.toggle("🔴 Laser Pointer Mode",
                                  help="When on, showing only your index finger moves your real mouse cursor.")

        st.divider()
        with st.expander("🧠 Gesture Guide", expanded=True):
            st.table({
                "Gesture": ["✋ Open Palm", "🤟 Three Fingers", "✌️ Two Fingers", "✊ Fist", "☝️ Index Finger"],
                "Action": ["Next Slide", "Previous Slide", "Start Slideshow", "Exit Slideshow", "Laser Pointer"],
            })

    return cooldown, hold_frames, pointer_mode


def render_header(pointer_mode):
    status_class = "status-live" if st.session_state.running else "status-off"
    status_text = "🟢 LIVE" if st.session_state.running else "⚪ STOPPED"
    mode_text = "Laser Pointer" if pointer_mode else "Slide Control"
    st.markdown(
        f"""
        <div class="app-header">
            <h1>🖐️ Gesture Control Presenter</h1>
            <div>
                <span class="status-pill {status_class}">{status_text}</span>
                &nbsp;
                <span class="status-pill" style="background:#1f2937;color:#93c5fd;border:1px solid #3b82f6;">
                    Mode: {mode_text}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_log(history_slot):
    if st.session_state.history:
        rows = "".join(f"<div>{entry}</div>" for entry in st.session_state.history)
    else:
        rows = '<div class="action-log-empty">No actions yet — gestures you trigger will show up here.</div>'
    history_slot.markdown(f'<div class="action-log">{rows}</div>', unsafe_allow_html=True)


def run_camera_loop(config, cooldown, hold_frames, pointer_mode,
                     video_slot, gesture_slot, mode_slot, fps_slot, history_slot):
    config = dict(config)
    config["cooldown_seconds"] = cooldown
    config["hold_frames"] = hold_frames

    try:
        detector = HandDetector(min_confidence=config.get("min_detection_confidence", 0.6))
    except FileNotFoundError as err:
        st.error(str(err))
        st.session_state.running = False
        return

    classifier = GestureClassifier(hold_frames=hold_frames)
    controller = ActionController(config)

    cap = cv2.VideoCapture(config.get("camera_index", 0))
    if not cap.isOpened():
        st.warning("⚠️ Camera not available in this cloud environment. This app is designed to run locally with a webcam — clone the repo and run 'streamlit run app.py' on your machine to try it live.")
        st.session_state.running = False
        return

    prev_time = time.time()

    try:
        while st.session_state.running:
            ok, frame = cap.read()
            if not ok:
                st.error("Lost connection to the webcam.")
                break

            frame = cv2.flip(frame, 1)  # mirror, feels natural
            landmarks = detector.detect(frame)
            gesture = classifier.classify_stable(landmarks)

            HandDetector.draw_landmarks(frame, landmarks)

            if pointer_mode and gesture == "index_only" and landmarks:
                controller.move_pointer(*landmarks[8])  # index fingertip
            else:
                fired_action = controller.trigger(gesture)
                if fired_action:
                    entry = f"{GESTURE_EMOJI.get(gesture, '')} {gesture.replace('_', ' ').title()} → {fired_action.replace('_', ' ').title()}"
                    st.session_state.history.appendleft(entry)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            video_slot.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                              channels="RGB", width="stretch")
            gesture_slot.metric("Detected Gesture",
                                 f"{GESTURE_EMOJI.get(gesture, '—')} {gesture.replace('_', ' ').title()}")
            mode_slot.metric("Mode", "🔴 Laser Pointer" if pointer_mode else "🖱️ Slide Control")
            fps_slot.metric("FPS", f"{fps:.1f}")
            render_action_log(history_slot)
    finally:
        cap.release()
        try:
            detector.close()
        except RuntimeError:
            # Streamlit can kill the script thread mid-loop (e.g. clicking Stop,
            # or any widget triggering a rerun). By the time this finally block
            # runs, MediaPipe's internal executor may already be shutting down,
            # so close() can raise "cannot schedule new futures after shutdown".
            # The resources are being torn down either way — safe to ignore.
            pass


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()
    config = load_config()

    cooldown, hold_frames, pointer_mode = render_sidebar(config)
    render_header(pointer_mode)

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        video_slot = st.empty()

    with col2:
        m1, m2, m3 = st.columns(3)
        with m1:
            gesture_slot = st.empty()
        with m2:
            mode_slot = st.empty()
        with m3:
            fps_slot = st.empty()

        st.markdown("#### 📜 Recent Actions")
        history_slot = st.empty()

    if not st.session_state.running:
        with col1:
            video_slot.info("📷 Camera is off. Click **▶️ Start** in the sidebar to begin.")
        gesture_slot.metric("Detected Gesture", "—")
        mode_slot.metric("Mode", "🔴 Laser Pointer" if pointer_mode else "🖱️ Slide Control")
        fps_slot.metric("FPS", "—")
        render_action_log(history_slot)
        return

    run_camera_loop(config, cooldown, hold_frames, pointer_mode,
                     video_slot, gesture_slot, mode_slot, fps_slot, history_slot)


if __name__ == "__main__":
    main()