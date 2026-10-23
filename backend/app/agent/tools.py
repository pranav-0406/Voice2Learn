"""Tool definitions and parser for the Voice2Learn Browser Agent."""

from __future__ import annotations

import json
from typing import Any

from app.agent.schemas import ActionType, AgentAction


AGENT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "resolve_curriculum",
            "description": (
                "Query the Class 6 curriculum database to resolve a subject, unit/chapter number, "
                "or topic title into a valid concept ID and target URL. Always use this tool when the "
                "user mentions a subject or unit (e.g. 'Science Unit 2') before attempting to navigate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Subject name or alias: 'science', 'math', 'english', 'social science'",
                    },
                    "unit_number": {
                        "type": "integer",
                        "description": "Unit or chapter number (e.g. 1, 2, 3)",
                    },
                    "topic_query": {
                        "type": "string",
                        "description": "Optional topic title or search term",
                    },
                },
                "required": ["subject"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate the browser to an internal application URL (e.g. '/concept/sci-ch02-c01', '/dashboard', '/quiz', '/quiz?subject=english').",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Internal route path to navigate to",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Explanation of why we are navigating to this page",
                    },
                },
                "required": ["url", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": "Click an interactive element (button, card, tab, link) on the current browser page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector or element ID (e.g. '#btn-continue-lesson', '#quick-ask-voice')",
                    },
                    "element_text": {
                        "type": "string",
                        "description": "Visible text or label on the element",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why we are clicking this element",
                    },
                },
                "required": ["selector", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll_page",
            "description": "Scroll the page to view content that is currently off-screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "description": "Direction to scroll",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why scrolling is necessary",
                    },
                },
                "required": ["direction", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_aloud",
            "description": "Read the current concept summary or question aloud using browser speech synthesis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text or concept to read aloud to the student",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this text is being read",
                    },
                },
                "required": ["text", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Signal that the requested task has been completed and speak the closing message to the student.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Friendly, spoken confirmation message for the Class 6 student",
                    },
                    "success": {
                        "type": "boolean",
                        "description": "True if the user's goal was successfully achieved",
                    },
                },
                "required": ["message", "success"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_clarification",
            "description": "Ask the student a clarifying question when their prompt is ambiguous or refers to an invalid unit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Clear and encouraging question to ask the student",
                    },
                },
                "required": ["question"],
            },
        },
    },
]


def parse_tool_call(tool_name: str, arguments_str: str) -> AgentAction:
    """Parse tool call arguments into a typed AgentAction."""
    try:
        args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
    except Exception:
        args = {}

    if tool_name == "navigate":
        return AgentAction(
            action_type=ActionType.NAVIGATE,
            thought=args.get("reason", "Navigating to page"),
            target_url=args.get("url"),
        )
    elif tool_name == "click_element":
        return AgentAction(
            action_type=ActionType.CLICK,
            thought=args.get("reason", "Clicking element"),
            selector=args.get("selector"),
            element_text=args.get("element_text"),
        )
    elif tool_name == "scroll_page":
        return AgentAction(
            action_type=ActionType.SCROLL,
            thought=args.get("reason", "Scrolling page"),
            scroll_direction=args.get("direction", "down"),
        )
    elif tool_name == "read_aloud":
        return AgentAction(
            action_type=ActionType.READ_ALOUD,
            thought=args.get("reason", "Reading aloud"),
            text_to_speak=args.get("text"),
        )
    elif tool_name == "complete_task":
        return AgentAction(
            action_type=ActionType.COMPLETE_TASK,
            thought="Task finished",
            message=args.get("message"),
            success=args.get("success", True),
        )
    elif tool_name == "ask_clarification":
        return AgentAction(
            action_type=ActionType.ASK_CLARIFICATION,
            thought="Needs clarification from student",
            message=args.get("question"),
            success=False,
        )
    else:
        return AgentAction(
            action_type=ActionType.COMPLETE_TASK,
            thought=f"Unknown tool: {tool_name}",
            message="I am not sure how to perform that action yet.",
            success=False,
        )
