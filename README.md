# ConcussionSite

A light-sensitivity and eye-response screening tool for potential concussion symptoms using only a laptop webcam.

## What is ConcussionSite?

ConcussionSite is a non-invasive screening tool that uses computer vision and AI to assess potential light sensitivity and eye-response patterns that may be associated with concussion. The tool tracks eye movements, blink rates, and gaze patterns during baseline and light-flicker conditions to identify potential indicators of visual stress.

**⚠️ IMPORTANT: This tool is NOT a diagnostic device. It is a screening tool only and should not replace professional medical evaluation.**

## How It Works

ConcussionSite follows a structured screening protocol:

1. **Baseline Phase (8 seconds)**: Records normal eye behavior while looking at the webcam
2. **Flicker Phase (15 seconds)**: Records eye behavior while exposed to a flickering light pattern
3. **Metrics Calculation**: Computes key indicators:
   - Baseline blink rate (blinks per minute)
   - Flicker blink rate (blinks per minute)
   - Blink rate delta (increase during flicker)
   - Eye-closed fraction (percentage of time eyes were closed)
   - Gaze-off-center fraction (percentage of time gaze was averted)
4. **Symptom Questionnaire**: Asks about headache, nausea, dizziness, and light sensitivity
5. **AI Summary**: Generates a concise assessment using GPT-4o-mini, explaining whether elevated light sensitivity is indicated and whether results are mild or potentially concerning

## Scientific Backing

ConcussionSite is based on established research in concussion assessment and eye-tracking:

### Visually-Evoked Effects After Concussion
- **Clark et al., 2021**: Research demonstrating that visually-evoked effects correlate with concussion symptoms. Visual stress testing can reveal subtle neurological changes following mild traumatic brain injury (mTBI).

### Blink Rate and Visual Stress
- Multiple studies have shown that blink rate increases under visual stress in individuals with mTBI. The flicker phase of ConcussionSite specifically tests this response, as increased blinking during visual stimulation may indicate light sensitivity.

### Oculomotor Dysfunction in mTBI
- Research has consistently documented eye movement dysfunction after concussion, including:
  - Abnormal gaze patterns
  - Difficulty maintaining visual fixation
  - Increased sensitivity to visual stimuli
  - These findings support the use of gaze-aversion detection as a screening metric.

### EAR Blink Detection
- **Soukupová & Čech, 2016**: "Real-Time Eye Blink Detection using Facial Landmarks" - The Eye Aspect Ratio (EAR) method provides reliable, real-time blink detection using facial landmark tracking. ConcussionSite implements EAR with a threshold of 0.25 to detect eye closures.

### MediaPipe FaceMesh
- Google's MediaPipe FaceMesh provides 468 facial landmarks with high accuracy and real-time performance. The system has been validated for facial landmark detection and is suitable for eye-tracking applications.

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_key_here
   ```
   Get your API key from [Google AI Studio](https://aistudio.google.com/)
   
4. (Optional) Set up Gmail OAuth for email sending:
   - Follow instructions in `email_service/GMAIL_SETUP.md`
   - Place `credentials.json` in the `email_service/` directory

Tip. Do this through your virtual env
     ```
     python3 -m venv venv
     ```
     - Set venv
     ```
     source venv/bin/activate
     ```
     - Install
     ```
     pip3 install -r requirements.txt
     ```

## Usage

### Running the Full System

Run the complete screening with AI assistant:
```bash
python3 main.py
```

This will:
1. Run baseline eye tracking (8 seconds)
2. Run flicker sensitivity test (15 seconds)
3. Run smooth pursuit test (12 seconds)
4. Ask for subjective feeling score (1-10)
5. Ask symptom questions
6. Calculate risk assessment
7. **Launch web-based AI assistant** (opens in browser at http://localhost:5000)

### Running Agent System Directly

To test the agent system independently:
```bash
python3 agents/runner.py
```
(Note: You'll need to provide test data or modify the runner to include test metrics)

### Follow the On-Screen Instructions

- Look at the webcam during the baseline phase
- Try to keep looking at the flicker window during the flicker phase
- Follow the moving dot during smooth pursuit test
- Answer the subjective feeling question (1-10 scale)
- Answer symptom questions (y/n)
- **Interact with the AI assistant in your web browser**

Press 'q' during visual tests to quit early.

## Technical Details

### Core Screening Components
- **Webcam Capture**: Uses OpenCV for real-time video capture
- **Face Tracking**: MediaPipe FaceMesh with 468 landmarks
- **Blink Detection**: EAR (Eye Aspect Ratio) algorithm with adaptive thresholds
- **Gaze Tracking**: Distance-based calculation from image center
- **Smooth Pursuit**: Vertical sinusoidal dot tracking test

### Multi-Agent System Architecture

ConcussionSite uses a hierarchical multi-agent system:

```
Root Agent (concussion_care_root_agent)
├── Question Agent (tool functions)
│   ├── explain_metric()
│   ├── ask_followup_question()
│   └── simplify_results()
└── Writing Agent (tool functions)
    ├── draft_email_for_mckinley()
    └── send_email_oauth()
```

**Components:**
- **Root Agent** (`agents/root_agent.py`): Manages conversation flow, coordinates tools
- **Tools** (`agents/tools.py`): Modular functions for email drafting, explanations, questions
- **Prompts** (`agents/prompt.py`): System prompts and templates
- **Setup** (`agents/setup.py`): LiteLLM wrapper for Gemini models
- **Runner** (`agents/runner.py`): Flask web UI for browser-based interaction
- **Email Service** (`email_service/email_service.py`): Gmail OAuth integration

**AI Stack:**
- **LiteLLM**: Wrapper for multiple LLM providers
- **Gemini 2.5 Flash**: Primary model (fast, cost-effective)
- **Flask**: Web UI framework
- **Gmail API**: OAuth email sending

### Data Flow

```
main.py
  ↓
Screening Tests (baseline, flicker, pursuit)
  ↓
Metrics Calculation
  ↓
Risk Assessment (includes subjective_score)
  ↓
agents/runner.py → start_conversation()
  ↓
Root Agent initialized with context
  ↓
Web UI launched (Flask)
  ↓
User interacts via browser
  ↓
Root Agent processes messages
  ↓
Tools called as needed (email, explanations)
  ↓
Conversation continues until user ends session
```

## Multi-Agent System Guide

### How to Extend Agents

1. **Add New Tools**: Edit `agents/tools.py`
   ```python
   def my_new_tool(param1, param2):
       """Tool description."""
       logger.debug("my_new_tool called")
       # Your logic here
       return result
   ```

2. **Modify Agent Behavior**: Edit `agents/prompt.py`
   - Update `ROOT_AGENT_SYSTEM_PROMPT` to change agent personality
   - Add new templates for specific use cases

3. **Add New Agents**: Create new agent class in `agents/`
   - Follow the pattern in `root_agent.py`
   - Initialize with `agents/setup.py`
   - Integrate into conversation flow

### How to Add More Tools

1. Define function in `agents/tools.py`
2. Add docstring explaining what it does
3. Add logging for debugging
4. Update `root_agent.py` to call the tool when appropriate
5. Test the tool in conversation

### Agent Workflow

1. **Initialization**: Root agent receives screening data
2. **Greeting**: Agent greets user with personalized message
3. **Conversation Loop**:
   - User sends message
   - Root agent processes intent
   - Tool calls triggered if needed
   - Response generated via Gemini
   - History maintained for context
4. **Escalation**: If risk_score >= 7, agent offers email drafting
5. **Email Flow**:
   - Agent drafts email
   - Shows draft to user
   - Asks for confirmation
   - Sends via Gmail OAuth (if confirmed)
6. **Session End**: User says "stop/exit/quit" → graceful exit

### Configuration

**Environment Variables** (`.env`):
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Model Configuration** (`agents/setup.py`):
- Default model: `gemini/gemini-2.5-flash`
- Temperature: 0.7 (balanced)
- Max tokens: 1000

**Gmail OAuth** (`email_service/`):
- See `email_service/GMAIL_SETUP.md` for setup instructions
- Credentials stored in `email_service/credentials.json` (not in git)
- Token stored in `email_service/token.json` (auto-generated)

## Future Enhancements

The `stimulus/` directory is reserved for future integration with TouchDesigner visual stimuli, which will replace the current grayscale flicker pattern with more sophisticated visual tests.

## Disclaimer

**This tool is for screening purposes only and does not provide medical diagnosis.** 

- ConcussionSite cannot replace professional medical evaluation
- Results should be interpreted by qualified healthcare professionals
- If you have concerns about a potential concussion, seek immediate medical attention
- This tool is not FDA-approved or certified for medical diagnosis

## References

- Clark, J. F., et al. (2021). Visually-evoked effects in concussion assessment.
- Soukupová, T., & Čech, J. (2016). Real-Time Eye Blink Detection using Facial Landmarks. *21st Computer Vision Winter Workshop*.
- MediaPipe FaceMesh: https://google.github.io/mediapipe/solutions/face_mesh.html
- Research on blink rate and visual stress in mTBI
- Studies on oculomotor dysfunction following concussion

## License

This project is provided as-is for educational and screening purposes.

