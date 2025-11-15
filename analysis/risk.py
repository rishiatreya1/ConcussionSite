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
