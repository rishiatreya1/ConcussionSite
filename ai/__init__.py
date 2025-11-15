"""AI module for generating summaries and interactive conversations using Gemini."""
from .gemini_summary import generate_summary
from .ai_conversation import start_conversation

__all__ = ['generate_summary', 'start_conversation']
