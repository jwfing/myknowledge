# Requirements & Implementation Plan

## Problem Statement
When developing products, switching between different agents/projects causes knowledge to become isolated information silos that cannot be leveraged globally. We aim to build a knowledge sharing service that stores and utilizes all personal knowledge and experience, enhancing agent capabilities.

## Memory Model

### Knowledge Type Classification
All knowledge is classified into the following categories:
- **Semantic Memory**: Factual knowledge — objective facts, definitions, rules. Example: "The InsForge platform project uses PKCE flow for OAuth, token endpoint at /api/v1/oauth/token", etc.
- **Episodic Memory**: Experiential knowledge — processes and outcomes of specific events. Example: "Got CORS error last time when calling OAuth, cause was redirect_uri not whitelisted", etc.
- **Procedural Memory**: Procedural knowledge — workflows, conventions, operational steps. Example: "Team convention: all APIs must have OpenAPI spec written first, then generate SDK", etc.

### Storage Hierarchy
Following the Letta/MemGPT approach, memory is organized into four layers based on proximity to the agent's context window:
- **Core Memory**: Always in context, e.g., system prompt, CLAUDE.md, etc.
- **Message Buffer**: Recent N conversation turns, e.g., sliding window, summaries, etc.
- **Archival Memory**: Long-term knowledge, retrieved on demand, e.g., vector database, knowledge graph, etc.
- **Recall Memory**: Raw conversation history, e.g., message list.

This product primarily operates at the Archival Memory layer, addressing long-term knowledge storage and retrieval across projects and conversations, while influencing the Core Memory layer via MCP (injecting retrieval results into context).


## Implementation Plan

### Collection Layer
Primarily used to extract raw information from development conversations, through two methods:
- Claude Code Hooks (Background Path)
- MCP Tool (Hot Path)

#### Background Path (Primary path, ensuring coverage)
Principle: After a conversation ends, a background process automatically processes the conversation content and extracts memories. Does not rely on the agent proactively calling save, solving the core problem of "agent forgets to save."
Implementation:
Claude Code Hooks: Configure a PostConversation hook in .claude/hooks/ that automatically triggers a script after each conversation ends, sending the current session's conversation content to the backend API.

#### Hot Path (Auxiliary path, improving quality)
Principle: Expose a `remember_this` tool via MCP Server, allowing agents to proactively mark important information during conversations. Memories saved this way receive higher confidence weights.
MCP Server exposed Tools:
- **remember_this**: Proactively save a knowledge snippet with classification tags. Trigger: When the agent determines current information has long-term value.
- **query_memory**: Semantic retrieval of related memories, returning concise results. Trigger: Automatically called when the agent needs cross-project knowledge.
- **list_projects**: List all user projects and their knowledge summaries. Trigger: When the agent needs to understand the user's overall project landscape.

### Distillation Layer
Primarily used to extract structured knowledge from raw conversations, using LLM extraction + classification/tagging to perform key information extraction from data collected by the collection layer. This is the product's core competitive advantage. 90% of raw conversations is debugging noise; the distillation layer's job is to extract truly valuable knowledge snippets from it.

Distillation Pipeline (Async):
- **Conversation Segmentation**: Split long conversations into topic-based segments, each corresponding to an independent development task or decision point.
- **Knowledge Extraction**: Use LLM to extract structured knowledge from each segment. Extracted information includes: involved entities (projects, APIs, tech components), key decisions and their rationale, specific configuration parameters and code snippets, debugging experiences and solutions.
- **Classification & Tagging**: Classify as Semantic / Episodic / Procedural, while adding project tags, tech stack tags, and importance scores.
- **Deduplication & Merging**: If newly extracted knowledge conflicts with existing memories (e.g., API upgraded to v2), update rather than simply append. New information overwrites old; old versions are downweighted but preserved.

Reference structure for extracted knowledge snippets:

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique identifier |
| content | text | Distilled knowledge summary (natural language) |
| embedding | vector(1536) | Semantic vector for similarity search |
| memory_type | enum | semantic \| episodic \| procedural |
| project_id | UUID | Source project |
| entities | jsonb | List of involved entities (projects, APIs, components, etc.) |
| importance | float (0-1) | Importance score, Hot Path saves default to higher values |
| tags | text[] | Tech stack, business domain, and other tags |
| created_at | timestamp | Creation time, used for time decay calculation |
| source_session | UUID | Reference to original conversation session, for traceability |


### Storage Layer
Persistent storage for knowledge snippets and entity relationships, implemented directly with PostgreSQL + pgvector.

The industry consensus is that vector databases and knowledge graphs each have their strengths, and hybrid use yields the best results. Initially, we use a single PostgreSQL + pgvector database to cover both capabilities:

#### Vector Search (Semantic Search)
Suitable for: Fuzzy queries, e.g., "Have I done a similar authentication solution before?"
Implementation: Generate embeddings using the local paraphrase-multilingual-mpnet-base-v2 model, stored in pgvector's vector(768) field. At retrieval time, use cosine similarity for initial filtering, combined with metadata filtering (project, tags, time) for re-ranking.

#### Entity Relationships (Structured Queries)
Suitable for: Precise queries, e.g., "What APIs does the platform project expose?"
Implementation: Model a lightweight knowledge graph with three PostgreSQL tables — entities (entity table: Project / API / Component / TechStack / Config), relations (relationship table: exposes / depends_on / uses / configured_with), memory_entity_links (memory-entity association table). At retrieval time, use SQL JOINs to query entity relationships, then fetch associated memory snippets.

### Retrieval Layer
Retrieval cannot rely on a single dimension; multiple signals must be combined for comprehensive ranking. Following Arize's recommendations, we use a three-dimensional scoring model:

Final score = α × semantic_similarity + β × importance + γ × recency

| Dimension | Calculation | Purpose |
|-----------|-------------|---------|
| Semantic Similarity | cosine_similarity(query_embedding, memory_embedding) | Ensures returned memories are semantically relevant to the query |
| Importance | importance field (LLM scoring + Hot Path weighting) | Prioritizes high-value knowledge, filters out debugging noise |
| Recency | e^(-λ × age_days), exponential decay | Newer knowledge takes priority over older knowledge, avoids returning outdated information |

When returning results, token usage must be controlled. Following Context Engineering principles, each query returns at most 3-5 of the most relevant memory snippets, with total tokens kept under 2000 to avoid crowding out the agent's available context.

### Service Layer
Based on the functionality described above, the service layer primarily provides:
- MCP Server endpoints
- Ingest endpoint needed for data import via the Background Path

We do NOT need:
- User registration/login or multi-tenant functionality, as this is not a SaaS platform

### Overall Tech Stack
- **Collection**
  - Choice: Claude Code Hooks + MCP
  - Rationale: Dual-path ensures coverage; Hooks are an officially supported extension point

- **Distillation**
  - Choice: Claude Haiku 4.5, using LLM services provided by OpenRouter
  - Rationale: Async processing doesn't need the most powerful model; prioritize cost-effectiveness

- **Vectorization**
  - Choice: Local paraphrase-multilingual-mpnet-base-v2 model for embedding generation
  - Rationale: Good balance of performance and cost; 768 dimensions are sufficient for development knowledge scenarios

- **Storage**
  - Choice: PostgreSQL + pgvector
  - Rationale: Single tech stack covers vector search + relational storage + entity relationships; simple to operate

- **Backend**
  - Choice: Python FastAPI + MCP
  - Rationale: Lightweight API service, providing both REST API and MCP Server

- **MCP Server**
  - Choice: @modelcontextprotocol/sdk, streamable HTTP mode
  - Rationale: Official SDK, supports both stdio and HTTP transport