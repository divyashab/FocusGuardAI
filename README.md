# FocusGuardAI 🎯
### Real-Time Study Focus & Distraction Monitor

FocusGuardAI is a computer vision-based study monitoring application that uses webcam input to estimate screen-facing behavior and track study sessions. It combines head pose estimation, focus/distraction tracking, a Pomodoro timer, session logging, and an interactive analytics dashboard.

## ✨ Features

- Real-time webcam monitoring
- Face detection
- Facial landmark detection
- Head pose estimation using Yaw, Pitch, and Roll
- Focus and distraction state estimation
- 3-second distraction grace period
- Focus score calculation
- Pomodoro timer
- Session data logging using CSV
- Streamlit dashboard
- Overview, Analytics, and Session History pages
- Smart Focus Insights

## 🛠️ Tech Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- Streamlit
- Pandas

## ⚙️ How It Works

1. The webcam captures live video frames.
2. The application detects the face and facial landmarks.
3. Head orientation is estimated using head pose calculations.
4. Head direction and face visibility are used to estimate screen-facing behavior.
5. Focus time, distraction time, and distraction events are tracked.
6. A focus score is calculated from session metrics.
7. Session data is saved in a CSV file.
8. Streamlit displays session statistics and analytics.

## 📂 Project Structure

```text
FocusGuardAI/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── face_landmarker.task
│   ├── blaze_face_short_range.tflite
│   └── session_history.csv
│
├── src/
│   ├── main.py
│   └── pomodoro.py
│
├── screenshots/
│
└── venv/
```

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/FocusGuardAI.git
cd FocusGuardAI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Ensure model files are present

Place the required model files inside the `data/` directory:

- `face_landmarker.task`
- `blaze_face_short_range.tflite`

## ▶️ Running the Application

### Webcam Focus Monitor

```bash
python src/main.py
```

### Dashboard

```bash
streamlit run app.py
```

The dashboard opens in your browser. If it does not open automatically, use the Local URL displayed in the terminal.

## 📊 Dashboard

The dashboard includes:

- **Overview:** Summary of study sessions and focus metrics
- **Analytics:** Charts and analysis of focus performance
- **Session History:** Previously saved study sessions

## 📈 Focus Score

The focus score is calculated using the recorded focus and distraction durations:

**Focus Score = (Focus Time / Total Tracked Time) × 100**

It represents estimated screen-facing behavior during the session and is not a direct measurement of mental concentration.

## 🔒 Privacy

FocusGuardAI is designed to process webcam frames for real-time monitoring. The project logs session metrics rather than intentionally storing webcam video recordings.

## ⚠️ Limitations

- Head pose is used as an approximation of screen-facing behavior.
- Looking at the screen does not necessarily mean a person is mentally focused.
- Lighting, camera placement, facial visibility, and movement may affect detection.
- The application is a prototype and its measurements may not always be accurate.

## 🔮 Future Improvements

- Personalized head-pose calibration
- Improved gaze estimation
- More robust detection across lighting conditions
- More advanced focus analytics
- Additional productivity insights

## 👩‍💻 Author

**Divyasha Biswal**

Computer Science & Engineering Student | Aspiring AI Engineer

