"""Pydantic models and schemas for BrandGuard."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Input Schemas
# ============================================================================

class EventBrief(BaseModel):
    """Input schema for event content generation."""

    event_title: str = Field(description="Title of the event")
    event_description: str = Field(description="Description of the event")
    event_date: Optional[str] = Field(default=None, description="Date of the event")
    target_audience: str = Field(description="Who the content is for")
    key_messages: List[str] = Field(
        default_factory=list,
        description="Key points to communicate"
    )
    channels: List[Literal["linkedin", "facebook", "email", "web"]] = Field(
        description="Marketing channels to generate content for"
    )
    relevant_urls: List[Dict[str, str]] = Field(
        default_factory=list,
        description="URLs for CTAs [{'label': 'Register', 'url': 'https://...'}]"
    )


# ============================================================================
# Content Schemas
# ============================================================================

class ChannelContent(BaseModel):
    """Generated content for a specific channel."""

    channel: Literal["linkedin", "facebook", "email", "web"]
    headline: Optional[str] = None
    subject_line: Optional[str] = None  # For email
    body: str
    cta: str
    hashtags: Optional[List[str]] = None  # For social


class Claim(BaseModel):
    """A factual claim with verification status."""

    claim: str = Field(description="The factual statement")
    source_id: Optional[str] = Field(
        default=None,
        description="ID of the supporting source chunk"
    )
    similarity: float = Field(default=0.0, description="Similarity score")
    supported: bool = Field(default=False, description="Whether claim is verified")
    quoted_span: Optional[str] = Field(
        default=None,
        description="Exact matching text from source"
    )


class ChannelScorecard(BaseModel):
    """Quality scores for a channel's content."""

    brand_voice_score: int = Field(ge=0, le=10)
    cta_clarity_score: int = Field(ge=0, le=10)
    length_ok: bool
    char_count: int
    passed: bool


# ============================================================================
# Output Schemas
# ============================================================================

class ContentBundle(BaseModel):
    """Complete output bundle for generated content."""

    event_title: str
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Content per channel
    content: Dict[str, ChannelContent]

    # Quality scores per channel
    scorecard: Dict[str, ChannelScorecard]

    # All claims with verification status
    claims_table: List[Claim]

    # Image paths per channel
    images: Dict[str, Optional[str]] = Field(default_factory=dict)

    # Metadata
    iterations: int = Field(default=1, description="Number of revision cycles")
    flags: List[str] = Field(
        default_factory=list,
        description="Any flags/warnings from generation"
    )


# ============================================================================
# Audit Schemas
# ============================================================================

class ToolCall(BaseModel):
    """Record of a single tool call."""

    timestamp: str
    tool: str
    input_summary: str
    response_summary: Optional[str] = None


class AuditLog(BaseModel):
    """Complete audit trail of agent execution."""

    started_at: str
    completed_at: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    total_iterations: int = 0
    success: bool = False
    flags: List[str] = Field(default_factory=list)


# ============================================================================
# Runner Result Schemas
# ============================================================================

class RunnerResult(BaseModel):
    """Result from the host runner."""

    success: bool
    result: Optional[ContentBundle] = None
    iterations: int
    flags: List[str] = Field(default_factory=list)
    audit_log: Optional[AuditLog] = None
    error: Optional[str] = None


# ============================================================================
# Validation Functions
# ============================================================================

def validate_output_schema(output: Dict[str, Any]) -> bool:
    """Validate that output matches ContentBundle schema.

    Returns True if valid, False otherwise.
    """
    try:
        # Check required fields
        required = ["content", "scorecard", "claims_table"]
        for field in required:
            if field not in output:
                return False

        # Check content has at least one channel
        if not output.get("content"):
            return False

        # Check each channel has required fields
        for channel, content in output["content"].items():
            if not isinstance(content, dict):
                return False
            if "body" not in content or "cta" not in content:
                return False

        return True

    except Exception:
        return False


def has_unverified_claims(output: Dict[str, Any]) -> bool:
    """Check if output contains any unverified factual claims.

    Returns True if there are unverified claims, False otherwise.
    """
    try:
        claims_table = output.get("claims_table", [])

        for claim in claims_table:
            if isinstance(claim, dict):
                if not claim.get("supported", False):
                    return True
            elif isinstance(claim, Claim):
                if not claim.supported:
                    return True

        return False

    except Exception:
        return True  # Assume there are issues if we can't parse


def extract_claims_from_content(content: Dict[str, Any]) -> List[str]:
    """Extract factual claims from content for verification.

    This is a simple heuristic - looks for statements with numbers,
    percentages, or specific feature claims.
    """
    claims = []
    claim_indicators = [
        "%", "customers", "users", "teams", "companies",
        "reduction", "increase", "faster", "secure",
        "integrates", "supports", "certified", "compliant"
    ]

    for channel, channel_content in content.items():
        if not isinstance(channel_content, dict):
            continue

        body = channel_content.get("body", "")

        # Split into sentences
        sentences = body.replace(".", ".\n").replace("!", "!\n").split("\n")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence looks like a factual claim
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in claim_indicators):
                # Skip if it's clearly an opinion or invitation
                opinion_starters = ["we believe", "we're excited", "join us", "discover", "learn"]
                if not any(sentence_lower.startswith(o) for o in opinion_starters):
                    claims.append(sentence)

    return claims
