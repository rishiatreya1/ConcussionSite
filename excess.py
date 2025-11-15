"""
ConcussionSite - Light-Sensitivity & Oculomotor Screening Tool
A webcam-based concussion screening prototype using:
- MediaPipe FaceMesh eye tracking
- EAR-based blink detection (Soukupová & Čech, 2016)
- Light flicker stress test (photophobia)
- Smooth pursuit vertical dot tracking (oculomotor dysfunction)

DISCLAIMER:
This is a research/demo tool only. It does NOT diagnose concussion.
Always consult a qualified healthcare professional.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import os
import math
from dotenv import load_dotenv

# Gemini SDK
import google.generativeai as genai

# ============================================================
# ENV + GEMINI CONFIG
# ============================================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️  GEMINI_API_KEY not found in .env – AI summaries will be skipped.")


# ============================================================
# MEDIAPIPE FACE MESH SETUP
# ============================================================
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Eye landmark indices for EAR calculation (MediaPipe FaceMesh)
# Using 6 points per eye: [left corner, top, top-mid, right corner, bottom-mid, bottom]
# Left eye: outer corner(33), inner corner(133), top(159), top-mid(158), bottom-mid(153), bottom(144)
# Right eye: outer corner(362), inner corner(263), top(386), top-mid(385), bottom-mid(373), bottom(380)
LEFT_EYE_EAR_INDICES = [33, 159, 158, 133, 153, 144]
RIGHT_EYE_EAR_INDICES = [362, 386, 385, 263, 373, 380]

# Full eye indices for gaze center estimation
LEFT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173,
                    157, 158, 159, 160, 161, 246]
RIGHT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263,
                     466, 388, 387, 386, 385, 384, 398]

# EAR thresholds
EAR_BASE_THRESHOLD = 0.25
EAR_CONSECUTIVE_FRAMES = 2  # frames below threshold to count a blink


# ============================================================
# CORE MATH UTILITIES
# ============================================================
def calculate_ear(eye_landmarks):
    """
    Calculate Eye Aspect Ratio (EAR) for blink detection.
    Based on Soukupová & Čech, 2016.

    eye_landmarks: 6 points in order:
      [left, top, top-mid, right, bottom-mid, bottom]
    """
    if len(eye_landmarks) < 6:
        return 0.3  # default "open" eye value

    points = np.array(eye_landmarks)

    # Vertical distances
    v1 = np.linalg.norm(points[1] - points[5])   # top to bottom
    v2 = np.linalg.norm(points[2] - points[4])   # top-mid to bottom-mid

    # Horizontal distance
    h = np.linalg.norm(points[0] - points[3])

    if h == 0:
        return 0.0

    ear = (v1 + v2) / (2.0 * h)
    return ear


def get_eye_center(eye_landmarks):
    """Return the (x,y) center of an eye from a list of [x,y] points."""
    if len(eye_landmarks) == 0:
        return None
    return np.mean(eye_landmarks, axis=0)


def calculate_gaze_distance(eye_center, image_center):
    """
    Distance between eye center and image center.
    Larger distance ≈ looking away (gaze aversion).
    """
    if eye_center is None:
        return 0.0
    return float(np.linalg.norm(eye_center - image_center))


# ============================================================
# GAZE POINT ESTIMATION FOR PURSUIT TEST
# ============================================================
def estimate_gaze_point(frame):
    """
    Estimate gaze/eye center in STIMULUS COORDINATES (800x600)
    by tracking eye center in webcam image and scaling.

    Returns:
        (gx, gy) in 800x600 space, or None if face not found.
    """
    h, w = frame.shape[:2]
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    if not results.multi_face_landmarks:
        return None

    face_landmarks = results.multi_face_landmarks[0]

    left_eye_full = []
    right_eye_full = []

    for idx in LEFT_EYE_INDICES:
        lm = face_landmarks.landmark[idx]
        x = lm.x * w
        y = lm.y * h
        left_eye_full.append([x, y])

    for idx in RIGHT_EYE_INDICES:
        lm = face_landmarks.landmark[idx]
        x = lm.x * w
        y = lm.y * h
        right_eye_full.append([x, y])

    left_center = get_eye_center(left_eye_full)
    right_center = get_eye_center(right_eye_full)

    if left_center is None or right_center is None:
        return None

    eye_center = (left_center + right_center) / 2.0

    # Scale webcam coordinates → stimulus coordinates (800x600)
    gx = int((eye_center[0] / w) * 800)
    gy = int((eye_center[1] / h) * 600)

    return (gx, gy)


# ============================================================
# FLICKER STIMULUS WINDOW
# ============================================================
def create_flicker_window():
    """Create flicker window."""
    window_name = "Light Sensitivity Test - Look at this window"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)
    return window_name


def flicker_display(window_name, frame_count, flicker_rate=10):
    """
    Show alternating white/black frame as flicker stimulus.
    flicker_rate: frames per cycle.
    """
    is_white = (frame_count // flicker_rate) % 2 == 0
    color = 255 if is_white else 0
    stim = np.full((600, 800, 3), color, dtype=np.uint8)

    text = "Keep looking at this window"
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
    text_x = (800 - text_size[0]) // 2
    text_y = 300
    cv2.putText(
        stim,
        text,
        (text_x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (128, 128, 128) if is_white else (255, 255, 255),
        2
    )

    cv2.imshow(window_name, stim)


# ============================================================
# MAIN PHASE LOOP (BASELINE & FLICKER)
# ============================================================
def run_phase(cap, flicker_window_name, phase_name, duration_sec, flicker=False):
    """
    Run a test phase:
      - Baseline (no flicker)
      - Flicker (with window)
    Track:
      - blink_count
      - eye_closed_time
      - gaze_distances
      - face_detection_rate
      - avg EAR

    Returns a metrics dict.
    """
    print(f"\n{'='*60}")
    print(f"Starting {phase_name} phase ({duration_sec} seconds)")
    print(f"{'='*60}")
    print("Please look at the camera and keep your eyes open.")
    if flicker:
        print("A flickering window will appear. Try to keep looking at it.")

    start_time = time.time()
    blink_count = 0
    eye_closed_time = 0.0
    gaze_distances = []
    frame_count = 0
    last_ear_time = time.time()
    is_eye_closed = False
    ear_below_threshold_count = 0
    ear_values = []
    face_detected_count = 0

    while time.time() - start_time < duration_sec:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        h, w = frame.shape[:2]
        image_center = np.array([w / 2, h / 2])

        current_time = time.time()
        frame_duration = current_time - last_ear_time
        last_ear_time = current_time

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            face_detected_count += 1

            # EAR landmarks (6 per eye)
            left_eye_ear = []
            right_eye_ear = []
            for idx in LEFT_EYE_EAR_INDICES:
                lm = face_landmarks.landmark[idx]
                left_eye_ear.append([lm.x * w, lm.y * h])
            for idx in RIGHT_EYE_EAR_INDICES:
                lm = face_landmarks.landmark[idx]
                right_eye_ear.append([lm.x * w, lm.y * h])

            # Full eye for gaze
            left_eye_full = []
            right_eye_full = []
            for idx in LEFT_EYE_INDICES:
                lm = face_landmarks.landmark[idx]
                left_eye_full.append([lm.x * w, lm.y * h])
            for idx in RIGHT_EYE_INDICES:
                lm = face_landmarks.landmark[idx]
                right_eye_full.append([lm.x * w, lm.y * h])

            # EAR calc
            ear_left = calculate_ear(left_eye_ear)
            ear_right = calculate_ear(right_eye_ear)
            avg_ear = (ear_left + ear_right) / 2.0
            ear_values.append(avg_ear)

            # Adaptive threshold
            if len(ear_values) > 10:
                baseline_ear = np.mean(ear_values[-30:])
                adaptive_threshold = baseline_ear * 0.70
                current_threshold = max(adaptive_threshold, 0.20)
            else:
                current_threshold = EAR_BASE_THRESHOLD

            # Blink detection
            if avg_ear < current_threshold:
                ear_below_threshold_count += 1
                if not is_eye_closed and ear_below_threshold_count >= EAR_CONSECUTIVE_FRAMES:
                    blink_count += 1
                    is_eye_closed = True
                if is_eye_closed:
                    eye_closed_time += frame_duration
            else:
                ear_below_threshold_count = 0
                if is_eye_closed:
                    is_eye_closed = False

            # Gaze aversion
            left_center = get_eye_center(left_eye_full)
            right_center = get_eye_center(right_eye_full)
            if left_center is not None and right_center is not None:
                eye_center = (left_center + right_center) / 2.0
                gaze_dist = calculate_gaze_distance(eye_center, image_center)
                gaze_distances.append(gaze_dist)

            # Draw landmarks
            mp_drawing.draw_landmarks(
                frame,
                face_landmarks,
                mp_face_mesh.FACEMESH_CONTOURS,
                None,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
            )

            # HUD
            cv2.putText(
                frame,
                f"EAR: {avg_ear:.3f} (th: {current_threshold:.3f})",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                f"Blinks: {blink_count}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            status = "EYES CLOSED" if is_eye_closed else "EYES OPEN"
            cv2.putText(
                frame,
                status,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255) if is_eye_closed else (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                "Face: DETECTED",
                (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
        else:
            cv2.putText(
                frame,
                "FACE NOT DETECTED - Look at camera",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
            cv2.putText(
                frame,
                f"Blinks: {blink_count}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        cv2.imshow("ConcussionSite - Webcam", frame)

        if flicker:
            flicker_display(flicker_window_name, frame_count)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Debug
    face_detection_rate = (face_detected_count / frame_count * 100) if frame_count > 0 else 0.0
    avg_ear_value = float(np.mean(ear_values)) if ear_values else 0.0
    min_ear_value = float(np.min(ear_values)) if ear_values else 0.0
    max_ear_value = float(np.max(ear_values)) if ear_values else 0.0

    print(f"\n[DEBUG {phase_name}]")
    print(f"  Frames: {frame_count}")
    print(f"  Face detected: {face_detected_count} ({face_detection_rate:.1f}%)")
    print(f"  EAR avg: {avg_ear_value:.3f}, min: {min_ear_value:.3f}, max: {max_ear_value:.3f}")
    print(f"  Blinks: {blink_count}")

    return {
        "blink_count": blink_count,
        "eye_closed_time": eye_closed_time,
        "gaze_distances": gaze_distances,
        "duration": duration_sec,
        "face_detection_rate": face_detection_rate,
        "avg_ear": avg_ear_value
    }


# ============================================================
# SMOOTH PURSUIT DOT TEST
# ============================================================
def run_dot_pursuit(duration_sec, cap):
    """
    Vertical sinusoidal smooth pursuit test.

    Returns:
        {
          "variance": float,
          "sp_percent": float,
          "mean_error": float,
          "num_frames": int
        }
    """
    window = "Oculomotor Smooth Pursuit Test"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 800, 600)

    start_time = time.time()
    errors = []
    in_window_frames = 0
    total_frames = 0

    amplitude = 200      # vertical amplitude (px)
    frequency = 0.4      # Hz (within typical TBI literature range)
    center_y = 300
    dot_x = 400

    print("\n============================================================")
    print(f"Starting Smooth Pursuit Phase ({duration_sec} seconds)")
    print("Follow the moving dot with your eyes, keep your head still.")
    print("============================================================")

    while time.time() - start_time < duration_sec:
        ret, frame = cap.read()
        if not ret:
            break

        # Compute dot position in 800x600
        t = time.time() - start_time
        dot_y = int(center_y + amplitude * math.sin(2 * math.pi * frequency * t))

        stim = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.circle(stim, (dot_x, dot_y), 15, (255, 255, 255), -1)

        cv2.putText(
            stim,
            "Follow the dot with your eyes",
            (150, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (200, 200, 200),
            2
        )

        cv2.imshow(window, stim)

        # Estimate gaze in 800x600 coordinates
        gaze = estimate_gaze_point(frame)
        if gaze is not None:
            gx, gy = gaze
            err = float(np.linalg.norm(np.array([gx - dot_x, gy - dot_y])))
            errors.append(err)

            if err < 80:  # within tolerance window
                in_window_frames += 1

        total_frames += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    variance = float(np.std(errors)) if errors else 999.0
    mean_error = float(np.mean(errors)) if errors else 999.0
    sp_percent = (in_window_frames / total_frames) if total_frames > 0 else 0.0

    print("\n[DEBUG Smooth Pursuit]")
    print(f"  Frames: {total_frames}")
    print(f"  Mean error: {mean_error:.1f} px")
    print(f"  Error variance: {variance:.1f}")
    print(f"  SP% (within window): {sp_percent*100:.1f}%")

    return {
        "variance": variance,
        "sp_percent": sp_percent,
        "mean_error": mean_error,
        "num_frames": total_frames
    }


# ============================================================
# SYMPTOM SURVEY
# ============================================================
def ask_symptoms():
    """Simple yes/no symptom questions."""
    print("\n" + "=" * 50)
    print("Symptom Questionnaire")
    print("=" * 50)

    symptoms = {
        "headache": "Do you have a headache? (y/n): ",
        "nausea": "Do you feel nauseous? (y/n): ",
        "dizziness": "Do you feel dizzy? (y/n): ",
        "light_sensitivity": "Are you sensitive to light? (y/n): "
    }

    answers = {}
    for key, question in symptoms.items():
        while True:
            ans = input(question).strip().lower()
            if ans in ["y", "yes", "n", "no"]:
                answers[key] = ans in ["y", "yes"]
                break
            print("Please enter 'y' or 'n'.")
    return answers


# ============================================================
# METRICS + RISK
# ============================================================
def calculate_metrics(baseline_metrics, flicker_metrics):
    """Summarize blink/gaze metrics from baseline + flicker."""
    baseline_duration = baseline_metrics["duration"]
    flicker_duration = flicker_metrics["duration"]

    # Blink rate (blinks/min)
    baseline_blink_rate = (baseline_metrics["blink_count"] / baseline_duration) * 60
    flicker_blink_rate = (flicker_metrics["blink_count"] / flicker_duration) * 60
    blink_rate_delta = flicker_blink_rate - baseline_blink_rate

    # Eye-closed fraction
    total_closed_time = baseline_metrics["eye_closed_time"] + flicker_metrics["eye_closed_time"]
    total_duration = baseline_duration + flicker_duration
    eye_closed_fraction = total_closed_time / total_duration if total_duration > 0 else 0.0

    # Gaze off-center fraction using a threshold
    if len(baseline_metrics["gaze_distances"]) > 0:
        avg_gaze_baseline = np.mean(baseline_metrics["gaze_distances"])
        std_gaze_baseline = np.std(baseline_metrics["gaze_distances"])
        gaze_threshold = avg_gaze_baseline + 2 * std_gaze_baseline
        gaze_threshold = max(gaze_threshold, 100.0)
    else:
        gaze_threshold = 100.0

    baseline_gaze_off = sum(1 for d in baseline_metrics["gaze_distances"] if d > gaze_threshold)
    flicker_gaze_off = sum(1 for d in flicker_metrics["gaze_distances"] if d > gaze_threshold)
    total_gaze_measurements = len(baseline_metrics["gaze_distances"]) + len(flicker_metrics["gaze_distances"])
    gaze_off_fraction = (baseline_gaze_off + flicker_gaze_off) / total_gaze_measurements if total_gaze_measurements > 0 else 0.0

    return {
        "baseline_blink_rate": baseline_blink_rate,
        "flicker_blink_rate": flicker_blink_rate,
        "blink_rate_delta": blink_rate_delta,
        "eye_closed_fraction": eye_closed_fraction,
        "gaze_off_fraction": gaze_off_fraction
    }


def assess_concussion_risk(metrics, symptoms, pursuit_metrics=None):
    """
    Combine:
      - Blink metrics
      - Eye-closed time
      - Gaze aversion
      - Smooth pursuit metrics
      - Symptom burden

    to produce a simple risk score + level.
    """
    risk_score = 0
    risk_factors = []

    # Blink dynamics
    if metrics["baseline_blink_rate"] < 5:
        risk_factors.append("Very low baseline blink rate (possible measurement artifact).")
    elif metrics["flicker_blink_rate"] > metrics["baseline_blink_rate"] * 1.5:
        risk_score += 2
        risk_factors.append(f"Large blink rate increase during flicker ({metrics['blink_rate_delta']:.1f} blinks/min).")
    elif metrics["blink_rate_delta"] > 10:
        risk_score += 1
        risk_factors.append("Moderate blink rate increase during flicker.")

    # Eye-closed fraction (light avoidance)
    if metrics["eye_closed_fraction"] > 0.15:
        risk_score += 2
        risk_factors.append(f"High eye-closure time ({metrics['eye_closed_fraction']:.1%}) – possible light avoidance.")
    elif metrics["eye_closed_fraction"] > 0.10:
        risk_score += 1
        risk_factors.append("Elevated eye-closure time during test.")

    # Gaze aversion
    if metrics["gaze_off_fraction"] > 0.50:
        risk_score += 2
        risk_factors.append(f"Frequent gaze aversion ({metrics['gaze_off_fraction']:.1%}) – often looking away from stimulus.")
    elif metrics["gaze_off_fraction"] > 0.30:
        risk_score += 1
        risk_factors.append("Moderate gaze aversion detected.")

    # Smooth pursuit (if available)
    if pursuit_metrics is not None:
        if pursuit_metrics["sp_percent"] < 0.6:
            risk_score += 2
            risk_factors.append(f"Poor smooth pursuit (% within window = {pursuit_metrics['sp_percent']*100:.1f}%).")
        elif pursuit_metrics["sp_percent"] < 0.75:
            risk_score += 1
            risk_factors.append(f"Borderline smooth pursuit tracking ({pursuit_metrics['sp_percent']*100:.1f}%).")

        if pursuit_metrics["variance"] > 150:
            risk_score += 1
            risk_factors.append(f"High pursuit error variance ({pursuit_metrics['variance']:.1f}).")

    # Symptoms
    symptom_count = sum([
        symptoms["headache"],
        symptoms["nausea"],
        symptoms["dizziness"],
        symptoms["light_sensitivity"]
    ])

    if symptom_count >= 3:
        risk_score += 3
        risk_factors.append(f"Multiple symptoms reported ({symptom_count}/4).")
    elif symptom_count == 2:
        risk_score += 2
        risk_factors.append("Some concussion-like symptoms reported.")
    elif symptom_count == 1:
        risk_score += 1
        risk_factors.append("One concussion-like symptom reported.")

    # Risk level mapping
    if risk_score >= 7:
        risk_level = "HIGH"
        recommendation = ("URGENT: Consult a healthcare professional as soon as possible. "
                          "Several objective signs AND symptoms suggest possible concussion-related issues.")
    elif risk_score >= 4:
        risk_level = "MODERATE"
        recommendation = ("RECOMMENDED: Seek medical evaluation. There are meaningful indicators of light sensitivity "
                          "and/or oculomotor dysfunction that could be concussion-related.")
    elif risk_score >= 2:
        risk_level = "LOW"
        recommendation = ("MONITOR: Mild indicators present. Monitor symptoms over time and seek care if they persist or worsen.")
    else:
        risk_level = "MINIMAL"
        recommendation = ("No strong indicators detected in this screening. This does NOT rule out concussion; "
                          "monitor how you feel and seek care if concerned.")

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "recommendation": recommendation
    }


# ============================================================
# GEMINI AI SUMMARY
# ============================================================
def generate_ai_summary_gemini(metrics, symptoms, risk_assessment, pursuit_metrics=None):
    """
    Use Gemini (free tier) to generate a short, patient-facing explanation.
    """
    if not GEMINI_API_KEY:
        print("\n⚠️  Gemini API key not configured. Skipping AI summary.")
        return None

    try:
        # Lightweight, cheaper model (good for free credits)
        model = genai.GenerativeModel("gemini-1.5-flash")

        pursuit_text = "Not performed."
        if pursuit_metrics is not None:
            pursuit_text = (
                f"Smooth pursuit mean error: {pursuit_metrics['mean_error']:.1f} px; "
                f"variance: {pursuit_metrics['variance']:.1f}; "
                f"SP% (within tracking window): {pursuit_metrics['sp_percent']*100:.1f}%."
            )

        prompt = f"""
You are a cautious, non-diagnostic medical screening assistant.

Summarize the following concussion-related light sensitivity and eye movement screening:

METRICS:
- Baseline blink rate: {metrics['baseline_blink_rate']:.2f} blinks/min
- Flicker blink rate: {metrics['flicker_blink_rate']:.2f} blinks/min
- Blink rate increase: {metrics['blink_rate_delta']:.2f} blinks/min
- Eye-closed fraction: {metrics['eye_closed_fraction']:.2%}
- Gaze-off-center fraction: {metrics['gaze_off_fraction']:.2%}

SMOOTH PURSUIT:
- {pursuit_text}

SYMPTOMS:
- Headache: {'Yes' if symptoms['headache'] else 'No'}
- Nausea: {'Yes' if symptoms['nausea'] else 'No'}
- Dizziness: {'Yes' if symptoms['dizziness'] else 'No'}
- Light sensitivity: {'Yes' if symptoms['light_sensitivity'] else 'No'}

RISK ASSESSMENT:
- Level: {risk_assessment['risk_level']}
- Score: {risk_assessment['risk_score']}/10

Write a concise (<150 words), plain-language summary that:
1. Explains what the patterns might suggest about light sensitivity or eye movement difficulties.
2. Clearly states that this is NOT a diagnosis.
3. Encourages seeing a healthcare professional if symptoms are significant or worsening.
4. Avoids giving definitive medical conclusions.
"""

        response = model.generate_content(prompt)
        text = response.text if hasattr(response, "text") else None
        if text:
            return text.strip()
        return None

    except Exception as e:
        print(f"\n⚠️  Error calling Gemini: {e}")
        return None


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("ConcussionSite - Light Sensitivity & Eye Movement Screening")
    print("=" * 60)
    print("\nThis tool screens for patterns that COULD be consistent with")
    print("concussion-related light sensitivity or oculomotor issues.")
    print("It is NOT a diagnostic tool.")
    print("\nPress 'q' during any visual phase to quit early.")
    input("\nPress Enter to start...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    flicker_window = create_flicker_window()

    try:
        # Baseline phase
        baseline_metrics = run_phase(cap, flicker_window, "Baseline", duration_sec=8, flicker=False)

        print("\nPreparing flicker test...")
        time.sleep(2)

        # Flicker phase
        flicker_metrics = run_phase(cap, flicker_window, "Flicker", duration_sec=15, flicker=True)

        # Smooth pursuit phase
        print("\nPreparing smooth pursuit test...")
        time.sleep(2)
        pursuit_metrics = run_dot_pursuit(duration_sec=12, cap=cap)

        # Combined metrics
        metrics = calculate_metrics(baseline_metrics, flicker_metrics)

        print("\n" + "=" * 50)
        print("SCREENING RESULTS")
        print("=" * 50)
        print(f"Baseline blink rate      : {metrics['baseline_blink_rate']:.2f} blinks/min")
        print(f"Flicker blink rate       : {metrics['flicker_blink_rate']:.2f} blinks/min")
        print(f"Blink rate increase      : {metrics['blink_rate_delta']:.2f} blinks/min")
        print(f"Eye-closed fraction      : {metrics['eye_closed_fraction']:.2%}")
        print(f"Gaze-off-center fraction : {metrics['gaze_off_fraction']:.2%}")
        print(f"Smooth pursuit mean error: {pursuit_metrics['mean_error']:.1f} px")
        print(f"Smooth pursuit variance  : {pursuit_metrics['variance']:.1f}")
        print(f"SP% (in tracking window) : {pursuit_metrics['sp_percent']*100:.1f}%")

        # Symptoms
        symptoms = ask_symptoms()

        # Risk assessment
        print("\n" + "=" * 50)
        print("CONCUSSION-LIKE RISK ASSESSMENT")
        print("=" * 50)
        risk_assessment = assess_concussion_risk(metrics, symptoms, pursuit_metrics)

        print(f"\n🔍 RISK LEVEL: {risk_assessment['risk_level']}")
        print(f"📊 Risk Score: {risk_assessment['risk_score']}/10")

        if risk_assessment["risk_factors"]:
            print("\n⚠️  Risk Factors Identified:")
            for i, factor in enumerate(risk_assessment["risk_factors"], 1):
                print(f"   {i}. {factor}")
        else:
            print("\n✓ No strong risk factors detected by this screening.")

        print(f"\n💡 Recommendation:")
        print(f"   {risk_assessment['recommendation']}")

        # Gemini summary
        print("\n" + "=" * 50)
        print("AI SUMMARY (Gemini)")
        print("=" * 50)
        ai_summary = generate_ai_summary_gemini(metrics, symptoms, risk_assessment, pursuit_metrics)
        if ai_summary:
            print(ai_summary)
        else:
            print("(AI summary unavailable – using local risk explanation only.)")

        print("\n" + "=" * 50)
        print("⚠️  IMPORTANT DISCLAIMER")
        print("=" * 50)
        print("This tool only screens for patterns that MIGHT be consistent")
        print("with concussion-related issues. It does NOT provide a diagnosis.")
        print("If you have symptoms or concerns, especially after a head injury,")
        print("please seek evaluation from a qualified healthcare professional.")
        print("=" * 50)

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
