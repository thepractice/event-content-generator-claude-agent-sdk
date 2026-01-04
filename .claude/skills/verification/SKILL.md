---
description: Rules for verifying factual claims
globs: ["**/*.json"]
alwaysApply: true
---

# Claim Verification

This skill defines the rules for verifying factual claims in marketing content.

## The Golden Rule

**No citation, no claim.**

Every factual statement must be traceable to a source document in the corpus.

## What Counts as a Factual Claim

These types of statements REQUIRE verification:

### Statistics and Numbers
- "40% reduction in security incidents"
- "500+ customers trust our platform"
- "99.99% uptime guarantee"

### Specific Features
- "Supports SSO and MFA"
- "Integrates with Salesforce"
- "Real-time monitoring"

### Comparisons
- "Faster than competitors"
- "More secure than traditional solutions"
- "Reduces costs by 50%"

### Customer Results
- "Fortune 500 companies use our platform"
- "Teams have reduced ticket volume by 40%"
- "Enterprise customers achieve ROI in 90 days"

### Certifications and Compliance
- "SOC 2 Type II certified"
- "GDPR compliant"
- "ISO 27001 certified"

## What Doesn't Need Verification

These types of statements DON'T require verification:

### Opinions and Beliefs
- "We believe in..."
- "Our vision is..."
- "We're excited to..."

### Invitations and Calls-to-Action
- "Join us for..."
- "Register now"
- "Learn more about..."

### Future-Oriented Statements
- "You'll learn how to..."
- "Discover strategies for..."
- "Explore approaches to..."

### Generic Industry Facts
- "Security threats are increasing"
- "Remote work is changing how teams collaborate"
- (Use WebSearch for trend validation if needed)

## Verification Process

### Step 1: Extract Claims
Identify ALL factual claims in your drafted content.

### Step 2: Call verify_claims
Use the MCP tool with:
- `claims`: List of all extracted claims
- `source_chunk_ids`: List of chunk IDs from your retrieve_context calls

### Step 3: Analyze Results
For each claim, the tool returns:
- `supported`: true/false
- `source_id`: matching chunk ID (if found)
- `similarity`: confidence score (0.7+ is strong)
- `quoted_span`: exact text from source

### Step 4: Handle Failures

For unsupported claims, you have two options:

**Option A: Remove the Claim**
Before: "Our platform reduces incidents by 75%."
After: Remove entirely.

**Option B: Soften to Opinion**
Before: "Our platform reduces incidents by 75%."
After: "Our platform is designed to help reduce security incidents."

**Never leave an unverified factual claim in final content.**

## WebSearch Constraints

WebSearch may ONLY be used for:
- Trending topics and hashtags
- Current event timing verification
- Industry trend validation

WebSearch must NEVER be used for:
- Product features or capabilities
- Customer statistics or results
- Performance claims
- Anything that should come from the corpus

If you need factual information that isn't in the corpus, you cannot make that claim.

## Citation Format

When drafting, cite sources inline:
```
"Our platform supports SSO, MFA, and lifecycle management [source: chunk_abc123],
helping teams achieve 75% reduction in identity-related incidents [source: chunk_def456]."
```

In the final output, the `claims_table` tracks all citations:
```json
{
  "claims_table": [
    {
      "claim": "Our platform supports SSO, MFA, and lifecycle management",
      "source_id": "chunk_abc123",
      "supported": true,
      "quoted_span": "Key features include SSO, MFA, and lifecycle management"
    },
    {
      "claim": "75% reduction in identity-related incidents",
      "source_id": "chunk_def456",
      "supported": true,
      "quoted_span": "Fortune 500 customers reported 75% reduction in identity-related security incidents"
    }
  ]
}
```

## Verification Thresholds

The `verify_claims` tool uses embedding similarity:
- **0.7+**: Strong match - claim is supported
- **0.5-0.7**: Weak match - consider revising claim to match source more closely
- **Below 0.5**: No match - claim is NOT supported

## Common Mistakes

1. **Overstating source material**
   - Source: "Can help reduce incidents"
   - Claim: "Guarantees 100% incident prevention"
   - Fix: Match the source language

2. **Inventing statistics**
   - Claim: "90% of users prefer our solution"
   - If not in corpus: Remove or soften

3. **Assuming industry facts**
   - Claim: "The average breach costs $4.5M"
   - If not in corpus: Either find a source or remove

4. **Extrapolating from examples**
   - Source mentions ONE customer's results
   - Claim: "All customers achieve these results"
   - Fix: Use the specific example only

## Quality Assurance

Before submitting final content:
1. Run `verify_claims` on ALL factual statements
2. Confirm every claim shows `"supported": true`
3. Review `quoted_span` to ensure claims match sources
4. Remove or soften any unsupported claims

**Zero tolerance for unverified claims.**
