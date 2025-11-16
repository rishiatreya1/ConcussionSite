"""
ADK setup and agent initialization for ConcussionSite.
Uses LiteLLM as wrapper for Gemini models.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

import litellm
from litellm import completion

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Model configuration
MODEL = "gemini/gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    litellm.set_verbose = True  # Enable verbose logging
    logger.info("LiteLLM configured with Gemini API key")
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")


def initialize_agent(
    agent_name: str,
    system_prompt: str,
    model: str = MODEL
) -> Dict[str, Any]:
    """
    Initialize an agent with system prompt and model.
    
    Args:
        agent_name: Name of the agent
        system_prompt: System prompt for the agent
        model: Model to use (default: gemini-2.5-flash)
    
    Returns:
        Agent configuration dictionary
    """
    logger.debug(f"Initializing agent: {agent_name}")
    logger.debug(f"Model: {model}")
    
    agent_config = {
        "name": agent_name,
        "model": model,
        "system_prompt": system_prompt,
        "temperature": 0.3,  # Lower for more consistent, shorter responses
        "max_tokens": 300  # Reduced for shorter responses
    }
    
    logger.info(f"Agent '{agent_name}' initialized successfully")
    return agent_config


def call_agent(
    agent_config: Dict[str, Any],
    user_message: str,
    conversation_history: Optional[list] = None
) -> str:
    """
    Call an agent with a user message.
    
    Args:
        agent_config: Agent configuration dictionary
        user_message: User's message
        conversation_history: Optional conversation history
    
    Returns:
        Agent's response text
    """
    logger.debug(f"Calling agent: {agent_config['name']}")
    logger.debug(f"User message: {user_message[:100]}...")
    
    try:
        # Build messages
        messages = []
        
        # Add system prompt
        messages.append({
            "role": "system",
            "content": agent_config["system_prompt"]
        })
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call LiteLLM
        response = completion(
            model=agent_config["model"],
            messages=messages,
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"]
        )
        
        # Extract response text
        if response and response.choices:
            response_text = response.choices[0].message.content
            logger.info(f"Agent '{agent_config['name']}' responded successfully")
            logger.debug(f"Response: {response_text[:100]}...")
            return response_text
        else:
            logger.error("No response from agent")
            return "I'm having trouble generating a response. Please try again."
    
    except Exception as e:
        error_msg = f"Error calling agent: {str(e)}"
        logger.error(error_msg)
        return f"I encountered an error: {error_msg}. Please try again."


def create_root_agent(system_prompt: str) -> Dict[str, Any]:
    """
    Create the root agent for ConcussionSite.
    
    Args:
        system_prompt: System prompt for root agent
    
    Returns:
        Root agent configuration
    """
    return initialize_agent(
        agent_name="concussion_care_root_agent",
        system_prompt=system_prompt,
        model=MODEL
    )

