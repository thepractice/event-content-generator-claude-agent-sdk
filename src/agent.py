"""BrandGuard Agent - Claude Agent SDK Integration.

Uses the official SDK pattern from:
https://platform.claude.com/docs/en/agent-sdk/quickstart

The SDK uses Claude Code as its runtime. Make sure you have:
1. Installed Claude Code: curl -fsSL https://claude.ai/install.sh | bash
2. Authenticated: run `claude` in terminal and follow prompts
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Audit Log
# ============================================================================

audit_log: Dict[str, Any] = {
    "started_at": None,
    "completed_at": None,
    "tool_calls": [],
    "messages": [],
}


def reset_audit_log():
    """Reset the audit log for a new run."""
    global audit_log
    audit_log = {
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "tool_calls": [],
        "messages": [],
    }


def get_audit_log() -> Dict[str, Any]:
    """Get the current audit log."""
    return audit_log.copy()


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

Use the MCP tools to complete this workflow:
1. Use mcp__brandguard__retrieve_context to get brand voice and product information (SAVE THE CHUNK IDs!)
2. Draft content for each channel following brand guidelines
3. Use mcp__brandguard__critique_draft to evaluate each draft - revise if scores < 7
4. Use mcp__brandguard__verify_claims to verify all factual claims using the chunk IDs
5. Use mcp__brandguard__generate_images to create visuals for each channel
6. Use mcp__brandguard__save_output to save the final bundle

Quality standards:
- Brand voice score >= 7
- CTA clarity score >= 7
- All claims must be verified against source documents
- Content within channel limits (LinkedIn 3000 chars, Email 300 words, Web 50 words)

Begin by retrieving brand voice and product context."""


# ============================================================================
# Agent Execution
# ============================================================================

async def run_brandguard(event_brief: Dict[str, Any], on_progress: callable = None) -> Dict[str, Any]:
    """Run the BrandGuard agent using Claude Agent SDK.

    This follows the official SDK quickstart pattern:
    - query() with prompt and options
    - Async iteration over messages
    - MCP server for custom tools
    """
    reset_audit_log()

    prompt = format_prompt(event_brief)
    project_dir = Path(__file__).parent.parent.resolve()

    # Path to MCP server
    mcp_server_path = project_dir / "brandguard_mcp" / "server.py"

    # Configure agent options following the quickstart pattern
    options = ClaudeAgentOptions(
        # Tools the agent can use (including MCP tools explicitly)
        allowed_tools=[
            "Read",
            "Write",
            "Glob",
            "Grep",
            # MCP tools must be explicitly allowed
            "mcp__brandguard__retrieve_context",
            "mcp__brandguard__critique_draft",
            "mcp__brandguard__verify_claims",
            "mcp__brandguard__generate_images",
            "mcp__brandguard__save_output",
        ],

        # Bypass all permission prompts for full automation
        permission_mode="bypassPermissions",

        # Working directory
        cwd=str(project_dir),

        # Connect to our MCP server (stdio pattern)
        mcp_servers={
            "brandguard": {
                "type": "stdio",
                "command": "python3",
                "args": [str(mcp_server_path)],
                "env": {
                    "PYTHONPATH": str(project_dir),
                }
            }
        },
    )

    # Collect output
    text_output = []
    tool_calls = []

    # Helper to notify progress
    def notify(event_type: str, data: dict):
        if on_progress:
            on_progress(event_type, data)

    notify("started", {"event_title": event_brief.get("event_title", "")})

    try:
        # Agentic loop: streams messages as Claude works
        async for message in query(prompt=prompt, options=options):

            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        # Claude's reasoning
                        text_output.append(block.text)
                        print(block.text)
                        audit_log["messages"].append({
                            "type": "text",
                            "content": block.text[:500],
                            "timestamp": datetime.now().isoformat(),
                        })
                        notify("reasoning", {"text": block.text[:200]})

                    elif hasattr(block, "name"):
                        # Tool being called
                        tool_name = block.name
                        print(f"Tool: {tool_name}")
                        tool_calls.append({
                            "tool": tool_name,
                            "timestamp": datetime.now().isoformat(),
                        })
                        audit_log["tool_calls"].append({
                            "tool": tool_name,
                            "timestamp": datetime.now().isoformat(),
                        })
                        notify("tool_call", {"tool": tool_name})

            elif isinstance(message, ResultMessage):
                # Final result
                print(f"Done: {message.subtype}")
                audit_log["completed_at"] = datetime.now().isoformat()
                notify("completed", {"subtype": getattr(message, "subtype", "success")})

    except Exception as e:
        audit_log["completed_at"] = datetime.now().isoformat()
        notify("error", {"message": str(e)})
        return {
            "success": False,
            "error": str(e),
            "audit_log": audit_log,
            "text_output": text_output,
        }

    # Try to load the saved bundle
    bundle_path = project_dir / "output" / "bundle.json"
    saved_bundle = None
    if bundle_path.exists():
        try:
            with open(bundle_path) as f:
                saved_bundle = json.load(f)
        except Exception:
            pass

    return {
        "success": True,
        "saved_bundle": saved_bundle,
        "audit_log": audit_log,
        "tool_calls": tool_calls,
        "text_output": text_output,
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    # Sample event brief for testing (single channel for faster iteration)
    event_brief = {
        "event_title": "Zero Trust Security Webinar",
        "event_description": "Learn how to implement Zero Trust architecture in your organization.",
        "event_date": "2026-02-15",
        "target_audience": "IT Security professionals and CISOs",
        "key_messages": [
            "Zero Trust is essential for modern security"
        ],
        "channels": ["linkedin"],  # Single channel for faster testing
        "relevant_urls": [
            {"label": "Register", "url": "https://example.com/register"}
        ]
    }

    print("=" * 60)
    print("BrandGuard Agent - Claude Agent SDK")
    print("=" * 60)
    print()

    result = asyncio.run(run_brandguard(event_brief))

    print()
    print("=" * 60)
    print(f"Result: {'Success' if result['success'] else 'Failed'}")
    print(f"Tool calls: {len(result.get('tool_calls', []))}")
    print("=" * 60)

    if result.get("error"):
        print(f"Error: {result['error']}")

    if result.get("saved_bundle"):
        print("Bundle saved to: output/bundle.json")
