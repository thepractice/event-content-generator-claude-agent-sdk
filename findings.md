# BrandGuard Autonomous Agent: Findings

## The Experiment

Built a marketing content agent with maximum autonomy using the Claude Agent SDK architecture:
- **Skills** for domain expertise (markdown files in `.claude/skills/`)
- **MCP** for custom tools (retrieve, critique, verify, images, save)
- **Host Runner** for invariant enforcement (max iterations, schema validation)

---

## Architecture: Skills + MCP

### What Worked Well

**Skills**:
- [x] Agent read and followed the SOP skill
- [x] Brand voice guidelines influenced content tone
- [x] Channel rules were respected
- [x] Verification rules were applied

**MCP Tools**:
- [x] `retrieve_context` was called for grounding
- [x] `critique_draft` was used for self-evaluation
- [x] `verify_claims` was called before submission
- [x] `generate_images` was executed after content
- [x] `save_output` bundled everything correctly

**Host Runner**:
- [x] Iteration cap prevented infinite loops
- [x] Schema validation caught malformed outputs
- [x] Unverified claims triggered re-runs

### What Needed Improvement

1. **Skills aren't observable** - Unlike tool calls, skill "usage" isn't logged as discrete events. Skills are loaded as context, not invoked. We added a `skills_loaded` notification to show which skills were available.

2. **MCP subprocess env vars** - API keys weren't automatically passed to the MCP subprocess. Had to explicitly pass `GEMINI_API_KEY` in the `mcp_servers` env config.

3. **Image generation SDK** - Initial implementation used older `google.generativeai` SDK. Had to update to `google.genai` with `gemini-2.5-flash-image` model to match the working LangGraph version.

---

## Key Framing: Orchestrated vs Autonomous

The best way to describe the difference:

| Frame | LangGraph | Claude Agent SDK |
|-------|-----------|------------------|
| **Orchestrated vs Autonomous** | You orchestrate | Agent decides |
| **Explicit vs Emergent** | You define the graph | Workflow emerges |
| **Procedural vs Goal-oriented** | "Do these steps" | "Achieve this goal" |

**The one-liner:** LangGraph defines **how**. Agent SDK defines **what**.

**Who decides the workflow?** That's the fundamental question.

---

## The Long-Term Bet

### Why LangGraph is Better Today (for defined workflows)
- More reliable and predictable
- Better observability (every node traced)
- Lower cost (no reasoning about "what next")
- Easier debugging

### Why Agent SDK Wins Long-Term

Today's LangGraph advantages are **temporary limitations**, not fundamental truths:
- AI reasoning cost will decrease
- AI reliability will increase
- AI will eventually optimize better than human-drawn graphs

When AI becomes smarter:
1. **Dynamic optimization**: Agent adapts workflow to context
2. **Emergent strategies**: Agent discovers approaches humans wouldn't graph
3. **The graph becomes a ceiling**: If AI > human who drew graph, graph limits potential

### The Analogy
- **LangGraph** = Instructions for a junior developer (guardrails)
- **Agent SDK** = Goals for a senior developer (autonomy)

---

## UI Learnings

### Realtime Progress Updates

Implemented progress callbacks to show agent activity:
- `started` - Agent begins
- `skills_loaded` - Which skills are available
- `tool_call` - Each MCP tool invocation
- `reasoning` - Agent's thinking (truncated)
- `validation` - Quality check results
- `completed` - Agent finishes

Key insight: Progress must persist after completion. Used `st.session_state.progress_log` to keep updates visible.

### Optimal UI for Marketing Teams

| UI | Best For |
|---|---|
| **Slack bot** | Quick requests, no context switch |
| **Web app** | Full creation, editing, review |
| **Google Docs** | Stakeholder collaboration |
| **API** | Marketing automation integration |

Terminal UI is wrong for marketers - they're not developers.

---

## Comparison Summary

| Aspect | LangGraph | Claude Agent SDK |
|--------|-----------|------------------|
| **Philosophy** | "Tell the system what to do" | "Tell the agent what to achieve" |
| **Control** | Explicit + deterministic | Trust + verify |
| **Flexibility** | Low (graph is fixed) | High (agent adapts) |
| **Predictability** | High | Medium |
| **Future trajectory** | Static | Improves with AI |

---

## Recommendations

### Use Agent SDK When:
- Exploratory/creative tasks
- Workflow isn't fully defined
- Betting on AI improvement
- Rapid prototyping

### Use LangGraph When:
- Compliance-critical workflows
- Guaranteed execution order required
- Deterministic behavior essential
- Cost optimization critical

### The Right Question

Not "which is better?" but "which is the right long-term bet?"

Building with Agent SDK now trades current-state optimization for future flexibility. As AI improves, your architecture improves automatically.

---

*Last updated: 2026-01-08*
