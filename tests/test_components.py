"""Unit tests for BrandGuard components.

Run with: pytest tests/ -v
"""

import pytest
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# MCP Tools Tests
# ============================================================================

class TestCritiqueDraft:
    """Tests for the critique_draft MCP tool."""

    def test_high_quality_content_passes(self):
        """Content with good brand voice and clear CTA should pass."""
        from brandguard_mcp.server import critique_draft

        result = critique_draft(
            channel="linkedin",
            headline="Join Our Security Webinar",
            body="Learn how to protect your team with Zero Trust architecture. Our experts will show you practical strategies to improve your security posture.",
            cta="Register now to secure your spot",
            claims=["Zero Trust reduces breach risk"]
        )

        assert result["brand_voice_score"] >= 7
        assert result["cta_clarity_score"] >= 7
        assert result["passed"] is True

    def test_content_with_buzzwords_scores_low(self):
        """Content with buzzwords should score lower on brand voice."""
        from brandguard_mcp.server import critique_draft

        result = critique_draft(
            channel="linkedin",
            headline="Revolutionary Game-Changing Paradigm Shift",
            body="Our cutting-edge, best-in-class, world-class solution leverages synergy to deliver next-gen results.",
            cta="Click here",
            claims=[]
        )

        assert result["brand_voice_score"] < 7
        assert result["cta_clarity_score"] < 7
        assert result["passed"] is False

    def test_weak_cta_scores_low(self):
        """Weak CTA should score lower."""
        from brandguard_mcp.server import critique_draft

        result = critique_draft(
            channel="linkedin",
            headline="Security Event",
            body="Your team needs better security practices.",
            cta="Click here",  # Weak CTA
            claims=[]
        )

        assert result["cta_clarity_score"] < 7

    def test_content_length_check(self):
        """Content exceeding channel limits should be flagged."""
        from brandguard_mcp.server import critique_draft

        # Web channel has 300 char limit
        long_body = "A" * 400
        result = critique_draft(
            channel="web",
            headline="Test",
            body=long_body,
            cta="Register now",
            claims=[]
        )

        assert result["length_ok"] is False
        assert any("exceeds" in issue.lower() for issue in result["issues"])


class TestVerifyClaims:
    """Tests for the verify_claims MCP tool."""

    def test_no_claims_returns_empty(self):
        """Empty claims list should return empty results."""
        from brandguard_mcp.server import verify_claims

        result = verify_claims(claims=[], source_chunk_ids=[])
        assert result == []

    def test_claims_without_sources_unsupported(self):
        """Claims without matching sources should be unsupported."""
        from brandguard_mcp.server import verify_claims

        result = verify_claims(
            claims=["Our platform has 99.99% uptime"],
            source_chunk_ids=["nonexistent_chunk"]
        )

        assert len(result) == 1
        assert result[0]["supported"] is False


# ============================================================================
# Schema Tests
# ============================================================================

class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_event_brief_validation(self):
        """EventBrief should validate required fields."""
        from src.schemas import EventBrief

        brief = EventBrief(
            event_title="Test Event",
            event_description="A test event",
            target_audience="Developers",
            channels=["linkedin"]
        )

        assert brief.event_title == "Test Event"
        assert brief.channels == ["linkedin"]

    def test_channel_content_optional_fields(self):
        """ChannelContent should handle optional fields."""
        from src.schemas import ChannelContent

        content = ChannelContent(
            channel="linkedin",
            body="Test body",
            cta="Register now"
        )

        assert content.headline is None
        assert content.hashtags is None

    def test_validate_output_schema(self):
        """validate_output_schema should correctly validate output."""
        from src.schemas import validate_output_schema

        valid_output = {
            "content": {"linkedin": {"body": "test", "cta": "click"}},
            "scorecard": {"linkedin": {}},
            "claims_table": []
        }

        invalid_output = {
            "content": {},  # Empty content
            "scorecard": {},
            "claims_table": []
        }

        assert validate_output_schema(valid_output) is True
        assert validate_output_schema(invalid_output) is False

    def test_has_unverified_claims(self):
        """has_unverified_claims should detect unverified claims."""
        from src.schemas import has_unverified_claims

        output_with_unverified = {
            "claims_table": [
                {"claim": "Test claim", "supported": False}
            ]
        }

        output_all_verified = {
            "claims_table": [
                {"claim": "Test claim", "supported": True}
            ]
        }

        assert has_unverified_claims(output_with_unverified) is True
        assert has_unverified_claims(output_all_verified) is False


# ============================================================================
# RAG Tests
# ============================================================================

class TestRAG:
    """Tests for RAG retrieval."""

    def test_retrieve_chunks_brand(self):
        """Should retrieve chunks from brand collection."""
        from src.rag.retrieve import retrieve_chunks

        chunks = retrieve_chunks(
            query="brand voice guidelines",
            collection_name="brand",
            top_k=3
        )

        assert len(chunks) <= 3
        if chunks:
            assert "id" in chunks[0]
            assert "text" in chunks[0]

    def test_retrieve_chunks_product(self):
        """Should retrieve chunks from product collection."""
        from src.rag.retrieve import retrieve_chunks

        chunks = retrieve_chunks(
            query="SSO features",
            collection_name="product",
            top_k=3
        )

        assert len(chunks) <= 3


# ============================================================================
# Integration Tests (require more setup)
# ============================================================================

class TestIntegration:
    """Integration tests that test multiple components together."""

    @pytest.mark.skip(reason="Requires full agent setup")
    def test_full_generation_flow(self):
        """Test the full content generation flow."""
        pass


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
