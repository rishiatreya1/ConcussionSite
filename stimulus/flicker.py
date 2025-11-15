import cv2
import numpy as np

def create_flicker_window():
    w = "Light Sensitivity Test"
    cv2.namedWindow(w, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(w, 800, 600)
    return w

def flicker_display(win, frame_count, rate=10):
    white = ((frame_count // rate) % 2 == 0)
    stim = np.full((600, 800, 3), 255 if white else 0, dtype=np.uint8)
    cv2.putText(stim, "Keep looking", (260, 300),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (150,150,150) if white else (255,255,255), 2)
    cv2.imshow(win, stim)
