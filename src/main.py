
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
import time
import csv

try:
    import winsound
except ImportError:
    winsound = None

# =========================================
# FOCUSGUARD AI - INTEGRATED SYSTEM
# Webcam + Head Pose + Focus Tracking + Pomodoro
# + Session History (CSV)
# =========================================

# -------- Pomodoro settings --------

TEST_MODE = False

STUDY_DURATION = 25 * 60       # 25 minutes
SHORT_BREAK = 5 * 60           # 5 minutes
LONG_BREAK = 15 * 60            # 15 minutes

LONG_BREAK_EVERY = 4
GRACE_PERIOD = 3.0

mode = "STUDY"
remaining_time = STUDY_DURATION
timer_running = False
completed_sessions = 0
timer_tick = 0.0

# -------- Load MediaPipe model --------

MODEL_PATH = Path("data/face_landmarker.task")

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

# -------- Webcam --------

cap = cv2.VideoCapture(0)

print("FocusGuard AI Integrated System Started!")
print("S = Start/Pause | R = Reset | Q = Quit")

start_time = time.time()
previous_frame_time = time.time()

# -------- Focus statistics --------

focus_seconds = 0.0
distraction_seconds = 0.0
distraction_count = 0

away_start = None
currently_distracted = False

# -------- Face model points --------

face_3d_model = np.array([
    (0.0, 0.0, 0.0),
    (0.0, -330.0, -65.0),
    (-225.0, 170.0, -135.0),
    (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0),
    (150.0, -150.0, -125.0)
], dtype=np.float64)

landmark_ids = [1, 152, 33, 263, 61, 291]


# =========================================
# FUNCTIONS
# =========================================

def play_sound():
    if winsound:
        try:
            winsound.Beep(1000, 400)
        except Exception:
            pass


def reset_timer():
    global remaining_time, timer_running, timer_tick

    if mode == "STUDY":
        remaining_time = STUDY_DURATION
    elif mode == "SHORT BREAK":
        remaining_time = SHORT_BREAK
    else:
        remaining_time = LONG_BREAK

    timer_running = False
    timer_tick = 0.0


def format_time(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def save_session_report():

    report_path = Path("data/session_history.csv")

    # Ensure the data folder exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = report_path.exists()

    with open(report_path, "a", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        # Write headers only when the file is new or empty
        if not file_exists or report_path.stat().st_size == 0:

            writer.writerow([
                "Date",
                "Total Session (seconds)",
                "Focus Time (seconds)",
                "Distraction Time (seconds)",
                "Distraction Events",
                "Focus Score (%)",
                "Completed Pomodoros"
            ])

        tracked_time = focus_seconds + distraction_seconds

        if tracked_time > 0:
            score = (focus_seconds / tracked_time) * 100
        else:
            score = 0.0

        writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            int(total_session),
            round(focus_seconds, 2),
            round(distraction_seconds, 2),
            distraction_count,
            round(score, 2),
            completed_sessions
        ])

    print(f"\nSession saved successfully to: {report_path}")


# =========================================
# MAIN LOOP
# =========================================

with FaceLandmarker.create_from_options(options) as landmarker:

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms = int((time.time() - start_time) * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        # Frame time
        now = time.time()
        dt = min(now - previous_frame_time, 0.1)
        previous_frame_time = now

        direction = "FACE NOT DETECTED"
        pitch = yaw = roll = 0.0

        # ---------------------------------
        # 1. HEAD POSE ESTIMATION
        # ---------------------------------

        if result.face_landmarks:

            landmarks = result.face_landmarks[0]
            face_2d = []

            for idx in landmark_ids:

                x = int(landmarks[idx].x * width)
                y = int(landmarks[idx].y * height)

                face_2d.append((x, y))
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

            face_2d = np.array(face_2d, dtype=np.float64)

            focal_length = width
            center = (width / 2, height / 2)

            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)

            distortion = np.zeros((4, 1))

            pose_success, rotation_vector, translation_vector = cv2.solvePnP(
                face_3d_model,
                face_2d,
                camera_matrix,
                distortion,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

            if pose_success:

                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

                angles, _, _, _, _, _ = cv2.RQDecomp3x3(
                    rotation_matrix
                )

                pitch, yaw, roll = angles

                if yaw > 15:
                    direction = "LOOKING LEFT"
                elif yaw < -15:
                    direction = "LOOKING RIGHT"
                elif pitch > 15:
                    direction = "LOOKING DOWN"
                elif pitch < -15:
                    direction = "LOOKING UP"
                else:
                    direction = "CENTER"

        # ---------------------------------
        # 2. FOCUS / DISTRACTION TRACKING
        # ---------------------------------

        looking_away = direction != "CENTER"

        if looking_away:

            if away_start is None:
                away_start = now

            away_duration = now - away_start

            if away_duration >= GRACE_PERIOD:

                if not currently_distracted:
                    distraction_count += 1
                    currently_distracted = True

                distraction_seconds += dt
                focus_status = "DISTRACTED"

            else:
                focus_seconds += dt
                focus_status = "GRACE PERIOD"

        else:

            away_start = None
            currently_distracted = False

            focus_seconds += dt
            focus_status = "FOCUSED"

        # ---------------------------------
        # 3. POMODORO COUNTDOWN
        # ---------------------------------

        if timer_running:

            timer_tick += dt

            if timer_tick >= 1.0:

                seconds_to_subtract = int(timer_tick)
                remaining_time -= seconds_to_subtract
                timer_tick -= seconds_to_subtract

            if remaining_time <= 0:

                remaining_time = 0
                timer_running = False
                play_sound()

                if mode == "STUDY":

                    completed_sessions += 1

                    if completed_sessions % LONG_BREAK_EVERY == 0:
                        mode = "LONG BREAK"
                        remaining_time = LONG_BREAK
                    else:
                        mode = "SHORT BREAK"
                        remaining_time = SHORT_BREAK

                else:

                    mode = "STUDY"
                    remaining_time = STUDY_DURATION

                timer_tick = 0.0

        # ---------------------------------
        # 4. CALCULATE FOCUS SCORE
        # ---------------------------------

        tracked_time = focus_seconds + distraction_seconds

        if tracked_time > 0:
            focus_score = (focus_seconds / tracked_time) * 100
        else:
            focus_score = 0.0

        session_time = now - start_time

        # ---------------------------------
        # 5. DISPLAY INFORMATION
        # ---------------------------------

        cv2.putText(
            frame, f"FocusGuard AI | {mode}",
            (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (0, 255, 255), 2
        )

        cv2.putText(
            frame, f"Pomodoro: {format_time(remaining_time)}",
            (20, 75), cv2.FONT_HERSHEY_SIMPLEX,
            0.8, (255, 255, 255), 2
        )

        cv2.putText(
            frame, f"Timer: {'RUNNING' if timer_running else 'PAUSED'}",
            (20, 110), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 0), 2
        )

        cv2.putText(
            frame, f"Direction: {direction}",
            (20, 155), cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (255, 255, 255), 2
        )

        cv2.putText(
            frame, f"Status: {focus_status}",
            (20, 195), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (0, 255, 0), 2
        )

        cv2.putText(
            frame, f"Focus: {int(focus_seconds)} sec",
            (20, 240), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 255, 0), 2
        )

        cv2.putText(
            frame, f"Distraction: {int(distraction_seconds)} sec",
            (20, 280), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 0, 255), 2
        )

        cv2.putText(
            frame, f"Events: {distraction_count}",
            (20, 320), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 0), 2
        )

        cv2.putText(
            frame, f"Focus Score: {focus_score:.1f}%",
            (20, 360), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 255, 255), 2
        )

        cv2.putText(
            frame, f"Completed Pomodoros: {completed_sessions}",
            (20, 400), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 255), 2
        )

        # ---------------------------------
        # 6. KEYBOARD CONTROLS
        # ---------------------------------

        cv2.imshow("FocusGuard AI", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            timer_running = not timer_running

        elif key == ord("r"):
            reset_timer()

        elif key == ord("q"):
            break

# =========================================
# CLEANUP
# =========================================

cap.release()
cv2.destroyAllWindows()

# =========================================
# FINAL SESSION REPORT
# =========================================

total_session = time.time() - start_time

tracked_time = focus_seconds + distraction_seconds

if tracked_time > 0:
    final_score = (focus_seconds / tracked_time) * 100
else:
    final_score = 0.0

print("\n========== FOCUSGUARD SESSION REPORT ==========")
print(f"Total session: {int(total_session)} seconds")
print(f"Focus time: {int(focus_seconds)} seconds")
print(f"Distraction time: {int(distraction_seconds)} seconds")
print(f"Distraction events: {distraction_count}")
print(f"Focus score: {final_score:.1f}%")
print(f"Pomodoros completed: {completed_sessions}")
print("============================================")

# Save session to CSV
save_session_report()

print("FocusGuard AI session ended.")


