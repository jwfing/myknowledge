# RememberIt

**Agent Memory Service for Cross-Project Knowledge Sharing**

When developing with AI coding agents like Claude Code or Codex, each project and each conversation becomes an isolated information silo. rememberit automatically distills valuable knowledge from development conversations (technical decisions, API designs, debugging experiences), stores them in a unified memory bank, and lets you query historical knowledge from any project via MCP.

## How It Works

```
Claude Code Conversation
       │
       ├─── Stop Hook (auto) ──→ POST /api/v1/ingest ──→ LLM Distillation ──→ Store in DB
       │                           (Background Path)
       └─── remember_it (manual) ──→ Store directly in DB
              recall_memory ←────── Vector Search + Entity Matching + 3-Dimensional Scoring
              (Hot Path via MCP)
```

**Dual-Path Collection**: The Background Path automatically collects knowledge via Claude Code Hooks after each conversation ends, ensuring coverage; the Hot Path lets agents proactively save and query knowledge via MCP Tools, improving quality.

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend Framework | Python + FastAPI |
| MCP Server | Python MCP SDK (streamable HTTP) |
| Database | PostgreSQL + pgvector |
| Embedding | sentence-transformers (paraphrase-multilingual-mpnet-base-v2, runs locally) |
| Knowledge Distillation | Claude Haiku 4.5 via OpenRouter |

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -e .
```

The embedding model (~400MB) will be automatically downloaded from HuggingFace on first run.

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in the required configuration:

```bash
# Required: PostgreSQL connection string (pgvector extension must be installed)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/rememberit

# Required: OpenRouter API Key (used for knowledge distillation)
OPENROUTER_API_KEY=sk-or-v1-xxx
```

### 3. Initialize Database

Make sure your PostgreSQL instance has the pgvector extension installed, then run migrations:

```bash
cd backend
alembic upgrade head
```

### 4. Start Server

```bash
cd backend
python -m rememberit
```

This starts a single server on port 6789 with both the REST API (`/api/v1/*`) and MCP endpoint (`/mcp`).

## Integrating with Claude Code

### Install MCP Server

Add MCP Server configuration in Claude Code:

```bash
claude mcp add --transport http --scope user rememberit http://127.0.0.1:6789/mcp
```

Or manually edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "rememberit": {
      "type": "http",
      "url": "http://localhost:6789/mcp"
    }
  }
}
```

Once configured, agents in Claude Code can use these three tools:

| Tool | Purpose | Example |
|------|---------|---------|
| `recall_memory` | Semantic search across cross-project knowledge | "How do I call the OAuth API in the platform project?" |
| `remember_it` | Proactively save important knowledge | Save key decisions, API designs, etc. |
| `list_projects` | View all projects and their knowledge summary | Get an overview of all projects |

### Install Claude Code Hook (Auto-Collection)

The hook automatically sends conversation content to the API for knowledge distillation when each Claude Code conversation ends.

**Option 1: One-Click Install**

```bash
./backend/scripts/claude-hook/install_hook.sh
```

**Option 2: Manual Configuration**

Edit `~/.claude/settings.json` and add the following to the `hooks` field:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /absolute/path/to/rememberit/backend/scripts/claude-hook/claude_hook.py",
            "async": true
          }
        ]
      }
    ]
  }
}
```

**Optional Environment Variables** (add to your shell profile):

```bash
# API address (default: http://localhost:6789)
export REMEMBERIT_API_URL=http://localhost:6789

# Manually specify project name (auto-inferred from git remote or directory name if not set)
export REMEMBERIT_PROJECT=my-project
```

After installation, run `claude /hooks` to verify — you should see the Stop hook listed under `[User]`.

## Project Structure

```
memor.ai/
├── backend/                          # Python 后端
│   ├── pyproject.toml                #   项目配置 & 依赖
│   ├── alembic.ini                   #   数据库迁移配置
│   ├── src/rememberit/
│   │   ├── config.py                 #   Environment variable configuration
│   │   ├── types.py                  #   Pydantic models, enums
│   │   ├── __main__.py               #   Entry point: python -m rememberit
│   │   ├── api/                      #   FastAPI REST API (also mounts MCP)
│   │   │   ├── app.py                #     Application factory, mounts MCP at /mcp
│   │   │   └── routes/
│   │   │       ├── ingest.py         #     POST /api/v1/ingest (Background Path)
│   │   │       └── health.py         #     GET /api/v1/health
│   │   ├── mcp/                      #   MCP Server (Hot Path, mounted at /mcp)
│   │   │   └── server.py             #     3 tools: remember_it, recall_memory, list_projects
│   │   ├── extraction/               #   Distillation layer
│   │   │   ├── pipeline.py           #     Async pipeline: segmentation → LLM → dedup → store
│   │   │   └── llm_client.py         #     OpenRouter Claude Haiku client
│   │   ├── storage/                  #   Storage layer
│   │   │   ├── db.py                 #     AsyncPG connection pool
│   │   │   ├── models.py             #     SQLAlchemy ORM for 6 tables
│   │   │   ├── repository.py         #     Data access layer
│   │   │   └── migrations/           #     Alembic migrations
│   │   └── retrieval/                #   Retrieval layer
│   │       ├── embedding.py          #     Local embedding model (singleton cache)
│   │       ├── search.py             #     Hybrid retrieval: vector + entity + scoring
│   │       └── scorer.py             #     score = α×similarity + β×importance + γ×recency
│   ├── tests/                        #   Python tests
│   └── scripts/
│       ├── claude-hook/              #   Claude Code Stop hook
│       │   ├── claude_hook.py
│       │   └── install_hook.sh
│       └── macOS-service/            #   macOS launchd service
│           ├── install_service.sh
│           └── uninstall_service.sh
├── .env                              # 环境变量（前后端共享）
├── .env.example
└── README.md
```

## Database Schema

6 tables in total:

- **projects** — Project information, tech stack tags
- **memories** — Core memory table, containing content, embedding vectors, type classification, importance scores
- **entities** — Entity graph nodes (Project / API / Component / TechStack / Config)
- **relations** — Entity relationships (exposes / depends_on / uses / configured_with)
- **memory_entity_links** — Links between memories and entities
- **conversations** — Raw conversation storage, for traceability and re-distillation

## Memory Model

Knowledge is classified and stored in three types:

| Type | Meaning | Example |
|------|---------|---------|
| **Semantic** | Factual knowledge | "OAuth uses PKCE flow, token endpoint: POST /api/v1/oauth/token" |
| **Episodic** | Experiential knowledge | "Got CORS error when calling OAuth, cause was redirect_uri not whitelisted" |
| **Procedural** | Procedural knowledge | "Team convention: all APIs must have OpenAPI spec written first, then generate SDK" |

Retrieval uses a three-dimensional composite scoring model:

```
score = 0.5 × semantic_similarity + 0.3 × importance + 0.2 × recency
```

Each query returns at most 3-5 results, with total tokens kept under 2000 to avoid crowding out the agent's available context.

## License

MIT