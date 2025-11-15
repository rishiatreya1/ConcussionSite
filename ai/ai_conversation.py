"""
Interactive conversational agent for ConcussionSite.
Uses Gemini to provide supportive, non-diagnostic guidance after screening.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def draft_mckinley_email(metrics, symptoms, risk_assessment, pursuit_metrics):
    """
    Draft an email template for McKinley Health Center referral.
    Returns a string the user can copy.
    """
    symptom_list = []
    if symptoms.get("headache"):
        symptom_list.append("headache")
    if symptoms.get("nausea"):
        symptom_list.append("nausea")
    if symptoms.get("dizziness"):
        symptom_list.append("dizziness")
    if symptoms.get("light_sensitivity"):
        symptom_list.append("light sensitivity")
    
    symptoms_text = ", ".join(symptom_list) if symptom_list else "none reported"
    
    email = f"""Subject: Request for Evaluation - Concussion Screening Results

Dear McKinley Health Center Staff,

I recently completed a vision-based concussion screening tool and would like to request an evaluation based on the results.

SYMPTOMS REPORTED:
- {symptoms_text}

SCREENING METRICS:
- Baseline blink rate: {metrics['baseline_blink_rate']:.2f} blinks/min
- Flicker blink rate: {metrics['flicker_blink_rate']:.2f} blinks/min
- Blink rate change: {metrics['blink_rate_delta']:.2f} blinks/min
- Eye-closed fraction: {metrics['eye_closed_fraction']:.2%}
- Gaze aversion: {metrics['gaze_off_fraction']:.2%}
- Smooth pursuit error: {pursuit_metrics.get('mean_error', 'N/A'):.1f} px

RISK ASSESSMENT:
- Level: {risk_assessment['risk_level']}
- Score: {risk_assessment['risk_score']}/10

I understand this screening tool is not a diagnostic device, but the results suggest some patterns that may warrant professional evaluation. I would appreciate the opportunity to discuss these findings with a healthcare provider.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your NetID]
[Your Contact Information]
"""
    return email


def start_conversation(metrics, symptoms, risk_assessment, pursuit_metrics):
    """
    Launches an interactive Gemini-driven conversation with the user.
    Returns when the user ends the session.
    """
    if not GEMINI_API_KEY:
        print("\n⚠️  Gemini API key not configured. Skipping interactive conversation.")
        print("Using standard summary instead.")
        return
    
    # Initialize model
    try:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
        except:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
            except:
                model = genai.GenerativeModel("gemini-pro")
    except Exception as e:
        print(f"\n⚠️  Error initializing Gemini: {e}")
        print("Skipping interactive conversation.")
        return
    
    # Build context for the assistant
    pursuit_text = "Not performed."
    if pursuit_metrics is not None:
        pursuit_text = (
            f"Mean error: {pursuit_metrics['mean_error']:.1f} px; "
            f"variance: {pursuit_metrics['variance']:.1f}; "
            f"tracking accuracy: {pursuit_metrics['sp_percent']*100:.1f}%"
        )
    
    symptom_list = []
    if symptoms.get("headache"):
        symptom_list.append("headache")
    if symptoms.get("nausea"):
        symptom_list.append("nausea")
    if symptoms.get("dizziness"):
        symptom_list.append("dizziness")
    if symptoms.get("light_sensitivity"):
        symptom_list.append("light sensitivity")
    
    symptoms_text = ", ".join(symptom_list) if symptom_list else "none"
    
    # System prompt with behavioral rules
    system_prompt = """You are ConcussionSite, a supportive, non-diagnostic assistant that helps UIUC students interpret their vision-based concussion screen.

CRITICAL RULES:
- You do NOT diagnose conditions
- You do NOT give medical commands
- You explain findings using plain language
- You help users understand what the numbers may suggest
- You use phrases like "patterns that may be consistent with..." not "you have..."
- You are calm, supportive, and non-alarming
- You follow the user's tone and respond appropriately
- If the user wants to stop (says "stop", "exit", "quit", "end session"), end immediately

REFERRAL LOGIC:
- If risk_score >= 7, gently encourage seeking help at McKinley Health Center at UIUC
- Offer to draft an email for them if they want
- The referral is always optional and supportive, never pushy
- Only suggest McKinley when risk_score >= 7

YOUR ROLE:
- Be educational and supportive
- Answer questions about the metrics
- Help interpret what the numbers might mean
- Guide next steps without being prescriptive
- Stay within your non-diagnostic scope"""
    
    # Initial context
    initial_context = f"""SCREENING RESULTS CONTEXT:

METRICS:
- Baseline blink rate: {metrics['baseline_blink_rate']:.2f} blinks/min
- Flicker blink rate: {metrics['flicker_blink_rate']:.2f} blinks/min
- Blink rate change: {metrics['blink_rate_delta']:.2f} blinks/min
- Eye-closed fraction: {metrics['eye_closed_fraction']:.2%}
- Gaze-off-center fraction: {metrics['gaze_off_fraction']:.2%}
- Smooth pursuit: {pursuit_text}

SYMPTOMS REPORTED:
- {symptoms_text}

RISK ASSESSMENT:
- Level: {risk_assessment['risk_level']}
- Score: {risk_assessment['risk_score']}/10

RISK FACTORS IDENTIFIED:
{chr(10).join(f"- {factor}" for factor in risk_assessment.get('risk_factors', []))}

RECOMMENDATION:
{risk_assessment.get('recommendation', 'No specific recommendation')}

IMPORTANT: This is NOT a diagnosis. The user has completed a screening tool only."""
    
    # Check if high risk for McKinley referral
    high_risk = risk_assessment.get("risk_score", 0) >= 7
    
    # Build initial message with system prompt and context
    mckinley_note = ""
    if high_risk:
        mckinley_note = "\n\nIMPORTANT: The user's risk score is 7 or higher. Gently mention that their results suggest meaningful concerns and that seeking evaluation at McKinley Health Center at UIUC could be helpful. Offer to draft an email for them if they're interested, but make it optional and supportive."
    
    initial_message = f"""{system_prompt}

{initial_context}{mckinley_note}

Now, greet the user and offer to help them understand their results. Be warm and supportive."""
    
    # Start conversation with initial greeting
    print("\n" + "=" * 60)
    print("INTERACTIVE ASSISTANT")
    print("=" * 60)
    
    # Get initial greeting from Gemini
    try:
        initial_response = model.generate_content(initial_message)
        if initial_response and initial_response.text:
            print(f"\n{initial_response.text.strip()}\n")
    except:
        print("\nYour screening is complete. I can help you understand your results,")
        print("answer questions, or guide your next steps.")
        if high_risk:
            print("\n⚠️  Based on your results, I'd like to discuss next steps with you.")
        print("\nWhat would you like to talk about?")
    
    print("(Type 'stop', 'exit', 'quit', or 'end session' to end the conversation)\n")
    
    # Conversation history for context
    conversation_history = []
    
    # Conversation loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit keywords
            exit_keywords = ["stop", "exit", "quit", "end session", "end", "done"]
            if user_input.lower() in exit_keywords:
                print("\n👋 Thank you for using ConcussionSite. Take care!")
                break
            
            # Special handling for McKinley email request
            if high_risk and any(keyword in user_input.lower() for keyword in ["email", "mckinley", "referral", "draft"]):
                if "yes" in user_input.lower() or "sure" in user_input.lower() or "ok" in user_input.lower() or "please" in user_input.lower():
                    print("\n" + "=" * 60)
                    print("MCKINLEY HEALTH CENTER EMAIL DRAFT")
                    print("=" * 60)
                    email = draft_mckinley_email(metrics, symptoms, risk_assessment, pursuit_metrics)
                    print("\n" + email)
                    print("\n" + "=" * 60)
                    print("You can copy the email above and send it to McKinley Health Center.")
                    print("Their email: healthcenter@illinois.edu")
                    print("Or visit: https://www.mckinley.illinois.edu/")
                    print("=" * 60 + "\n")
                    continue
            
            # Build context-aware prompt
            history_text = ""
            if conversation_history:
                history_lines = []
                for h in conversation_history[-5:]:
                    history_lines.append(f"User: {h['user']}")
                    history_lines.append(f"Assistant: {h['assistant']}")
                history_text = "\n".join(history_lines)
            else:
                history_text = "This is the start of the conversation."
            
            context_prompt = f"""{system_prompt}

{initial_context}

CONVERSATION HISTORY:
{history_text}

CURRENT USER MESSAGE: {user_input}

Respond naturally and helpfully. Remember: no diagnosing, be supportive, stay non-diagnostic."""
            
            # Generate response
            response = model.generate_content(context_prompt)
            
            if response and response.text:
                ai_response = response.text.strip()
                print(f"\nAssistant: {ai_response}\n")
                
                # Add to conversation history (keep last 10 exchanges)
                conversation_history.append({
                    "user": user_input,
                    "assistant": ai_response
                })
                if len(conversation_history) > 10:
                    conversation_history.pop(0)
            else:
                print("\n⚠️  I'm having trouble generating a response. Please try rephrasing your question.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Conversation ended. Take care!")
            break
        except Exception as e:
            error_msg = str(e)
            print(f"\n⚠️  Error: {error_msg}")
            
            if "quota" in error_msg.lower() or "429" in error_msg:
                print("   → API quota exceeded. Please try again later.")
                break
            elif "API key" in error_msg or "401" in error_msg or "403" in error_msg:
                print("   → API key issue. Check your configuration.")
                break
            else:
                print("   → Please try again or type 'stop' to end the conversation.\n")

