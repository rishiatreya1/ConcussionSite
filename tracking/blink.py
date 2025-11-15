import numpy as np

# EAR thresholds
EAR_BASE_THRESHOLD = 0.25
EAR_CONSECUTIVE_FRAMES = 2  # frames below threshold to count a blink


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


def get_adaptive_threshold(ear_values, base_threshold=EAR_BASE_THRESHOLD):
    """
    Calculate adaptive threshold based on recent EAR values.
    Uses 70% of baseline EAR if we have enough samples.
    """
    if len(ear_values) > 10:
        baseline_ear = np.mean(ear_values[-30:])  # Use last 30 frames
        adaptive_threshold = baseline_ear * 0.70  # 70% of baseline = closed
        return max(adaptive_threshold, 0.20)  # Minimum 0.20
    else:
        return base_threshold
