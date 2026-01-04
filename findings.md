# BrandGuard Autonomous Agent: Findings

## The Experiment

I built a marketing content agent with maximum autonomy using the Claude Agent SDK architecture:
- **Skills** for domain expertise (markdown files in `.claude/skills/`)
- **MCP** for custom tools (proper extensibility pattern)
- **Hooks** for observability and guardrails
- **Host Runner** for invariant enforcement

The agent had tools and a goal. I observed what it did without forcing any particular process.

---

## Architecture: Skills + MCP

### What Worked Well

**Skills**:
- [ ] Agent read and followed the SOP skill
- [ ] Brand voice guidelines influenced content tone
- [ ] Channel rules were respected
- [ ] Verification rules were applied

**MCP Tools**:
- [ ] `retrieve_context` was called for grounding
- [ ] `critique_draft` was used for self-evaluation
- [ ] `verify_claims` was called before submission
- [ ] `generate_images` was executed after content

**Hooks**:
- [ ] PreToolUse successfully blocked unwanted tools
- [ ] PostToolUse captured full audit trail
- [ ] WebSearch guard worked as expected

**Host Runner**:
- [ ] Iteration cap prevented infinite loops
- [ ] Schema validation caught malformed outputs
- [ ] Unverified claims triggered re-runs

### What Needed Improvement

*Document issues encountered during testing*

---

## Patterns Observed

### Tool Sequence

*What was the typical order?*

Example: `retrieve_context(brand) → retrieve_context(product) → [drafting] → critique_draft → verify_claims → generate_images → save_output`

Did it vary? When?

### Retrieval Behavior

- Did agent retrieve first? [ ] Always / [ ] Usually / [ ] Sometimes / [ ] Never
- Did it retrieve both brand AND product context?
- How many retrieval calls per generation?

### Self-Critique

- How often did agent call critique_draft?
- Did it iterate on low scores?
- What triggered revisions?

### Claim Verification

- Did agent call verify_claims?
- How did it handle unsupported claims?
- Did the host runner catch any missed verifications?

### Image Generation

- When did agent generate images? Before or after verification?
- Quality of generated images?

---

## Surprises

*What did the agent do that you didn't expect?*

1.
2.
3.

---

## Comparison to LangGraph Version

| Aspect | LangGraph | Claude Agent SDK (Skills + MCP) |
|--------|-----------|--------------------------------|
| Process consistency | Deterministic | Emergent, mostly consistent |
| Token usage | ~X tokens | ~Y tokens |
| Quality | Score avg: X | Score avg: Y |
| Flexibility | Low | High |
| Developer experience | Explicit control | Trust + observe |
| Debugging | LangSmith traces | Audit logs + hooks |
| Extensibility | Add nodes | Add skills + MCP tools |

---

## Autonomy Observations

### When Agent Made Good Decisions

*Document cases where autonomous behavior was beneficial*

### When Agent Needed Guidance

*Document cases where prompting or host enforcement was necessary*

### The Autonomy/Reliability Tradeoff

*Your conclusions about trusting agents vs. explicit control*

---

## Key Learnings

### 1. Skills Shape Behavior

*How effective was the skills approach?*

### 2. MCP Provides Capabilities

*How well did the MCP tools work?*

### 3. Hooks Enable Guardrails

*How useful were PreToolUse and PostToolUse hooks?*

### 4. Host Enforcement is Essential

*Why the iteration cap and validation layer mattered*

---

## Recommendations

### When to Use This Architecture

- [ ] Exploratory/creative tasks
- [ ] Flexible workflows
- [ ] Rapid prototyping
- [ ] When agent reasoning is valuable

### When to Use LangGraph Instead

- [ ] Compliance-critical workflows
- [ ] Guaranteed step execution
- [ ] Deterministic behavior required
- [ ] Strict audit requirements

---

## Interview Narrative

> "I built a marketing agent using the Claude Agent SDK with the optimal 2026 architecture: Skills for domain expertise, MCP for custom tools, Hooks for guardrails.
>
> Skills are markdown files that encode brand voice, channel rules, and verification policy. The agent reads these automatically. MCP is how you extend the SDK with custom tools — I built a server exposing RAG retrieval, quality scoring, and claim verification.
>
> The host runner enforces invariants the agent might miss: max iterations, schema validation, and no-unverified-claims. This is the trust-but-verify approach.
>
> Compared to LangGraph: the SDK approach is more autonomous and feels like working with a capable colleague. LangGraph gives you explicit control over every step. Both have their place — SDK for exploration, LangGraph for compliance-critical workflows.
>
> The real skill is knowing which approach fits which problem."

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| Test runs | |
| Avg iterations | |
| Avg tool calls | |
| Success rate | |
| Avg brand voice score | |
| Avg CTA clarity score | |
| Claims verified | |
| Images generated | |
| Total tokens (avg) | |

---

*Last updated: YYYY-MM-DD*
