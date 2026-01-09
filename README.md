# BrandGuard: Autonomous Marketing Content Agent

An autonomous marketing content generator built with the **Claude Agent SDK** using the Skills + MCP architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLAUDE AGENT SDK RUNTIME                        │
│                                                                     │
│   SKILLS (Domain Expertise)          MCP SERVER (Custom Tools)     │
│   ├── brandguard-sop                 ├── retrieve_context          │
│   ├── brand-voice                    ├── critique_draft            │
│   ├── channel-rules                  ├── verify_claims             │
│   └── verification                   └── generate_images           │
│                                                                     │
│   HOOKS                              HOST RUNNER                    │
│   ├── PreToolUse (guard)             ├── Max iterations            │
│   └── PostToolUse (audit)            └── Schema validation         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Install Claude Code CLI

The Claude Agent SDK requires the Claude Code CLI to be installed first:

```bash
# macOS/Linux/WSL
curl -fsSL https://claude.ai/install.sh | bash

# Or via Homebrew
brew install --cask claude-code

# Or via npm
npm install -g @anthropic-ai/claude-code
```

### 2. Set up API Keys

```bash
# Required: Anthropic API key
export ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Gemini API key for image generation
export GEMINI_API_KEY=your_gemini_api_key
```

## Installation

```bash
# Clone or navigate to the project
cd event-content-generator-claude-agent-sdk

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Note:** If `claude-agent-sdk` fails to install, the app will fall back to using the direct Anthropic API with the same tool definitions.

## Quick Start

### 1. Set up environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Index the corpus

```bash
python3 -c "from src.rag.ingest import ingest_documents; print(ingest_documents(force_reingest=True))"
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

### 4. Or run from command line

```bash
python3 -m src.runner
```

## Project Structure

```
event-content-generator-claude-agent-sdk/
├── CLAUDE.md                           # Agent identity
├── .claude/skills/                     # Skills (domain expertise)
│   ├── brandguard-sop/SKILL.md         # Complete workflow
│   ├── brand-voice/SKILL.md            # Tone/style guidelines
│   ├── channel-rules/SKILL.md          # Platform constraints
│   └── verification/SKILL.md           # Claim verification rules
├── brandguard_mcp/
│   └── server.py                       # MCP server (4 tools)
├── src/
│   ├── agent.py                        # SDK client + hooks
│   ├── runner.py                       # Host enforcement
│   ├── schemas.py                      # Pydantic models
│   └── rag/                            # Vector search
├── corpus/                             # Brand documents
├── output/                             # Generated content
├── app.py                              # Streamlit UI
└── findings.md                         # Document learnings
```

## How It Works

### The Agent's Workflow

1. **Retrieve Context** - Searches the knowledge base for brand voice and product info
2. **Draft Content** - Writes content for each requested channel
3. **Critique Drafts** - Scores quality (brand voice, CTA clarity, length)
4. **Verify Claims** - Checks all factual claims against source documents
5. **Generate Images** - Creates marketing visuals with Gemini
6. **Save Output** - Packages final bundle to `output/bundle.json`

### Quality Gates

- Brand voice score >= 7
- CTA clarity score >= 7
- Length within channel limits
- ALL claims must be verified

### Host Enforcement

The host runner doesn't trust the agent to self-terminate:
- **Max iterations** - Prevents infinite loops (configurable via `MAX_ITERATIONS`)
- **Schema validation** - Ensures output format is correct
- **Claim verification** - Double-checks no unverified claims

## MCP Tools

| Tool | Description |
|------|-------------|
| `retrieve_context` | RAG search from ChromaDB (brand or product) |
| `critique_draft` | Deterministic quality scoring with feedback |
| `verify_claims` | Embedding-based citation matching |
| `generate_images` | Gemini Imagen API for marketing visuals |

## Behaviors to Observe

When running the agent, watch for:

1. **Does it retrieve first?** (grounding behavior)
2. **Does it critique its work?** (self-correction)
3. **Does it verify claims?** (no hallucination)
4. **Does it iterate on failure?** (quality pursuit)
5. **What's the tool sequence?** (emergent process)

Document your observations in `findings.md`!

## Comparison: LangGraph vs Claude Agent SDK

| Aspect | LangGraph | Claude Agent SDK |
|--------|-----------|------------------|
| **Workflow** | Explicit graph (nodes + edges) | Emergent (agent decides) |
| **Decision Making** | `should_continue()` function | Claude's reasoning |
| **Tools** | Python functions in nodes | MCP server (subprocess) |
| **Iteration** | Counter + conditional edge | Agent decides + host caps |
| **State** | TypedDict passed between nodes | Agent manages internally |
| **Observability** | LangSmith traces | Audit log + tool calls |

### Key Insight

**LangGraph**: "Tell the system what to do" - You define every node and edge explicitly. The graph executes deterministically.

**Claude Agent SDK**: "Tell the agent what to achieve" - You provide skills (domain knowledge) and tools (capabilities). The agent reasons about what to do.

For detailed comparison, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Testing

Run the unit tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_components.py::TestCritiqueDraft -v
```

Tests cover:
- MCP tools (critique_draft, verify_claims)
- Pydantic schemas and validation
- RAG retrieval functionality

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for Claude Agent SDK |
| `GEMINI_API_KEY` | No | API key for image generation |
| `CLAUDE_MODEL` | No | Model to use (default: `claude-sonnet-4-20250514`) |

### Model Options

```bash
# Use Sonnet (default - faster, cheaper)
export CLAUDE_MODEL=claude-sonnet-4-20250514

# Use Opus (more capable, slower)
export CLAUDE_MODEL=claude-opus-4-5-20250514
```

## Documentation

- [Architecture & Comparison](docs/ARCHITECTURE.md) - Deep dive into how the agent works and comparison with LangGraph
- [Findings](findings.md) - Learnings from building and testing the agent

## License

MIT
