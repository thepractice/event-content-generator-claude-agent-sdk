"""BrandGuard Agent - Claude Agent SDK client with hooks.

This module provides the agent integration using the Claude Agent SDK.
It includes PreToolUse guards and PostToolUse audit logging.

Note: The claude-agent-sdk package may not be available yet.
This implementation follows the expected API based on documentation.
Falls back to direct Anthropic API if SDK is not available.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import Claude Agent SDK, fall back to direct API
try:
    from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher
    USING_SDK = True
except ImportError:
    USING_SDK = False
    import anthropic

from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Audit Log (Global for hook access)
# ============================================================================

audit_log: Dict[str, Any] = {
    "started_at": None,
    "completed_at": None,
    "tool_calls": [],
    "blocked_tools": [],
}


def reset_audit_log():
    """Reset the audit log for a new run."""
    global audit_log
    audit_log = {
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "tool_calls": [],
        "blocked_tools": [],
    }


# ============================================================================
# Hooks
# ============================================================================

# Tools that are blocked entirely
BLOCKED_TOOLS = ["Bash", "Edit", "WebFetch"]

# Keywords that allow WebSearch
WEBSEARCH_ALLOWED_KEYWORDS = ["trend", "hashtag", "popular", "trending"]


async def guard_tools(input_data: Dict[str, Any], tool_use_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """PreToolUse hook: Guard against unwanted tool usage.

    Blocks:
    - Bash, Edit, WebFetch entirely
    - WebSearch unless query contains trend/hashtag keywords
    """
    tool_name = input_data.get("tool_name", "")

    # Block dangerous tools
    if tool_name in BLOCKED_TOOLS:
        audit_log["blocked_tools"].append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "reason": "Tool not allowed for this agent",
        })
        return {
            "decision": "block",
            "message": f"Tool {tool_name} is not allowed. Use the designated MCP tools instead.",
        }

    # Guard WebSearch - only for trends/hashtags
    if tool_name == "WebSearch":
        tool_input = input_data.get("tool_input", {})
        query = tool_input.get("query", "").lower()

        if not any(kw in query for kw in WEBSEARCH_ALLOWED_KEYWORDS):
            audit_log["blocked_tools"].append({
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "query": query,
                "reason": "WebSearch only allowed for trends/hashtags",
            })
            return {
                "decision": "block",
                "message": "WebSearch is only allowed for trends and hashtags, not factual claims. Use retrieve_context for factual information.",
            }

    return {}


async def log_tool_call(input_data: Dict[str, Any], tool_use_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """PostToolUse hook: Log every tool call for audit trail."""
    audit_log["tool_calls"].append({
        "timestamp": datetime.now().isoformat(),
        "tool": input_data.get("tool_name", "unknown"),
        "input_summary": str(input_data.get("tool_input", ""))[:200],
        "response_summary": str(input_data.get("tool_response", ""))[:200],
    })
    return {}


# ============================================================================
# Prompt Formatting
# ============================================================================

def format_prompt(event_brief: Dict[str, Any]) -> str:
    """Format the event brief into an agent prompt."""
    urls_text = "\n".join(
        f"- {u['label']}: {u['url']}"
        for u in event_brief.get("relevant_urls", [])
    )

    key_messages = "\n".join(
        f"- {m}"
        for m in event_brief.get("key_messages", [])
    )

    return f"""Generate marketing content for this event:

**Event:** {event_brief['event_title']}
**Description:** {event_brief['event_description']}
**Date:** {event_brief.get('event_date', 'TBD')}
**Target Audience:** {event_brief['target_audience']}

**Key Messages:**
{key_messages if key_messages else '(none provided)'}

**Channels to create:** {', '.join(event_brief['channels'])}

**URLs for CTAs:**
{urls_text if urls_text else '(none provided)'}

Follow your skills in .claude/skills/ and use your MCP tools to:
1. Retrieve context from the knowledge base
2. Draft content for each channel
3. Critique each draft and revise if needed
4. Verify all claims have source citations
5. Generate images for each channel
6. Save final output to output/bundle.json

Quality standards:
- Brand voice score >= 7
- CTA clarity score >= 7
- All claims must be verified
- Content within channel limits

Begin by reading your skills and retrieving relevant context."""


# ============================================================================
# Agent Execution (SDK Version)
# ============================================================================

async def run_brandguard_sdk(event_brief: Dict[str, Any]) -> Dict[str, Any]:
    """Run the BrandGuard agent using Claude Agent SDK.

    This is the preferred method when the SDK is available.
    """
    reset_audit_log()

    prompt = format_prompt(event_brief)

    # Configure agent options
    options = ClaudeAgentOptions(
        # Built-in tools (guarded by hooks)
        allowed_tools=["Write", "Read", "WebSearch"],

        # Connect to MCP server
        mcp_servers={
            "brandguard": {
                "command": "python",
                "args": ["mcp/server.py"],
            }
        },

        # Load skills from filesystem
        setting_sources=["project"],

        # No permission prompts (automated)
        permission_mode="bypassPermissions",

        # Hooks for guard and audit
        hooks={
            "PreToolUse": [HookMatcher(matcher=".*", hooks=[guard_tools])],
            "PostToolUse": [HookMatcher(matcher=".*", hooks=[log_tool_call])],
        },
    )

    # Run agent
    messages = []
    final_result = None

    try:
        async for message in query(prompt=prompt, options=options):
            messages.append(message)

            # Capture final result
            if hasattr(message, "result"):
                final_result = message.result

            # Log text output
            if hasattr(message, "text"):
                print(f"Agent: {message.text[:100]}...")

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "audit_log": audit_log,
            "error": str(e),
        }

    audit_log["completed_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "result": final_result,
        "audit_log": audit_log,
        "message_count": len(messages),
    }


# ============================================================================
# Agent Execution (Fallback - Direct Anthropic API)
# ============================================================================

# Tool definitions for direct API
TOOLS = [
    {
        "name": "retrieve_context",
        "description": "Search the knowledge base for relevant information. Use 'brand' for voice/tone examples, 'product' for facts and features.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
                "context_type": {"type": "string", "enum": ["brand", "product"]}
            },
            "required": ["query", "context_type"]
        }
    },
    {
        "name": "critique_draft",
        "description": "Evaluate a piece of content against quality standards. Returns scores and specific feedback.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "enum": ["linkedin", "facebook", "email", "web"]},
                "headline": {"type": "string"},
                "body": {"type": "string"},
                "cta": {"type": "string"},
                "claims": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["channel", "body", "cta", "claims"]
        }
    },
    {
        "name": "verify_claims",
        "description": "Check whether factual claims can be traced to source documents. Unsupported claims should be removed or softened.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claims": {"type": "array", "items": {"type": "string"}},
                "source_chunk_ids": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["claims", "source_chunk_ids"]
        }
    },
    {
        "name": "generate_images",
        "description": "Create marketing visuals for the content. Call this after content is finalized.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channels": {"type": "array", "items": {"type": "string"}},
                "event_title": {"type": "string"},
                "visual_style": {"type": "string"}
            },
            "required": ["channels", "event_title"]
        }
    },
    {
        "name": "save_output",
        "description": "Save the final content bundle to output/bundle.json",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "object", "description": "Content per channel"},
                "scorecard": {"type": "object", "description": "Quality scores per channel"},
                "claims_table": {"type": "array", "description": "All claims with verification status"},
                "images": {"type": "object", "description": "Image paths per channel"}
            },
            "required": ["content", "scorecard", "claims_table"]
        }
    }
]

# System prompt for direct API
SYSTEM_PROMPT = """You are BrandGuard, an autonomous marketing content agent.

## YOUR MISSION

Generate high-quality, brand-safe marketing content for an event. Every factual claim must be traceable to a source document. Create matching visuals. Deliver a complete package.

## YOUR TOOLS

- retrieve_context: Search the knowledge base for brand voice or product info
- critique_draft: Score content quality (brand voice, CTA clarity, length)
- verify_claims: Check if claims are supported by source documents
- generate_images: Create marketing visuals with Gemini
- save_output: Save final bundle to output/bundle.json

## QUALITY STANDARDS

- Brand voice score >= 7
- CTA clarity score >= 7
- Length within channel limits (LinkedIn 3000, Facebook 500, Email 300 words, Web 50 words)
- ALL factual claims must have source citations

## WORKFLOW

1. Retrieve context (brand voice + product info) - SAVE THE CHUNK IDs
2. Draft content for each channel
3. Critique each draft - revise if scores < 7
4. Verify ALL claims using the chunk IDs
5. Remove/soften any unsupported claims
6. Generate images
7. Save final output

## CHANNEL LIMITS

- LinkedIn: 3000 chars
- Facebook: 500 chars
- Email: Subject 60 chars, body 300 words
- Web: Headline 10 words, hero 50 words

## IMPORTANT

- Think step by step
- Never submit unverified claims
- Iterate if quality scores are low
- Use the save_output tool when complete

Begin by retrieving context from the knowledge base."""


def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Any:
    """Execute a tool and return the result."""
    from mcp.server import retrieve_context, critique_draft, verify_claims, generate_images

    if tool_name == "retrieve_context":
        return retrieve_context(
            query=tool_input["query"],
            context_type=tool_input["context_type"]
        )
    elif tool_name == "critique_draft":
        return critique_draft(
            channel=tool_input["channel"],
            headline=tool_input.get("headline"),
            body=tool_input["body"],
            cta=tool_input["cta"],
            claims=tool_input.get("claims", [])
        )
    elif tool_name == "verify_claims":
        return verify_claims(
            claims=tool_input["claims"],
            source_chunk_ids=tool_input["source_chunk_ids"]
        )
    elif tool_name == "generate_images":
        return generate_images(
            channels=tool_input["channels"],
            event_title=tool_input["event_title"],
            visual_style=tool_input.get("visual_style", "modern, professional")
        )
    elif tool_name == "save_output":
        # Save to file
        output = {
            "event_title": tool_input.get("event_title", "Unknown Event"),
            "generated_at": datetime.now().isoformat(),
            "content": tool_input["content"],
            "scorecard": tool_input["scorecard"],
            "claims_table": tool_input["claims_table"],
            "images": tool_input.get("images", {}),
        }
        output_path = Path("output/bundle.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        return {"success": True, "path": str(output_path)}
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def run_brandguard_direct(event_brief: Dict[str, Any], max_turns: int = 30) -> Dict[str, Any]:
    """Run the BrandGuard agent using direct Anthropic API.

    Fallback when Claude Agent SDK is not available.
    """
    reset_audit_log()

    client = anthropic.Anthropic()
    prompt = format_prompt(event_brief)

    messages = [{"role": "user", "content": prompt}]

    for turn in range(max_turns):
        # Call Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Log the turn
        audit_log["tool_calls"].append({
            "turn": turn + 1,
            "timestamp": datetime.now().isoformat(),
            "stop_reason": response.stop_reason,
            "tools_called": [
                block.name for block in response.content
                if hasattr(block, "name")
            ]
        })

        # Check if done
        if response.stop_reason == "end_turn":
            audit_log["completed_at"] = datetime.now().isoformat()

            # Try to extract final result from last message
            final_result = None
            if Path("output/bundle.json").exists():
                with open("output/bundle.json") as f:
                    final_result = json.load(f)

            return {
                "success": True,
                "result": final_result,
                "audit_log": audit_log,
                "turns": turn + 1,
            }

        # Execute tool calls
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"Executing tool: {block.name}")

                    result = execute_tool(block.name, block.input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            # Add assistant response and tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    # Max turns reached
    audit_log["completed_at"] = datetime.now().isoformat()
    return {
        "success": False,
        "result": None,
        "audit_log": audit_log,
        "error": "Max turns exceeded",
    }


# ============================================================================
# Main Entry Point
# ============================================================================

async def run_brandguard(event_brief: Dict[str, Any]) -> Dict[str, Any]:
    """Run the BrandGuard agent.

    Uses Claude Agent SDK if available, falls back to direct API.
    """
    if USING_SDK:
        return await run_brandguard_sdk(event_brief)
    else:
        return await run_brandguard_direct(event_brief)


# CLI Entry Point
if __name__ == "__main__":
    # Sample event brief for testing
    event_brief = {
        "event_title": "Zero Trust Security Webinar",
        "event_description": "Learn how to implement Zero Trust architecture in your organization.",
        "event_date": "2026-02-15",
        "target_audience": "IT Security professionals and CISOs",
        "key_messages": [
            "Zero Trust is essential for modern security",
            "Implementation doesn't have to be complex"
        ],
        "channels": ["linkedin", "email"],
        "relevant_urls": [
            {"label": "Register", "url": "https://example.com/register"}
        ]
    }

    print(f"Using {'Claude Agent SDK' if USING_SDK else 'Direct Anthropic API'}")
    result = asyncio.run(run_brandguard(event_brief))

    print(f"\nResult: {'Success' if result['success'] else 'Failed'}")
    print(f"Tool calls: {len(result['audit_log']['tool_calls'])}")

    if result.get("error"):
        print(f"Error: {result['error']}")
