import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
KEY = os.getenv("GEMINI_API_KEY")

if KEY:
    genai.configure(api_key=KEY)

def generate_summary(metrics, symptoms, risk, pursuit):
    if not KEY:
        return None

    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Summarize this non-diagnostic concussion screening:

Blink:
- Baseline: {metrics['baseline_blink_rate']:.1f}
- Flicker: {metrics['flicker_blink_rate']:.1f}
- Delta: {metrics['blink_rate_delta']:.1f}

Eye closure fraction: {metrics['eye_closed_fraction']:.2%}
Gaze-off fraction: {metrics['gaze_off_fraction']:.2%}

Smooth pursuit:
- Mean error: {pursuit['mean_error']:.1f}
- Tracking %: {pursuit['sp_percent']*100:.1f}%

Symptoms: {symptoms}

Risk: {risk['risk_level']} ({risk['risk_score']}/10)

Write a short, cautious explanation (<150 words).
"""

    try:
        resp = model.generate_content(prompt)
        return resp.text
    except:
        return None
