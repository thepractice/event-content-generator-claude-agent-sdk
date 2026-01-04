---
description: Complete workflow for generating brand-safe marketing content
globs: ["**/*.md", "**/*.json"]
alwaysApply: true
---

# BrandGuard Standard Operating Procedure

This skill defines the complete workflow for generating brand-safe marketing content.

## Workflow Overview

Follow these steps in order:

1. **Retrieve Context** - Ground yourself in the knowledge base
2. **Draft Content** - Write content for each channel
3. **Critique Each Draft** - Score quality and identify issues
4. **Verify Claims** - Ensure all claims are traceable to sources
5. **Fix Issues** - Revise content based on feedback
6. **Generate Images** - Create marketing visuals
7. **Save Output** - Package and export final deliverables

## Step 1: Retrieve Context

Before drafting ANY content, retrieve relevant context from the knowledge base.

Use the MCP tool `retrieve_context`:
- Query for "brand" context to get voice/tone examples
- Query for "product" context to get facts and features

**Save the chunk IDs** - you'll need them for claim verification later.

Example:
```
retrieve_context(query="brand voice guidelines", context_type="brand")
retrieve_context(query="product features security", context_type="product")
```

## Step 2: Draft Content

For each requested channel, write content that:
- Matches the brand voice (see brand-voice skill)
- Fits channel constraints (see channel-rules skill)
- Includes a clear CTA with the provided URL
- Explicitly lists all factual claims you're making

When making factual claims, cite the source chunk ID:
- "Our platform supports SSO and MFA [source: chunk_abc123]"

## Step 3: Critique Each Draft

Call `critique_draft` for EVERY channel's content.

The tool returns:
- `brand_voice_score` (0-10)
- `cta_clarity_score` (0-10)
- `length_ok` (boolean)
- `issues` (list of problems)
- `feedback_string` (natural language guidance)
- `passed` (boolean - true if all scores >= 7 and length_ok)

**If any draft fails**: Note the feedback and plan to revise.

## Step 4: Verify Claims

Collect ALL factual claims from ALL drafts.

Call `verify_claims` with:
- `claims`: List of factual statements
- `source_chunk_ids`: List of chunk IDs from your retrieval step

The tool returns for each claim:
- `supported`: boolean - is this claim traceable to a source?
- `source_id`: the matching chunk ID (if supported)
- `similarity`: confidence score
- `quoted_span`: exact text from source (if found)

**For any unsupported claims**:
- REMOVE the claim entirely, OR
- SOFTEN to opinion: "We believe..." or "designed to help..."

## Step 5: Fix Issues

If critique scores < 7 OR any claims are unsupported:

1. Review the `feedback_string` from critique
2. Review unsupported claims from verification
3. Revise the content
4. Re-critique to confirm improvement

**Maximum 3 revision cycles** - if still failing, proceed to export with flags.

## Step 6: Generate Images

After content is finalized, call `generate_images`:
- `channels`: List of channels needing images
- `event_title`: The event title
- `visual_style`: Optional style guidance (default: "modern, professional")

Images are saved to `output/images/{channel}.png`.

## Step 7: Save Output

Use the `Write` tool to save final content to `output/bundle.json`:

```json
{
  "event_title": "...",
  "generated_at": "2026-01-04T...",
  "content": {
    "linkedin": {
      "headline": "...",
      "body": "...",
      "cta": "...",
      "hashtags": ["#...", "#..."]
    },
    "email": {
      "subject": "...",
      "body": "...",
      "cta": "..."
    }
  },
  "scorecard": {
    "linkedin": {"brand_voice": 8, "cta_clarity": 9, "length_ok": true},
    "email": {"brand_voice": 7, "cta_clarity": 8, "length_ok": true}
  },
  "claims_table": [
    {"claim": "...", "source_id": "chunk_abc", "supported": true}
  ],
  "images": {
    "linkedin": "output/images/linkedin.png",
    "email": "output/images/email.png"
  }
}
```

## Quality Gates

Content MUST meet these requirements:
- Brand voice score >= 7
- CTA clarity score >= 7
- Length within channel limits (see channel-rules)
- ALL factual claims verified

## Iteration Rules

- Maximum 3 revision cycles per generation
- If still failing after 3 cycles, export with `"flags": ["quality_gate_failed"]`
- Log all iterations in the output for observability
