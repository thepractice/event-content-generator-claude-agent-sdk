# BrandGuard Architecture: Claude Agent SDK

This document describes the architecture of the BrandGuard autonomous marketing agent built with the Claude Agent SDK, and compares it to the LangGraph version.

## The Core Distinction: Orchestrated vs Autonomous

| Frame | LangGraph | Claude Agent SDK |
|-------|-----------|------------------|
| **Orchestrated vs Autonomous** | You orchestrate the workflow | Agent decides the workflow |
| **Explicit vs Emergent** | You define the graph | Workflow emerges from reasoning |
| **Procedural vs Goal-oriented** | "Do these steps" | "Achieve this goal" |
| **Deterministic vs Adaptive** | Same input → same path | May vary based on context |

**The one-liner:** LangGraph defines **how**. Agent SDK defines **what**.

**Who decides the workflow?** That's the fundamental question. With LangGraph, you do. With Agent SDK, the agent does.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent Flow](#agent-flow)
3. [Key Components](#key-components)
4. [Comparison: Claude Agent SDK vs LangGraph](#comparison-claude-agent-sdk-vs-langgraph)
5. [When to Use Each Approach](#when-to-use-each-approach)
6. [Future Trajectory](#future-trajectory)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLAUDE AGENT SDK RUNTIME                        │
│                                                                     │
│  ┌──────────────────┐    ┌────────────────────────────────────────┐ │
│  │   SKILLS         │    │         MCP SERVER                     │ │
│  │  (.claude/skills)│    │      (brandguard_mcp/server.py)        │ │
│  │                  │    │                                        │ │
│  │  • brandguard-sop│    │  • retrieve_context (RAG search)       │ │
│  │  • brand-voice   │    │  • critique_draft (quality scoring)    │ │
│  │  • channel-rules │    │  • verify_claims (citation matching)   │ │
│  │  • verification  │    │  • generate_images (Gemini Imagen)     │ │
│  │                  │    │  • save_output (bundle export)         │ │
│  └──────────────────┘    └────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     CLAUDE REASONING                          │   │
│  │                                                               │   │
│  │   The agent DECIDES its own workflow based on:                │   │
│  │   • Skills (domain knowledge as markdown)                     │   │
│  │   • Tool results (feedback from MCP tools)                    │   │
│  │   • Quality standards (scores must be >= 7)                   │   │
│  │   • Prompt instructions (user's event brief)                  │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│   HOST RUNNER (src/runner.py)                                       │
│                                                                     │
│   • Max 2 iterations (invariant enforcement)                        │
│   • Schema validation (output must match expected structure)        │
│   • Unverified claims check (host doesn't trust agent)              │
│   • Best-effort export with flags on failure                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Insight: Emergent vs. Prescribed Workflow

**The Claude Agent SDK version lets Claude decide the workflow.** We provide:
- Skills (domain knowledge)
- Tools (capabilities)
- Quality standards (thresholds)
- A goal (generate marketing content)

Claude reasons about what to do, in what order, and when it's done.

---

## Agent Flow

### Typical Execution Sequence

When given an event brief, Claude typically follows this pattern:

```
1. READ SKILLS
   └─► Agent reads .claude/skills/ to understand brand voice, channel rules, verification policy

2. RETRIEVE CONTEXT
   ├─► mcp__brandguard__retrieve_context(query="brand voice", context_type="brand")
   └─► mcp__brandguard__retrieve_context(query="product features", context_type="product")

3. DRAFT CONTENT
   └─► Agent writes content for each channel based on retrieved context

4. CRITIQUE DRAFTS
   └─► mcp__brandguard__critique_draft(channel, headline, body, cta, claims)
       ├─► If scores < 7: Revise and re-critique
       └─► If scores >= 7: Continue

5. VERIFY CLAIMS
   └─► mcp__brandguard__verify_claims(claims, source_chunk_ids)
       ├─► If unsupported claims: Remove or soften, then re-verify
       └─► If all supported: Continue

6. GENERATE IMAGES (optional)
   └─► mcp__brandguard__generate_images(channels, event_title, visual_style)

7. SAVE OUTPUT
   └─► mcp__brandguard__save_output(event_title, content, scorecard, claims_table, images)
```

### What Makes This "Agentic"

The agent **decides**:
- **Order of operations**: May retrieve product context before brand context, or vice versa
- **When to iterate**: Based on critique scores, not a hardcoded counter
- **How to fix issues**: Reads feedback and decides what to change
- **When to stop**: When quality standards are met (not after N iterations)

The host runner provides **invariant enforcement**:
- Maximum iterations (prevents infinite loops)
- Schema validation (ensures output is usable)
- Final verification (catches agent mistakes)

---

## Key Components

### 1. Skills (`.claude/skills/`)

Skills are markdown files that encode domain expertise. The agent reads these automatically when `setting_sources=["project"]` is set.

| Skill | Purpose |
|-------|---------|
| `brandguard-sop/SKILL.md` | Complete workflow (retrieve → draft → critique → verify → save) |
| `brand-voice/SKILL.md` | Tone, style, words to use/avoid |
| `channel-rules/SKILL.md` | Platform constraints (LinkedIn 3000 chars, etc.) |
| `verification/SKILL.md` | "No citation, no claim" rule |

**Why Skills?** They let us encode expertise without hardcoding it into prompts. The agent can reference them naturally during reasoning.

### 2. MCP Server (`brandguard_mcp/server.py`)

The MCP (Model Context Protocol) server exposes domain-specific tools:

| Tool | Input | Output |
|------|-------|--------|
| `retrieve_context` | query, context_type | List of chunks with IDs |
| `critique_draft` | channel, headline, body, cta, claims | Scores, issues, feedback |
| `verify_claims` | claims, source_chunk_ids | Verification status per claim |
| `generate_images` | channels, event_title, visual_style | Image paths |
| `save_output` | event_title, content, scorecard, claims_table, images | Success status |

**Why MCP?** It's the standard protocol for extending Claude's capabilities. Tools run in a subprocess, isolated from the agent runtime.

### 3. Agent Client (`src/agent.py`)

The agent client uses the official SDK pattern:

```python
async for message in query(prompt=prompt, options=options):
    if isinstance(message, AssistantMessage):
        # Claude's reasoning and tool calls
    elif isinstance(message, ResultMessage):
        # Final result
```

**Configuration:**
```python
ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Glob", "Grep", "mcp__brandguard__*"],
    permission_mode="bypassPermissions",
    mcp_servers={"brandguard": {...}},
    setting_sources=["project"],  # Load skills
)
```

### 4. Host Runner (`src/runner.py`)

The host runner wraps agent execution with invariant enforcement:

```python
for iteration in range(MAX_ITERATIONS):
    result = await run_brandguard(event_brief)

    if validate_output_schema(result):
        if not has_unverified_claims(result):
            return success

    # Add feedback and retry
```

**Why a host runner?** The agent might:
- Loop forever on unsatisfiable quality goals
- Output malformed JSON
- Miss verification on some claims

The host catches these issues and enforces hard limits.

---

## Comparison: Claude Agent SDK vs LangGraph

### Architecture Comparison

| Aspect | LangGraph | Claude Agent SDK |
|--------|-----------|------------------|
| **Workflow Definition** | Explicit graph (nodes + edges) | Emergent (agent decides) |
| **Decision Making** | `should_continue()` function | Claude's reasoning |
| **Tool Execution** | Node functions call APIs | MCP server handles tools |
| **State Management** | TypedDict passed between nodes | Agent manages internally |
| **Iteration Control** | Counter in state + conditional edge | Agent decides + host caps |
| **Quality Evaluation** | Critic node with fixed rubric | Agent interprets feedback |
| **Observability** | LangSmith traces | Audit log + tool calls |

### Workflow Comparison

**LangGraph (Deterministic):**
```
RETRIEVE → DRAFT → CRITIC → VERIFY → [should_continue?] → EXPORT
                              ↑                              ↓
                              └────────── LOOP BACK ─────────┘
```

The graph is pre-defined. `should_continue()` checks:
- `iteration < 3`
- `critic_feedback.passed == True`
- `no unsupported claims`

**Claude Agent SDK (Emergent):**
```
[Agent reads skills and prompt]
     ↓
[Agent decides what to do next]
     ↓
[Tool call] → [Result] → [Agent reasons about result]
     ↓
[Agent decides: iterate or done?]
```

The agent decides based on:
- Skill instructions
- Tool feedback
- Quality standards in prompt

### Code Comparison

**LangGraph Node:**
```python
def critic_node(state: ContentGeneratorState) -> ContentGeneratorState:
    """Fixed function that evaluates drafts."""
    drafts = state["drafts"]
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": critic_prompt(drafts)}]
    )
    feedback = parse_critic_response(response)
    return {"critic_feedback": feedback, "iteration": state["iteration"] + 1}
```

**Claude Agent SDK (in MCP tool):**
```python
@mcp.tool()
def critique_draft(channel: str, headline: str, body: str, cta: str, claims: list) -> dict:
    """Tool that Claude calls when it wants to evaluate a draft."""
    # Deterministic scoring logic
    brand_voice_score = calculate_brand_voice_score(body, headline)
    cta_clarity_score = calculate_cta_score(cta)
    return {
        "brand_voice_score": brand_voice_score,
        "cta_clarity_score": cta_clarity_score,
        "feedback_string": generate_feedback(...)
    }
```

The difference: LangGraph node is **always called** in the graph. The MCP tool is **called when Claude decides to**.

### Iteration Logic Comparison

**LangGraph:**
```python
def should_continue(state):
    if state["iteration"] >= 3:
        return "export"
    if not state["critic_feedback"].passed:
        return "draft"  # Loop back
    if has_unsupported_claims(state):
        return "draft"  # Loop back
    return "export"
```

**Claude Agent SDK:**
Claude reads the skill that says:
> "If brand voice score < 7 or CTA clarity score < 7, revise the draft and critique again."

And decides whether to iterate based on the feedback it received.

---

## When to Use Each Approach

### Use Claude Agent SDK When:

1. **Exploratory workflows** - You don't know the exact steps in advance
2. **Flexible iteration** - Quality depends on content, not fixed thresholds
3. **Natural language reasoning** - You want to see Claude's thought process
4. **Rapid prototyping** - Faster to describe skills than code graph nodes
5. **Complex decision making** - Multiple factors influence next steps

### Use LangGraph When:

1. **Compliance-critical workflows** - Every step must be auditable and repeatable
2. **Guaranteed execution order** - Certain steps must always run
3. **Deterministic behavior** - Same input must produce same path
4. **Fine-grained control** - Need to inject logic between every step
5. **Cost optimization** - Minimize LLM calls with explicit branching

### Hybrid Approach

You can combine both:
- Use LangGraph for the outer workflow (retrieve → generate → verify)
- Use Claude Agent SDK for complex sub-tasks (drafting with iteration)

---

## Observability

### Audit Log Structure

```json
{
  "started_at": "2026-01-06T10:30:00Z",
  "completed_at": "2026-01-06T10:32:15Z",
  "tool_calls": [
    {"tool": "mcp__brandguard__retrieve_context", "timestamp": "..."},
    {"tool": "mcp__brandguard__critique_draft", "timestamp": "..."},
    {"tool": "mcp__brandguard__verify_claims", "timestamp": "..."},
    {"tool": "mcp__brandguard__save_output", "timestamp": "..."}
  ],
  "messages": [
    {"type": "text", "content": "I'll start by retrieving brand context..."}
  ]
}
```

### Analyzing Agent Behavior

Run the analyzer to see what the agent did:

```bash
python3 -m src.runner analyze
```

Output:
```
=== Run Analysis ===
Success: True
Iterations: 1
Flags: []

Tool sequence: retrieve_context → retrieve_context → critique_draft → verify_claims → save_output

Tool counts: {'retrieve_context': 2, 'critique_draft': 1, 'verify_claims': 1, 'save_output': 1}

Observations:
  - Agent correctly retrieved context first
  - Agent critiqued drafts 1 times
  - Agent verified claims 1 times
```

---

## Summary

| Characteristic | Claude Agent SDK | LangGraph |
|----------------|------------------|-----------|
| **Philosophy** | "Tell the agent what to achieve" | "Tell the system what to do" |
| **Control** | Trust + verify | Explicit + deterministic |
| **Debugging** | Watch reasoning | Trace graph execution |
| **Flexibility** | High (agent adapts) | Low (graph is fixed) |
| **Predictability** | Medium (emergent behavior) | High (defined paths) |
| **Developer Experience** | Natural language skills | Python code nodes |

The Claude Agent SDK approach treats the agent as a **capable colleague** who understands the domain and can make decisions. The LangGraph approach treats the workflow as a **state machine** where every transition is explicitly programmed.

Both are valid. Choose based on your needs for control vs. flexibility.

---

## Future Trajectory

### The Long-Term Bet

As AI capabilities improve, the calculus shifts:

| Timeframe | Better Choice | Why |
|-----------|--------------|-----|
| **Today** | LangGraph (for defined workflows) | More reliable, predictable, observable |
| **Near future** | Parity | AI reliability improves |
| **Further out** | Agent SDK | AI optimizes better than static graphs |

### Why Agent SDK Wins Long-Term

Today's arguments for LangGraph:
- AI reasoning is expensive (tokens, latency)
- AI sometimes doesn't follow instructions
- We need predictability for business users

But these are **temporary limitations**, not fundamental truths.

When AI becomes significantly smarter:
1. **Dynamic workflow optimization**: The agent realizes "for THIS event type, I should do deeper research first"
2. **Emergent strategies**: The agent discovers approaches humans wouldn't think to graph
3. **Self-improvement**: The agent learns from past runs what works best
4. **The graph becomes a ceiling**: If the AI is smarter than the human who drew the graph, the graph limits potential

### The Analogy

- **LangGraph** = Detailed instructions for a junior developer (guardrails prevent mistakes)
- **Agent SDK** = Goals for a senior developer (autonomy finds better solutions)

You give juniors explicit steps because they might mess up. You give seniors autonomy because they'll find the better path.

### Building for the Future

Building with Agent SDK now is a **forward-thinking architectural bet**:
- You're trading some current-state optimization for future flexibility
- As AI improves, your architecture improves automatically
- No graph refactoring needed when capabilities increase

The question isn't "which is better?" but "which is the right long-term bet?"
