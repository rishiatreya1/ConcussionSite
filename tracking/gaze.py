import numpy as np
import cv2
from .facemesh import face_mesh, LEFT_EYE_INDICES, RIGHT_EYE_INDICES


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
