# 🖐️ Gesture Control Presenter

## Author
Nikita Nagfase

## Affiliation
Department Of MCA | Suryodaya College Of Engineering and  technology

## Abstract
Gesture Control Presenter is a computer-vision-based application designed to enable hands-free control of digital slide presentations (Google Slides) using real-time hand gesture recognition. The system captures live webcam input, detects hand landmarks using MediaPipe, classifies the gesture, and maps it to a corresponding keyboard action using PyAutoGUI.

The system leverages OpenCV for video processing, MediaPipe for AI-based hand landmark detection, and PyAutoGUI for automated keyboard control. A Streamlit-based frontend is integrated to provide a simple, interactive, and professional user interface for starting/stopping detection and viewing live gesture feedback.

The proposed solution aims to enhance human-computer interaction during presentations by removing the dependency on physical input devices such as a mouse, keyboard, or remote clicker.

## 1. Introduction
Traditional slide presentations require presenters to rely on a keyboard, mouse, or remote clicker to navigate slides, which can restrict natural movement and audience engagement. With the growth of computer vision and AI-based gesture recognition, it has become possible to build touchless, intuitive control systems.

Gesture Control Presenter addresses this limitation by allowing presenters to control their slides using simple hand gestures captured through a standard laptop webcam, without requiring any additional hardware.

A distinctive aspect of the system is its real-time gesture stability check (cooldown mechanism), which prevents accidental multiple triggers and ensures reliable slide control.

## 2. Literature Review
Existing systems in the domain of gesture recognition and presentation control exhibit partial solutions to the identified problem:

**Remote Clicker Devices:** Physical presentation remotes provide reliable slide control but require additional hardware and have limited functionality beyond next/previous slide.

**Generic Gesture Recognition Tools:** Some open-source gesture libraries provide raw hand tracking but do not offer application-specific mapping to presentation software.

**Voice-Controlled Presentation Tools:** Voice-based systems allow hands-free control but are unreliable in noisy environments and raise privacy concerns during live presentations.

### Research Gap
- Lack of lightweight, camera-only gesture control systems for presentations
- Absence of gesture stability/debounce mechanisms in beginner-level projects
- No unified system combining real-time detection with a simple, accessible frontend

Gesture Control Presenter addresses these gaps through a modular, beginner-friendly, and extensible system design.

## 3. Methodology

### System Architecture
The system follows a modular pipeline architecture, where the webcam feed is processed frame-by-frame through a hand detection module, a gesture classification module, and an action control module, coordinated through a Streamlit-based frontend.

### Development Approach
An incremental development model is adopted, starting with core gesture detection logic, followed by action mapping, and finally frontend integration.

### Functional Modules
- Hand Detection Module
- Gesture Classification Module
- Action Control Module
- Configuration Management Module
- Streamlit Frontend Module

## 4. Implementation

| Component | Technology Used |
|---|---|
| Hand Detection | MediaPipe Hand Landmarker |
| Video Processing | OpenCV |
| Gesture Classification | Custom Python logic (landmark geometry) |
| Action Control | PyAutoGUI |
| Frontend | Streamlit |
| Configuration | JSON |

## 5. Project Structure
```
gesture-slides/
│
├── app.py                     # Streamlit frontend (main entry point)
├── hand_detector.py           # Finds hand + 21 landmarks
├── gesture_classifier.py      # Decides which gesture it is
├── action_controller.py       # Presses keyboard keys (PyAutoGUI)
├── config.json                 # Gesture → action mapping
├── setup_models.py             # Downloads hand_landmarker.task
├── requirements.txt
├── .gitignore
├── README.md
├── models/
│   └── hand_landmarker.task    # (downloaded, not uploaded to git)
└── assets/
    └── demo.gif                # optional demo for README
```

## 6. System Workflow
1. User launches the Streamlit application
2. Webcam feed is captured frame-by-frame using OpenCV
3. MediaPipe detects 21 hand landmarks per frame
4. Gesture Classifier determines finger positions and identifies the gesture
5. Gesture is held for a minimum stable duration (cooldown check)
6. Action Controller triggers the corresponding keyboard shortcut
7. Google Slides responds to the simulated key press
8. Streamlit UI displays the detected gesture and triggered action in real time

## 7. Gesture Mapping

| Gesture | Action |
|---|---|
| ✋ Open Palm | Next Slide |
| 🤟 Three Fingers | Previous Slide |
| ✌️ Two Fingers | Start Slideshow |
| ✊ Fist | Exit Slideshow |
| ☝️ Index Finger | Laser Pointer Mode (moves real system cursor) |

## 8. Installation

```bash
git clone https://github.com/<your-username>/gesture-slides.git
cd gesture-slides
pip install -r requirements.txt
python setup_models.py
streamlit run app.py
```

## 9. Results and Discussion
The system demonstrates effective real-time gesture recognition with minimal latency on a standard laptop webcam. The cooldown mechanism significantly reduces false or repeated triggers, improving control reliability. The Streamlit frontend provides an accessible interface for non-technical users to start, stop, and monitor gesture detection without using the terminal.

Additional features implemented in the final build:
- **Laser Pointer Mode** — showing only the index finger moves the real system mouse cursor, controlled via a sidebar toggle
- **Live FPS counter** — displays real-time processing speed for performance monitoring
- **Adjustable sensitivity controls** — sliders for gesture cooldown and stability (hold frames), letting the user tune responsiveness without editing code
- **Action history log** — sidebar panel showing the last several triggered gestures and their corresponding actions

## 10. Limitations
- Requires good lighting conditions for accurate detection
- Single-hand support only in current version
- macOS-specific keyboard shortcuts require modification for Windows/Linux
- No support for custom user-trained gestures

## 11. Future Scope
- Two-hand gesture support
- Custom gesture training/calibration mode
- Zoom / volume control gestures
- Deployment as a standalone desktop application
- Support for PowerPoint and other presentation tools
- AI-based personalized gesture recognition per user

## 12. Conclusion
Gesture Control Presenter provides a lightweight, accessible, and hardware-free solution for hands-free presentation control. By combining real-time computer vision with a simple Streamlit interface, the system offers a practical demonstration of applied AI and human-computer interaction, with strong potential for future expansion into a fully-featured presentation automation tool.
