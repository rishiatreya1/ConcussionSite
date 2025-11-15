import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️  GEMINI_API_KEY not found in .env – AI summaries will be skipped.")


def generate_summary(metrics, symptoms, risk_assessment, pursuit_metrics=None):
    """
    Use Gemini (free tier) to generate a short, patient-facing explanation.
    """
    if not GEMINI_API_KEY:
        print("\n⚠️  Gemini API key not configured. Skipping AI summary.")
        return None

    try:
        # Use gemini-2.0-flash (newer, faster, free tier friendly)
        # Falls back to gemini-1.5-flash if not available
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
        except:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
            except:
                model = genai.GenerativeModel("gemini-pro")

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
        error_msg = str(e)
        print(f"\n⚠️  Error calling Gemini: {error_msg}")
        if "API key" in error_msg or "401" in error_msg or "403" in error_msg:
            print("   → Check that your GEMINI_API_KEY in .env is correct and active.")
        elif "quota" in error_msg.lower() or "429" in error_msg:
            print("   → Gemini API quota/rate limit reached. Please try again later.")
        elif "safety" in error_msg.lower():
            print("   → Content was blocked by Gemini safety filters. Try again.")
        else:
            print("   → Check your internet connection and API key configuration.")
        return None
