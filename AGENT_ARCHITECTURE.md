# ConcussionSite Multi-Agent Architecture

## 📋 Implementation Summary

The ConcussionSite project has been restructured into a clean, modular, multi-agent conversational system using Google ADK patterns, LiteLLM, and Gemini models.

## 🏗️ Architecture Overview

### Agent Hierarchy

```
Root Agent (concussion_care_root_agent)
│
├── Question Agent Functions (tools.py)
│   ├── explain_metric()
│   ├── ask_followup_question()
│   └── simplify_results()
│
└── Writing Agent Functions (tools.py)
    ├── draft_email_for_mckinley()
    └── send_email_oauth()
```

### File Structure

```
agents/
├── __init__.py          # Package initialization
├── root_agent.py        # Root agent class (conversation manager)
├── tools.py             # All tool functions
├── prompt.py            # System prompts and templates
├── setup.py             # LiteLLM wrapper and agent initialization
└── runner.py            # Flask web UI runner

email_service/
├── __init__.py          # Package initialization
├── email_service.py     # Gmail OAuth service
└── GMAIL_SETUP.md       # OAuth setup instructions
```

## 🔄 Data Flow

```
1. main.py
   ├── Runs screening tests (baseline, flicker, pursuit)
   ├── Calculates metrics
   ├── Asks for subjective_score (1-10)
   ├── Asks symptom questions
   └── Calculates risk_assessment

2. agents/runner.py → start_conversation()
   ├── Receives: metrics, pursuit_metrics, symptoms, subjective_score, risk_assessment
   ├── Initializes RootAgent
   └── Launches Flask web UI (http://localhost:5000)

3. Root Agent (root_agent.py)
   ├── Builds context from screening data
   ├── Initializes with system prompt
   ├── Manages conversation loop
   ├── Processes user messages
   ├── Calls tools as needed
   └── Maintains conversation history

4. Tools (tools.py)
   ├── draft_email_for_mckinley() → Creates email draft
   ├── send_email_oauth() → Sends via Gmail API
   ├── explain_metric() → Explains metrics in plain language
   └── ask_followup_question() → Asks clarifying questions

5. Email Service (email_service/email_service.py)
   ├── Handles OAuth authentication
   ├── Creates MIME messages
   └── Sends via Gmail API
```

## 🎯 Key Features Implemented

### ✅ 1. Subjective Score Integration
- Added 1-10 feeling scale question in `main.py`
- Integrated into risk assessment calculation
- Affects risk score: 1-3 (+0), 4-6 (+1), 7-8 (+2), 9-10 (+3)

### ✅ 2. Root Agent
- Manages entire conversation flow
- Coordinates tool calls
- Maintains conversation history (last 20 messages)
- Handles escalation logic (risk_score >= 7)
- Enforces non-diagnostic behavior

### ✅ 3. Tool Functions
- **draft_email_for_mckinley()**: Creates professional email draft
- **send_email_oauth()**: Sends email via Gmail OAuth
- **explain_metric()**: Plain-language metric explanations
- **ask_followup_question()**: Supportive follow-up questions
- All tools have verbose logging for debugging

### ✅ 4. Web UI (Flask)
- Browser-based chat interface
- Real-time message exchange
- Email draft display
- Clean, modern design
- Responsive layout

### ✅ 5. Email Service
- Gmail OAuth 2.0 authentication
- Token management
- MIME message creation
- Error handling
- Setup instructions included

### ✅ 6. System Prompts
- Enforces non-diagnostic behavior
- UIUC-specific context
- Supportive, calm tone
- Clear escalation rules
- Safety-first approach

## 🔐 Security & Privacy

- OAuth credentials in `.gitignore`
- Environment variables for API keys
- No hardcoded secrets
- Secure token storage
- User consent for email sending

## 🚀 Usage

### Running Full System
```bash
python3 main.py
```

### Testing Agent System
```bash
python3 agents/runner.py
```
(Requires test data or modification)

## 📊 Agent Workflow

1. **Initialization**
   - Root agent receives screening data
   - Builds context string
   - Initializes with system prompt

2. **Greeting**
   - Agent generates personalized greeting
   - Mentions McKinley if risk_score >= 7
   - Offers to help

3. **Conversation Loop**
   - User sends message
   - Root agent processes intent
   - Checks for tool triggers
   - Generates response via Gemini
   - Updates conversation history

4. **Escalation (if risk_score >= 7)**
   - Agent offers to draft email
   - User confirms → email drafted
   - Email shown to user
   - User confirms → email sent
   - User declines → safety recommendations

5. **Session End**
   - User says "stop/exit/quit"
   - Graceful exit
   - Thank you message

## 🛠️ Extending the System

### Add New Tool
1. Add function to `agents/tools.py`
2. Add docstring and logging
3. Update `root_agent.py` to call tool
4. Test in conversation

### Modify Agent Behavior
1. Edit `agents/prompt.py`
2. Update `ROOT_AGENT_SYSTEM_PROMPT`
3. Restart system

### Add New Agent
1. Create new agent class in `agents/`
2. Follow `root_agent.py` pattern
3. Initialize with `agents/setup.py`
4. Integrate into conversation flow

## 📝 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for AI functionality

### Model Settings
- Model: `gemini/gemini-2.5-flash`
- Temperature: 0.7
- Max tokens: 1000

### Gmail OAuth
- Credentials: `email_service/credentials.json`
- Token: `email_service/token.json` (auto-generated)
- Scope: `gmail.send`

## ✅ Implementation Checklist

- [x] Subjective score question added
- [x] Risk assessment includes subjective_score
- [x] Root agent created
- [x] Tools module created
- [x] Prompts module created
- [x] Setup module created
- [x] Runner with web UI created
- [x] Email service with OAuth created
- [x] Gmail setup instructions created
- [x] main.py updated to use agent system
- [x] README.md updated
- [x] Quick start guide created
- [x] All files compile successfully

## 🎉 Ready to Use!

The system is fully implemented and ready for testing. Install dependencies and run `python3 main.py` to start!

