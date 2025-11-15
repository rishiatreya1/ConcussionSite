import numpy as np


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
