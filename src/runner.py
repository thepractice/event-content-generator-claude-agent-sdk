"""BrandGuard Host Runner - Invariant enforcement layer.

This module provides the outer loop that enforces invariants:
- Maximum 3 iterations
- Schema validation
- No unverified claims

The host runner doesn't trust the agent to self-terminate correctly.
It validates outputs and retries if necessary.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .agent import run_brandguard, audit_log
from .schemas import (
    validate_output_schema,
    has_unverified_claims,
    extract_claims_from_content,
    RunnerResult,
    AuditLog,
    ContentBundle,
)


# Maximum iterations before giving up
MAX_ITERATIONS = 2


async def run_with_guardrails(event_brief: Dict[str, Any]) -> Dict[str, Any]:
    """Run the BrandGuard agent with host-level invariant enforcement.

    This function wraps the agent execution and ensures:
    1. Maximum 3 iteration cycles
    2. Output matches expected schema
    3. No unverified claims in final output

    Args:
        event_brief: The event details to generate content for

    Returns:
        RunnerResult with success status, result, and flags
    """
    best_result = None
    flags = []
    all_audit_logs = []

    for iteration in range(MAX_ITERATIONS):
        print(f"\n{'='*60}")
        print(f"Iteration {iteration + 1}/{MAX_ITERATIONS}")
        print(f"{'='*60}")

        # Run the agent
        try:
            result = await run_brandguard(event_brief)
        except Exception as e:
            flags.append(f"iteration_{iteration}_error: {str(e)}")
            continue

        # Save audit log for this iteration
        all_audit_logs.append({
            "iteration": iteration + 1,
            "audit_log": result.get("audit_log", {}),
            "success": result.get("success", False),
        })

        # Check if agent reported success
        if not result.get("success"):
            flags.append(f"iteration_{iteration}_agent_failed")
            continue

        # Get the output (agent saves to saved_bundle or we load from file)
        output = result.get("saved_bundle")
        if output is None:
            # Try to load from file
            output = _load_output_from_file()

        if output is None:
            flags.append(f"iteration_{iteration}_no_output")
            continue

        best_result = output

        # Validate output schema
        if not validate_output_schema(output):
            flags.append(f"iteration_{iteration}_schema_invalid")
            print("Schema validation failed - will retry")
            continue

        # Verify no unverified claims (host enforcement)
        if has_unverified_claims(output):
            unverified = _get_unverified_claims(output)
            flags.append(f"iteration_{iteration}_unverified_claims: {len(unverified)}")
            print(f"Found {len(unverified)} unverified claims - will retry")

            # Update the event brief to request claim fixes
            event_brief = _add_feedback_to_brief(event_brief, unverified)
            continue

        # All invariants passed!
        print("\nAll invariants passed!")

        # Save final audit log
        _save_audit_log(all_audit_logs, flags, success=True)

        return {
            "success": True,
            "result": output,
            "iterations": iteration + 1,
            "flags": [],
            "audit_log": _combine_audit_logs(all_audit_logs),
        }

    # Max iterations reached - export best effort
    print(f"\nMax iterations ({MAX_ITERATIONS}) reached - exporting best effort")
    flags.append("max_iterations_reached")

    # Add warning flags to the best result
    if best_result:
        best_result["flags"] = flags

        # Save with flags
        output_path = Path("output/bundle.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(best_result, f, indent=2)

    # Save final audit log
    _save_audit_log(all_audit_logs, flags, success=False)

    return {
        "success": False,
        "result": best_result,
        "iterations": MAX_ITERATIONS,
        "flags": flags,
        "audit_log": _combine_audit_logs(all_audit_logs),
    }


def _load_output_from_file() -> Optional[Dict[str, Any]]:
    """Try to load output from the standard output file."""
    output_path = Path("output/bundle.json")
    if output_path.exists():
        try:
            with open(output_path) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _get_unverified_claims(output: Dict[str, Any]) -> list[str]:
    """Extract the unverified claims from output."""
    unverified = []
    claims_table = output.get("claims_table", [])

    for claim in claims_table:
        if isinstance(claim, dict) and not claim.get("supported", False):
            unverified.append(claim.get("claim", "Unknown claim"))

    return unverified


def _add_feedback_to_brief(event_brief: Dict[str, Any], unverified_claims: list[str]) -> Dict[str, Any]:
    """Add feedback about unverified claims to help the agent fix them."""
    feedback = (
        "\n\nIMPORTANT FEEDBACK FROM PREVIOUS ITERATION:\n"
        "The following claims could not be verified and must be removed or softened:\n"
    )
    for claim in unverified_claims[:5]:  # Limit to 5
        feedback += f"- {claim}\n"

    feedback += "\nPlease either remove these claims or soften them to opinions."

    updated = event_brief.copy()
    updated["event_description"] = event_brief["event_description"] + feedback

    return updated


def _combine_audit_logs(logs: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple iteration audit logs into one."""
    combined = {
        "total_iterations": len(logs),
        "iterations": logs,
        "all_tool_calls": [],
    }

    for log in logs:
        audit = log.get("audit_log", {})
        tool_calls = audit.get("tool_calls", [])
        for call in tool_calls:
            call["iteration"] = log.get("iteration", 0)
            combined["all_tool_calls"].append(call)

    return combined


def _save_audit_log(logs: list[Dict[str, Any]], flags: list[str], success: bool):
    """Save the complete audit log to file."""
    audit_path = Path("output/audit.json")
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    audit_data = {
        "completed_at": datetime.now().isoformat(),
        "success": success,
        "total_iterations": len(logs),
        "flags": flags,
        "iterations": logs,
    }

    with open(audit_path, "w") as f:
        json.dump(audit_data, f, indent=2)


# ============================================================================
# Analysis Functions
# ============================================================================

def analyze_run(output_path: str = "output/audit.json") -> Dict[str, Any]:
    """Analyze a completed run from its audit log.

    Returns observations about agent behavior.
    """
    try:
        with open(output_path) as f:
            audit = json.load(f)
    except Exception as e:
        return {"error": f"Could not load audit log: {e}"}

    observations = []
    tool_sequence = []

    # Extract tool sequence across all iterations
    for iteration in audit.get("iterations", []):
        iter_audit = iteration.get("audit_log", {})
        for call in iter_audit.get("tool_calls", []):
            tool = call.get("tool", "")
            if tool and tool != "unknown":
                tool_sequence.append(tool)

    # Check if agent retrieved first
    if tool_sequence:
        first_tool = tool_sequence[0]
        if first_tool != "retrieve_context":
            observations.append(f"Agent started with {first_tool} instead of retrieve_context")
        else:
            observations.append("Agent correctly retrieved context first")

    # Count tool usage
    tool_counts = {}
    for tool in tool_sequence:
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    # Check for critique
    if "critique_draft" not in tool_counts:
        observations.append("Agent never critiqued its drafts")
    else:
        observations.append(f"Agent critiqued drafts {tool_counts['critique_draft']} times")

    # Check for verification
    if "verify_claims" not in tool_counts:
        observations.append("Agent never verified claims")
    else:
        observations.append(f"Agent verified claims {tool_counts['verify_claims']} times")

    # Check for images
    if "generate_images" not in tool_counts:
        observations.append("Agent did not generate images")
    else:
        observations.append("Agent generated images")

    return {
        "success": audit.get("success", False),
        "iterations": audit.get("total_iterations", 0),
        "flags": audit.get("flags", []),
        "tool_sequence": tool_sequence,
        "tool_counts": tool_counts,
        "observations": observations,
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        # Analyze a previous run
        analysis = analyze_run()
        print("\n=== Run Analysis ===")
        print(f"Success: {analysis.get('success')}")
        print(f"Iterations: {analysis.get('iterations')}")
        print(f"Flags: {analysis.get('flags')}")
        print(f"\nTool sequence: {' -> '.join(analysis.get('tool_sequence', []))}")
        print(f"\nTool counts: {analysis.get('tool_counts')}")
        print("\nObservations:")
        for obs in analysis.get("observations", []):
            print(f"  - {obs}")
    else:
        # Run the agent (single channel for faster testing)
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

        result = asyncio.run(run_with_guardrails(event_brief))

        print(f"\n{'='*60}")
        print("FINAL RESULT")
        print(f"{'='*60}")
        print(f"Success: {result['success']}")
        print(f"Iterations: {result['iterations']}")
        print(f"Flags: {result['flags']}")

        if result.get("result"):
            print("\nOutput saved to: output/bundle.json")
            print("Audit log saved to: output/audit.json")
