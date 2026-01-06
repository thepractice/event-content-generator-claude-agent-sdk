"""BrandGuard MCP Server - Custom domain tools for autonomous marketing agent.

This server exposes 4 tools:
1. retrieve_context - RAG search from ChromaDB
2. critique_draft - Quality scoring with feedback
3. verify_claims - Embedding-based citation matching
4. generate_images - Gemini Imagen API

Run with: python brandguard_mcp/server.py
Or connect via Claude Desktop / Claude Agent SDK
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from typing import Optional
import json

# Initialize MCP server
mcp = FastMCP("BrandGuard Tools")


# ============================================================================
# Tool 1: retrieve_context
# ============================================================================

@mcp.tool()
def retrieve_context(query: str, context_type: str) -> list[dict]:
    """Search the knowledge base for relevant information.

    Args:
        query: What to search for (e.g., "brand voice guidelines", "security features")
        context_type: Type of context to retrieve - "brand" for voice/tone examples,
                     "product" for facts and features

    Returns:
        List of matching chunks with IDs and text. Use the IDs for verify_claims.
    """
    from src.rag.retrieve import retrieve_chunks

    if context_type not in ["brand", "product"]:
        return [{"error": f"Invalid context_type: {context_type}. Use 'brand' or 'product'."}]

    try:
        chunks = retrieve_chunks(query=query, collection_name=context_type, top_k=5)

        # Format for agent consumption
        return [
            {
                "id": chunk["id"],
                "text": chunk["text"][:500],  # Truncate for readability
                "source": chunk.get("source", "unknown"),
            }
            for chunk in chunks
        ]
    except Exception as e:
        return [{"error": str(e)}]


# ============================================================================
# Tool 2: critique_draft
# ============================================================================

# Channel-specific limits
CHANNEL_LIMITS = {
    "linkedin": {"max_chars": 3000},
    "facebook": {"max_chars": 500},
    "email": {"max_chars": 1500, "subject_max": 60},
    "web": {"max_chars": 300},
}

# CTA keywords that indicate a strong call-to-action
CTA_KEYWORDS = [
    "register", "join", "learn", "discover", "get", "start",
    "sign up", "download", "watch", "explore", "reserve", "claim"
]

# Brand voice indicators (positive)
BRAND_POSITIVE = [
    "you", "your", "teams", "together", "discover", "learn",
    "build", "create", "transform", "improve"
]

# Brand voice indicators (negative - jargon/buzzwords)
BRAND_NEGATIVE = [
    "revolutionary", "game-changing", "synergy", "leverage",
    "paradigm", "best-in-class", "world-class", "cutting-edge"
]


@mcp.tool()
def critique_draft(
    channel: str,
    headline: Optional[str],
    body: str,
    cta: str,
    claims: list[str]
) -> dict:
    """Evaluate a piece of content against quality standards.

    Args:
        channel: The marketing channel ("linkedin", "facebook", "email", "web")
        headline: Optional headline (not all channels need this)
        body: Main content body
        cta: Call-to-action text
        claims: List of factual claims made in the content

    Returns:
        Quality scores, issues, feedback, and pass/fail status.
    """
    issues = []
    suggestions = []

    # Get channel limits
    limits = CHANNEL_LIMITS.get(channel, CHANNEL_LIMITS["linkedin"])
    max_chars = limits.get("max_chars", 3000)

    # === Hard Constraints (Deterministic) ===

    # 1. Length check
    total_chars = len(body) + len(headline or "") + len(cta)
    length_ok = total_chars <= max_chars

    if not length_ok:
        issues.append(f"Content exceeds {channel} limit: {total_chars}/{max_chars} chars")
        suggestions.append(f"Reduce content by {total_chars - max_chars} characters")

    # 2. Email subject check
    if channel == "email" and headline:
        subject_max = limits.get("subject_max", 60)
        if len(headline) > subject_max:
            issues.append(f"Subject line too long: {len(headline)}/{subject_max} chars")
            suggestions.append("Shorten subject line to under 60 characters")

    # 3. CTA presence check
    if not cta or len(cta.strip()) < 5:
        issues.append("CTA is missing or too short")
        suggestions.append("Add a clear call-to-action")

    # === Soft Quality (Heuristic) ===

    # 4. CTA clarity score
    cta_lower = cta.lower()
    cta_has_keyword = any(kw in cta_lower for kw in CTA_KEYWORDS)
    cta_clarity_score = 8 if cta_has_keyword else 5

    if not cta_has_keyword:
        issues.append("CTA lacks clear action verb")
        suggestions.append("Use action words like 'Register', 'Join', 'Learn', 'Discover'")

    # 5. Brand voice score
    content_lower = (body + " " + (headline or "")).lower()

    # Count positive indicators
    positive_count = sum(1 for word in BRAND_POSITIVE if word in content_lower)

    # Count negative indicators
    negative_count = sum(1 for word in BRAND_NEGATIVE if word in content_lower)

    # Calculate brand voice score
    if negative_count > 2:
        brand_voice_score = 4
        issues.append(f"Contains {negative_count} buzzwords/jargon terms")
        suggestions.append("Remove buzzwords: " + ", ".join(
            [w for w in BRAND_NEGATIVE if w in content_lower][:3]
        ))
    elif positive_count >= 3 and negative_count == 0:
        brand_voice_score = 9
    elif positive_count >= 2:
        brand_voice_score = 8
    elif positive_count >= 1:
        brand_voice_score = 7
    else:
        brand_voice_score = 6
        suggestions.append("Add more direct address ('you', 'your') and action words")

    # 6. Check for passive voice indicators (simple heuristic)
    passive_indicators = ["will be", "has been", "was", "were", "is being"]
    passive_count = sum(1 for p in passive_indicators if p in content_lower)
    if passive_count > 2:
        issues.append("Content may contain passive voice")
        suggestions.append("Convert passive voice to active voice")
        brand_voice_score = max(5, brand_voice_score - 1)

    # === Overall Assessment ===
    passed = (
        brand_voice_score >= 7 and
        cta_clarity_score >= 7 and
        length_ok
    )

    # Build feedback string for agent reasoning
    if passed:
        feedback_parts = ["PASS: Content meets quality standards."]
        if suggestions:
            feedback_parts.append("MINOR IMPROVEMENTS: " + "; ".join(suggestions[:2]))
    else:
        feedback_parts = ["FAIL: Content does not meet quality standards."]
        if issues:
            feedback_parts.append("ISSUES: " + "; ".join(issues))
        if suggestions:
            feedback_parts.append("FIX: " + "; ".join(suggestions))

    feedback_string = " ".join(feedback_parts)

    return {
        "brand_voice_score": brand_voice_score,
        "cta_clarity_score": cta_clarity_score,
        "length_ok": length_ok,
        "char_count": total_chars,
        "max_chars": max_chars,
        "issues": issues,
        "suggestions": suggestions,
        "feedback_string": feedback_string,
        "passed": passed,
    }


# ============================================================================
# Tool 3: verify_claims
# ============================================================================

@mcp.tool()
def verify_claims(claims: list[str], source_chunk_ids: list[str]) -> list[dict]:
    """Check whether factual claims can be traced to source documents.

    Args:
        claims: List of factual statements to verify
        source_chunk_ids: List of chunk IDs from retrieve_context to check against

    Returns:
        Verification status for each claim including:
        - supported: boolean
        - source_id: matching chunk ID (if found)
        - similarity: confidence score
        - quoted_span: exact matching text from source (if found)
    """
    from src.rag.retrieve import get_chunks_by_ids, compute_similarity

    if not claims:
        return []

    # Load all referenced chunks
    all_chunks = get_chunks_by_ids(source_chunk_ids)

    if not all_chunks:
        # No chunks found - all claims are unsupported
        return [
            {
                "claim": claim,
                "source_id": None,
                "similarity": 0.0,
                "supported": False,
                "quoted_span": None,
            }
            for claim in claims
        ]

    results = []
    for claim in claims:
        best_match = {
            "source_id": None,
            "similarity": 0.0,
            "quoted_span": None,
        }

        for chunk_id, chunk in all_chunks.items():
            chunk_text = chunk.get("text", "")

            # Compute semantic similarity using embeddings
            similarity = compute_similarity(claim, chunk_text)

            if similarity > best_match["similarity"]:
                best_match["similarity"] = similarity
                best_match["source_id"] = chunk_id

                # Try to find quoted span (simple substring matching)
                quoted_span = _find_quoted_span(claim, chunk_text)
                best_match["quoted_span"] = quoted_span

        # Threshold for support: 0.7 similarity
        supported = best_match["similarity"] >= 0.7

        results.append({
            "claim": claim,
            "source_id": best_match["source_id"] if supported else None,
            "similarity": round(best_match["similarity"], 3),
            "supported": supported,
            "quoted_span": best_match["quoted_span"] if supported else None,
        })

    return results


def _find_quoted_span(claim: str, source_text: str, min_words: int = 3) -> Optional[str]:
    """Try to find a matching span in the source text.

    Uses simple word overlap to find the best matching phrase.
    """
    claim_words = claim.lower().split()
    source_words = source_text.lower().split()

    if len(claim_words) < min_words or len(source_words) < min_words:
        return None

    best_span = None
    best_overlap = 0

    # Sliding window over source
    for window_size in range(min_words, min(len(source_words), 20)):
        for i in range(len(source_words) - window_size + 1):
            window = source_words[i:i + window_size]
            overlap = len(set(claim_words) & set(window))

            if overlap > best_overlap:
                best_overlap = overlap
                # Get original case from source
                original_words = source_text.split()
                if i + window_size <= len(original_words):
                    best_span = " ".join(original_words[i:i + window_size])

    # Only return if significant overlap
    if best_overlap >= len(claim_words) * 0.5:
        return best_span

    return None


# ============================================================================
# Tool 4: generate_images
# ============================================================================

@mcp.tool()
def generate_images(
    channels: list[str],
    event_title: str,
    visual_style: str = "modern, professional, corporate photography"
) -> dict:
    """Generate marketing visuals for each channel using Gemini Imagen.

    Args:
        channels: List of channels needing images (e.g., ["linkedin", "email"])
        event_title: The event title to incorporate in the image
        visual_style: Style guidance for image generation

    Returns:
        Dict mapping channel to image path (or None if generation failed)
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return {channel: None for channel in channels}

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {
            channel: None for channel in channels
        } | {"error": "GEMINI_API_KEY not set"}

    genai.configure(api_key=api_key)

    # Create output directory
    output_dir = Path("output/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Channel-specific style adjustments
    channel_styles = {
        "linkedin": "professional corporate photography, clean design, business context",
        "facebook": "engaging social media graphic, vibrant, approachable",
        "email": "clean header image, simple, professional",
        "web": "hero banner, modern, high-impact visual",
    }

    images = {}
    for channel in channels:
        try:
            # Build prompt
            channel_style = channel_styles.get(channel, visual_style)
            prompt = (
                f"Marketing image for {channel} social media post about: {event_title}. "
                f"Style: {channel_style}. {visual_style}. "
                f"No text in image. High quality, professional."
            )

            # Generate image
            model = genai.ImageGenerationModel("imagen-3.0-generate-001")
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9" if channel in ["linkedin", "web"] else "1:1",
            )

            # Save image
            if response.images:
                path = output_dir / f"{channel}.png"
                response.images[0]._pil_image.save(str(path), format="PNG")
                images[channel] = str(path)
            else:
                images[channel] = None

        except Exception as e:
            images[channel] = None
            images[f"{channel}_error"] = str(e)

    return images


# ============================================================================
# Tool 5: save_output
# ============================================================================

@mcp.tool()
def save_output(
    event_title: str,
    content: dict,
    scorecard: dict,
    claims_table: list,
    images: Optional[dict] = None
) -> dict:
    """Save the final content bundle to output/bundle.json.

    Args:
        event_title: The event title
        content: Dict with content per channel, each having headline, body, cta
        scorecard: Dict with quality scores per channel
        claims_table: List of claim verification results
        images: Optional dict with image paths per channel

    Returns:
        Success status and path to saved file.
    """
    from datetime import datetime

    output = {
        "event_title": event_title,
        "generated_at": datetime.now().isoformat(),
        "content": content,
        "scorecard": scorecard,
        "claims_table": claims_table,
        "images": images or {},
    }

    output_path = Path("output/bundle.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    return {"success": True, "path": str(output_path)}


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
