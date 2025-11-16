# ConcussionSite Multi-Agent System - Quick Start Guide

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create `.env` file in project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key from: https://aistudio.google.com/

### 3. (Optional) Set Up Gmail OAuth

For email sending functionality:
1. Follow instructions in `email_service/GMAIL_SETUP.md`
2. Download OAuth credentials from Google Cloud Console
3. Place `credentials.json` in `email_service/` directory

### 4. Run the System

```bash
python3 main.py
```

This will:
1. Run all screening tests
2. Ask for subjective score (1-10)
3. Ask symptom questions
4. **Launch web UI** at http://localhost:5000
5. Open your browser automatically

## 📁 Project Structure

```
ConcussionSite/
├── main.py                 # Main entry point
├── agents/                 # Multi-agent system
│   ├── root_agent.py      # Root agent (conversation manager)
│   ├── tools.py           # Tool functions
│   ├── prompt.py          # System prompts
│   ├── setup.py           # LiteLLM setup
│   └── runner.py          # Web UI runner
├── email_service/          # Email service
│   ├── email_service.py   # Gmail OAuth
│   └── GMAIL_SETUP.md     # Setup instructions
├── tracking/              # Eye tracking
├── analysis/              # Metrics & risk assessment
└── stimulus/              # Visual tests
```

## 🎯 How It Works

### Data Flow

1. **Screening** → `main.py` runs tests
2. **Metrics** → Calculated from test results
3. **Risk Assessment** → Includes subjective_score
4. **Agent System** → `agents/runner.py` launches web UI
5. **Root Agent** → Manages conversation
6. **Tools** → Called as needed (email, explanations)
7. **User Interaction** → Via browser at localhost:5000

### Agent Hierarchy

```
Root Agent
  ├── Question Agent (tools)
  │   └── explain_metric(), ask_followup_question()
  └── Writing Agent (tools)
      └── draft_email_for_mckinley(), send_email_oauth()
```

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "GEMINI_API_KEY not found"
- Check `.env` file exists
- Verify key is correct (starts with "AIza")
- Get new key from https://aistudio.google.com/

### "Gmail OAuth error"
- Follow `email_service/GMAIL_SETUP.md` instructions
- Make sure `credentials.json` is in `email_service/` directory
- Check OAuth consent screen is configured

### Web UI not opening
- Check terminal for URL (should be http://localhost:5000)
- Manually open browser to that URL
- Check if port 5000 is already in use

## 📝 Key Features

✅ **Multi-Agent System**: Hierarchical agent architecture
✅ **Web UI**: Browser-based chat interface
✅ **Email Integration**: Gmail OAuth for referrals
✅ **Tool-Based**: Modular, extensible tools
✅ **Context-Aware**: Maintains conversation history
✅ **Risk-Based Escalation**: Automatic McKinley referral for high risk
✅ **Non-Diagnostic**: Enforces safety rules

## 🎓 Next Steps

- Read `README.md` for full documentation
- Check `IMPROVEMENTS.md` for enhancement ideas
- Review `agents/prompt.py` to customize agent behavior
- Add new tools in `agents/tools.py`

