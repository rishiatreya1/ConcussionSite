import cv2
import numpy as np
import time
import math
from tracking.gaze import estimate_gaze_point

def run_dot_pursuit(duration_sec, cap):
    win = "Smooth Pursuit Test"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 800, 600)

    print("\n" + "=" * 60)
    print(f"Starting Smooth Pursuit Phase ({duration_sec} seconds)")
    print("=" * 60)
    print("Follow the moving dot with your eyes, keep your head still.")

    start = time.time()
    errors = []
    inside = 0
    total = 0

    amp = 200
    freq = 0.4
    mid = 300
    dot_x = 400

    while time.time() - start < duration_sec:
        ret, frame = cap.read()
        if not ret:
            break

        t = time.time() - start
        dot_y = int(mid + amp * math.sin(2*math.pi*freq*t))

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
        
        cv2.imshow(win, stim)

        gaze = estimate_gaze_point(frame)
        if gaze:
            gx, gy = gaze
            err = np.linalg.norm([gx-dot_x, gy-dot_y])
            errors.append(err)
            if err < 80:
                inside += 1

        total += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    variance = float(np.std(errors)) if errors else 999.0
    mean_error = float(np.mean(errors)) if errors else 999.0
    sp_percent = (inside / total) if total > 0 else 0.0

    print("\n[DEBUG Smooth Pursuit]")
    print(f"  Frames: {total}")
    print(f"  Mean error: {mean_error:.1f} px")
    print(f"  Error variance: {variance:.1f}")
    print(f"  SP% (within window): {sp_percent*100:.1f}%")

    return {
        "variance": variance,
        "sp_percent": sp_percent,
        "mean_error": mean_error,
        "num_frames": total
    }
