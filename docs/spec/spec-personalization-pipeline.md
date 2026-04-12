# Personalization Pipeline

Three-phase pipeline that recommends, evolves, and creates AI tools from user session history. Crawls GitHub to build a catalog of 10,000+ items spanning skills, subagents, commands, hooks, and repos (including MCP servers). Replaces the current 299-skill static retrieval.

## Purpose

Turn session history into a personalized agent setup through three phases:

1. **Recommend** (new): Search a self-built catalog of 10,000+ AI tools discovered from GitHub. Return ranked matches with LLM-generated rationale. Produce an agent-executable installation plan.
2. **Evolve** (existing): Improve installed agent elements (skills, subagents, commands, hooks) based on observed usage patterns. Detect conflicts between element instructions and actual behavior, then generate granular edits.
3. **Create** (existing): Generate new agent elements (SKILL.md, AGENT.md, commands, hooks) for workflow patterns no catalog item covers.

The pipeline is the primary onboarding experience. Users follow a funnel: Recommend -> Install -> Evolve -> Create.

## Architecture

```
Phase 1: RECOMMEND                    Phase 2: EVOLVE              Phase 3: CREATE
                                      (after days of usage)        (fill remaining gaps)

10M tokens   5-10K    500     top-15   final
(sessions)--L1-->(signals)--L2-->(profile)--L3-->(candidates)--L4-->(recommendations)
            local    LLM     retrieval   LLM      installed elements       uncovered patterns
            5-10s   15-25s     <1s      15-25s         |                      |
                                                       v                      v
                                                  proposals -> edits    proposals -> element files
                                                  (2-4 LLM calls)      (2-4 LLM calls)
```

Phase 1 uses 2 LLM calls, 35-60 seconds. Phases 2 and 3 are the existing evolution/creation pipelines.

## Repo Structure

Three separate domains: recommendation (all tool types), creation (new elements), and evolution (improve existing elements). Prompts move from `llm/prompts/` to a top-level `prompts/` package.

### Changes Summary

```
NEW directories:
  models/recommendation/            — catalog, profile, result models
  models/creation/                  — element creation models
  models/evolution/                 — element evolution models
  models/friction/                  — friction models (from models/analysis/)
  models/session/                   — session insight models (from models/analysis/)
  services/recommendation/          — recommendation pipeline
  services/recommendation/crawler/  — GitHub self-discovery
  services/creation/                — element creation pipeline
  services/evolution/               — element evolution pipeline
  prompts/                          — all LLM prompt definitions (moved from llm/prompts/)
  api/recommendation.py             — recommendation endpoints
  schemas/recommendation.py         — recommendation request/response

NEW files:
  models/enums.py                   — add ElementType (shared enum)
  models/step_ref.py                — moved from models/analysis/step_ref.py
  services/shared.py                — cross-pipeline utilities (parse_llm_output, etc.)

MOVED directories:
  llm/prompts/ → prompts/           — prompt definitions become top-level vibelens package

DISSOLVED:
  models/analysis/                  — split into models/friction/, models/session/, models/step_ref.py

DELETED files:
  models/skill/retrieval.py         — replaced by models/recommendation/
  models/skill/patterns.py          — SkillMode removed; WorkflowPattern → models/session/
  models/skill/creation.py          — generalized to models/creation/
  models/skill/evolution.py         — generalized to models/evolution/
  models/skill/results.py           — split into models/creation/ and models/evolution/
  services/skill/retrieval.py       — replaced by services/recommendation/
  services/skill/creation.py        — generalized to services/creation/
  services/skill/evolution.py       — generalized to services/evolution/
  services/skill/shared.py          — cross-pipeline parts → services/shared.py
  services/skill/store.py           — split into creation and evolution stores
  services/skill/mock.py            — split into creation and evolution mocks
  services/skill/download.py        — moved to services/recommendation/
  services/skill/importer.py        — moved to services/recommendation/
  llm/prompts/skill_retrieval.py    — replaced by prompts/recommendation.py
  llm/prompts/skill_creation.py     — moved to prompts/creation.py
  llm/prompts/skill_evolution.py    — moved to prompts/evolution.py

MODIFIED files:
  models/enums.py                   — add ElementType enum
  config/settings.py                — add catalog_update_url, catalog_auto_update, catalog_check_interval_hours
  api/skill_analysis.py             — split into api/creation.py and api/evolution.py
  api/__init__.py                   — add recommendation, creation, evolution routers
  schemas/skills.py                 — split into schemas/creation.py and schemas/evolution.py
  deps.py                           — add get_recommendation_store()
  cli.py                            — add build-catalog and update-catalog commands
```

### New Structure

All paths below are relative to `src/vibelens/`.

```
models/
├── enums.py                           # MODIFIED — add ElementType (shared by creation + evolution)
├── step_ref.py                        # MOVED from analysis/ — cross-cutting step locator
├── recommendation/                    # NEW — recommendation domain models
│   ├── __init__.py
│   ├── catalog.py                     # CatalogItem, ItemType, ITEM_TYPE_LABELS, FILE_BASED_TYPES
│   ├── profile.py                     # UserProfile
│   └── results.py                     # RecommendationResult, CatalogRecommendation
├── creation/                          # NEW (from models/skill/creation.py, generalized)
│   ├── __init__.py
│   ├── models.py                      # ElementCreation, ElementCreationProposal
│   └── results.py                     # CreationResult
├── evolution/                         # NEW (from models/skill/evolution.py, generalized)
│   ├── __init__.py
│   ├── models.py                      # ElementEvolution, ElementEvolutionProposal, ElementEdit
│   └── results.py                     # EvolutionResult
├── friction/                          # MOVED from analysis/friction.py
│   ├── __init__.py
│   └── models.py                      # FrictionAnalysisResult, FrictionType, FrictionCost, Mitigation
├── session/                           # MOVED from analysis/ — session-level insight models
│   ├── __init__.py
│   ├── correlator.py                  # CorrelatedGroup, CorrelatedSession
│   ├── phase.py                       # PhaseSegment
│   └── tool_graph.py                  # ToolDependencyGraph, ToolEdge
├── skill/                             # EXISTING — skill info + source only
│   ├── info.py                        # SkillInfo
│   └── source.py                      # SkillSource, SkillSourceType
├── dashboard/                         # EXISTING (unchanged)
└── trajectories/                      # EXISTING (unchanged)

services/
├── shared.py                          # NEW — cross-pipeline utilities (parse_llm_output, merge_batch_refs, validate_patterns)
├── recommendation/                    # NEW — recommendation pipeline
│   ├── __init__.py                    # exports: analyze_recommendation, estimate_recommendation
│   ├── engine.py                      # L1-L4 orchestration, background job
│   ├── retrieval.py                   # TF-IDF search, pluggable RetrievalBackend ABC
│   ├── scoring.py                     # Multi-signal weighted scoring
│   ├── catalog.py                     # Runtime: load catalog.json, auto-update check
│   ├── installer.py                   # Generate agent-executable installation plans
│   ├── download.py                    # MOVED from skill/ — GitHub download (used by installer)
│   ├── importer.py                    # MOVED from skill/ — agent CLI import (used by installer)
│   ├── store.py                       # RecommendationStore (AnalysisStore subclass)
│   ├── mock.py                        # Demo recommendation data
│   └── crawler/                       # Build-time: GitHub self-discovery
│       ├── __init__.py
│       ├── github.py                  # GitHub Search + Contents + Repos API
│       ├── classifier.py              # Auto-classify repos/files into ItemType
│       ├── scorer.py                  # Quality scoring (stars, forks, recency, etc.)
│       ├── builder.py                 # Orchestrate: search → fetch → classify → score → catalog.json
│       └── seeds.py                   # Curated seed repos + search queries
├── creation/                          # NEW (from services/skill/creation.py, generalized)
│   ├── __init__.py                    # entry point: analyze_creation, estimate_creation
│   ├── pipeline.py                    # two-step: proposal → generation
│   ├── store.py                       # CreationStore (AnalysisStore subclass)
│   └── mock.py                        # demo data
├── evolution/                         # NEW (from services/skill/evolution.py, generalized)
│   ├── __init__.py                    # entry point: analyze_evolution, estimate_evolution
│   ├── pipeline.py                    # two-step: proposal → edit generation
│   ├── store.py                       # EvolutionStore (AnalysisStore subclass)
│   └── mock.py                        # demo data
└── (other existing service dirs unchanged)

prompts/                               # MOVED from llm/prompts/ — top-level within vibelens package
├── __init__.py                        # PROMPT_REGISTRY
├── recommendation.py                  # NEW — profile generation + rationale prompts
├── creation.py                        # MOVED from skill_creation.py, generalized
├── evolution.py                       # MOVED from skill_evolution.py, generalized
├── friction_analysis.py               # MOVED (unchanged)
└── templates/                         # Jinja2 templates
    ├── recommendation/                # NEW — profile + rationale templates
    ├── creation/                      # MOVED from skill/ — creation templates
    ├── evolution/                     # MOVED from skill/ — evolution templates
    └── friction/                      # MOVED (unchanged)

api/
├── recommendation.py                  # NEW — recommendation + install endpoints
├── creation.py                        # RENAMED from skill_analysis.py — creation only
├── evolution.py                       # NEW — evolution only
├── skill_management.py                # UNCHANGED
└── (other existing API files unchanged)

schemas/
├── recommendation.py                  # NEW — recommendation request/response schemas
├── creation.py                        # SPLIT from skills.py — creation schemas
├── evolution.py                       # SPLIT from skills.py — evolution schemas
└── (other existing schema files unchanged)
```

### Design Rationale

**Why separate recommendation, creation, and evolution?**

Each is a distinct pipeline with its own models, prompts, and API routes. Recommendation covers ALL tool types. Creation generates new file-based elements. Evolution improves existing ones. Keeping them as separate packages avoids wrapper concepts and makes each pipeline independently understandable.

**Why not keep them under `skill/`?**

Creation and evolution are no longer skill-specific. They generate and modify any file-based agent element: skills, subagents, commands, hooks. Keeping the `skill/` name would be misleading. `models/skill/` retains only `info.py` and `source.py` (skill discovery metadata).

**Why dissolve `models/analysis/`?**

The former `models/analysis/` was a grab-bag of unrelated models. Each file moves to the domain that owns it:
- `friction.py` → `models/friction/` (parallels `services/friction/`)
- `correlator.py`, `phase.py`, `tool_graph.py` → `models/session/` (session-level insight models, parallel `services/session/`)
- `step_ref.py` → `models/` root (cross-cutting building block used by friction, creation, evolution)

**Why move `llm/prompts/` to `prompts/`?**

Prompts are a cross-cutting concern used by recommendation, creation, evolution, and friction analysis. Nesting them under `llm/` implies they belong to the LLM layer, but they reference domain models and service concepts. A top-level `prompts/` package (at `src/vibelens/prompts/`) is cleaner and avoids circular imports.

**Shared types:**
- `ElementType` lives in `models/enums.py` (shared by creation, evolution, and recommendation). Not in `models/creation/` — that would make evolution depend on creation.
- `WorkflowPattern` lives in `models/session/` (session insight model used by creation and evolution results).
- `StepRef` lives in `models/step_ref.py` (cross-cutting, used by friction and creation).

**Clean boundaries:**
- `models/recommendation/` owns CatalogItem, ItemType, UserProfile, RecommendationResult.
- `models/creation/` owns ElementCreation, CreationResult.
- `models/evolution/` owns ElementEvolution, EvolutionResult.
- `models/friction/` owns FrictionAnalysisResult, FrictionType.
- `models/session/` owns PhaseSegment, CorrelatedGroup, ToolDependencyGraph, WorkflowPattern.
- `models/skill/` owns SkillInfo, SkillSource (discovery metadata only).
- `models/enums.py` owns ElementType and other shared enumerations.
- `services/recommendation/` owns the L1-L4 pipeline, catalog, crawler, download, import.
- `services/creation/` owns the creation pipeline.
- `services/evolution/` owns the evolution pipeline.
- `services/shared.py` owns cross-pipeline utilities (parse_llm_output, merge_batch_refs, validate_patterns).
- `prompts/` owns all LLM prompt definitions and Jinja2 templates.
- Shared infrastructure (`context_extraction.py`, `context_params.py`, `session_batcher.py`, `job_tracker.py`) stays in `services/` root.
- UserProfile is cached in `services/recommendation/` and optionally passed to creation/evolution for context.

## Catalog

### Self-Discovery via GitHub Crawler

The catalog is built by crawling GitHub directly. No dependency on third-party APIs, databases, or other repos' internal structure.

**Why GitHub?** Stable API, covers 95%+ of open-source AI tools, rich metadata (stars, topics, README, license, activity), well-documented rate limits.

### Search Strategy

The crawler uses GitHub Search API with multiple queries to maximize coverage:

**Topic-based queries:**

| Query | Target |
|-------|--------|
| `topic:mcp-server` | MCP server implementations |
| `topic:claude-code OR topic:claude-skill` | Claude Code skills |
| `topic:codex-cli OR topic:codex-skill` | Codex CLI skills |
| `topic:cursor-rules` | Cursor editor rules |
| `topic:agent-tool` | General agent tools |
| `topic:ai-skill` | Editor/IDE skills |
| `topic:llm-plugin` | LLM framework plugins |

**Keyword-based queries:**

| Query | Target |
|-------|--------|
| `"SKILL.md" in:path` | Any repo with SKILL.md files |
| `"CLAUDE.md" in:path language:Markdown` | Claude instruction files |
| `mcp server in:name,description` | MCP servers by name/description |
| `claude code skill in:name,description` | Skills by name/description |
| `agent tool in:name,description` | Agent tools by name/description |

**Organization-based queries:**

| Query | Target |
|-------|--------|
| `org:modelcontextprotocol` | Official MCP servers |
| `org:anthropics path:skills` | Official Anthropic skills |

Each query returns up to 1,000 results (GitHub Search API limit). With 15+ queries covering different angles, the crawler discovers 5,000-8,000 unique repos before dedup.

### Seed Repos

Curated repos that are always included regardless of search results. These are known multi-item repositories that contain hundreds of individual installable items:

| Seed Repo | Why | Expected Items |
|-----------|-----|---------------|
| `anthropics/skills` | Official Anthropic skill library | ~300 skills |
| `modelcontextprotocol/servers` | Official MCP server reference implementations | ~50 servers |
| `davepoon/buildwithclaude` | Curated marketplace: agents, commands, hooks, MCP configs | ~2,281 items |
| `nicobailon/claude-code-templates` | Agents, commands, skills across 26 domains | ~3,560 items |

Seed repos are defined in `services/recommendation/crawler/seeds.py`. Adding a new seed is a one-line change.

### Multi-Item Repo Detection

Most repos contain a single tool. But seed repos and some discovered repos are "collections" containing many installable items. The crawler detects and unpacks these:

**Detection signals:**
- Directory structure matches known patterns: `agents/`, `commands/`, `hooks/`, `skills/`, `servers/`
- Many `.md` files with YAML frontmatter in subdirectories
- `mcp-servers.json` or similar registry files
- Repo description mentions "collection", "templates", "marketplace"

**Unpacking:**
1. Crawl repo contents via GitHub Contents API.
2. Walk directories matching collection patterns.
3. For each item file (`.md` with frontmatter, `.json` config), create a separate CatalogItem.
4. Each item's `item_id` = `{repo_full_name}/{relative_path}` for uniqueness.
5. Read file content for `install_content` field.

**Rate limiting:** Multi-item repos can require hundreds of Contents API calls. The crawler respects GitHub rate limits (5,000/hour for authenticated requests) and caches responses.

### Classification

The crawler auto-classifies each discovered item into an ItemType:

**Repo-level signals:**
- GitHub topics → primary classification (e.g., `topic:mcp-server` → `repo` with `install_method: "mcp_config"`)
- Repo name patterns (e.g., `*-mcp`, `mcp-*` → `repo` with MCP tags)
- Language (e.g., Docker-only repos → likely `repo`)

**File-level signals (for multi-item repos):**
- Parent directory: `agents/` → `subagent`, `commands/` → `command`, `hooks/` → `hook`, `skills/` → `skill`
- YAML frontmatter: `hooks:` field → `hook`, `tools:` field → `subagent`
- File content keywords

**Fallback:** Items that don't match any signal → `repo` (generic).

### Quality Scoring

Each item gets a quality score (0-100) computed from objective, publicly available GitHub metrics. All signals are computable without human judgment or LLM calls.

| Signal | Weight | Measurement |
|--------|--------|-------------|
| Stars | 30% | log(1 + stars), normalized against catalog max |
| Recency | 20% | Exponential decay from last commit (e^(-0.01 * days)) |
| Forks | 15% | log(1 + forks), normalized |
| Commits | 10% | log(1 + total_commits), normalized |
| Issue resolution | 10% | closed_issues / total_issues (default 0.5 if no issues) |
| Contributors | 10% | log(1 + contributors), normalized |
| License | 5% | Has OSI-approved license (binary) |

All metrics are fetched from GitHub API (repos endpoint + contributors count). No subjective signals (README quality, description quality) — these are unreliable and expensive to compute consistently.

Items from seed repos that are also in the official Skills Hub featured list (Anthropic's curated 300) get a +5 bonus, capped at 100.

### Bundled Snapshot

Each VibeLens release ships `catalog.json`:

```json
{
  "schema_version": 1,
  "version": "2026-04-10",
  "built_at": "2026-04-10T08:30:00Z",
  "item_count": 10247,
  "items": [ ... ],
  "tfidf_vectors": "base64-encoded sparse matrix",
  "composability_pairs": [
    {"item_a": "test-runner", "item_b": "ci-pipeline", "score": 0.78}
  ]
}
```

`schema_version` (integer) enables forward compatibility. New fields are always optional. Old VibeLens versions ignore unknown fields.

**Composability pairs:** Pre-computed TF-IDF cosine similarity between item descriptions. Each pair has `item_a` (item_id), `item_b` (item_id), and `score` (0.0-1.0). Only pairs with score > 0.3 are stored. The runtime scoring pipeline's `composability` signal (5% weight) looks up whether a candidate appears in pairs with other high-scoring candidates, boosting items that complement the user's selection.

### Build Pipeline

CLI command:

```
vibelens build-catalog --github-token $GITHUB_TOKEN --output catalog.json
```

Steps:
1. Run all search queries (GitHub Search API).
2. Fetch seed repos and their contents.
3. Dedup by repo URL, then by normalized name + type.
4. Classify each item.
5. Fetch metadata for each unique repo (stars, README, topics, etc.).
6. Detect and unpack multi-item repos.
7. Score quality.
8. Pre-compute TF-IDF vectors from `name + description + tags`.
9. Compute composability pairs (TF-IDF cosine similarity between item descriptions).
10. Serialize to `catalog.json`.

**Rate budget:** ~3,000-5,000 GitHub API calls per full build. With authenticated rate limit (5,000/hour), a full build completes in under 2 hours. Incremental builds (only new/updated repos) take minutes.

**Schedule:** The build runs weekly via CI. Output is published as a GitHub Release asset.

### Dynamic Updates

The catalog updates independently of VibeLens releases. Any VibeLens version can fetch the latest catalog.

**Runtime behavior:**

```
Startup:
  1. Load bundled catalog.json (always available as fallback)
  2. Check ~/.vibelens/catalog/catalog.json (downloaded cache)
  3. Use whichever has newer "version" date

Background check (once per day, non-blocking):
  1. HEAD request to CATALOG_UPDATE_URL for Last-Modified
  2. If newer than local cache, download in background
  3. Save to ~/.vibelens/catalog/catalog.json
  4. Next engine run uses the new catalog
```

**Configuration:**

| Setting | Default | Description |
|---------|---------|-------------|
| `catalog_update_url` | GitHub Release asset URL | Where to fetch updates |
| `catalog_auto_update` | `true` | Check for updates on startup |
| `catalog_check_interval_hours` | `24` | Minimum hours between checks |

**Manual update:**

```
vibelens update-catalog          # download latest
vibelens update-catalog --check  # check version without downloading
```

**Compatibility:** `schema_version` increments only on breaking changes. New fields are optional with defaults. Older VibeLens versions load newer catalogs by ignoring unknown fields.

## ItemType

Items are divided into two categories based on how they are defined and installed:

**File-based:** Defined by one or more local files. Users can create, edit, and evolve these directly. These are the targets for Phase 2 (evolution) and Phase 3 (creation).

**Repo-based (installable):** Defined by an entire repository. Installed via package managers, Docker, or config changes. Users install but don't author these locally.

| ItemType | Category | User-Facing Label | Description | Install Method | Discovery Signal |
|----------|----------|------------------|-------------|----------------|-----------------|
| `skill` | file-based | "Skill" | Behavior rules and workflow instructions (SKILL.md) | Write file to `~/.claude/commands/` | `skills/` dir, SKILL.md, topic:claude-skill |
| `subagent` | file-based | "Expert Agent" | Specialized AI expert (Python, security, DevOps, etc.) | Write file to `~/.claude/commands/` | `agents/` dir, tools: frontmatter |
| `command` | file-based | "Slash Command" | Quick actions you trigger with / (e.g., /commit, /docs) | Write file to `~/.claude/commands/` | `commands/` dir, argument-hint frontmatter |
| `hook` | file-based | "Automation" | Runs automatically before or after agent actions | Add to settings hooks array | `hooks/` dir, hooks: frontmatter |
| `repo` | repo-based | "Repository" | GitHub repos: MCP servers, CLI tools, frameworks, libraries, templates | pip/npm/brew install, mcp_config, clone | Fallback for unclassified |

**Key distinctions:**
- File-based items (skill, subagent, command, hook) can be created and evolved. A skill may consist of one file (SKILL.md) or several related files. A subagent is an agent config file (AGENT.md) with optional supporting files.
- Repo-based items are installed as-is. The `repo` type is the single catch-all for any GitHub repository: MCP servers, CLI tools, frameworks, libraries, templates. The `install_method` field (e.g., `mcp_config`, `pip`, `npm`, `docker`) captures how each repo is installed, not its ItemType.
- The `repo` type replaces the former `mcp_server`, `agent_tool`, `llm_plugin`, `template`, and `tool` types. Sub-categorization of repos is handled by `install_method` and `tags`, not by multiplying ItemType values.

User-facing labels avoid jargon. The UI never shows raw ItemType values.

## CatalogItem

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | Unique identifier (`{repo_full_name}` or `{repo_full_name}/{path}` for multi-item repos) |
| `item_type` | `ItemType` | Classified type |
| `name` | `str` | Display name |
| `description` | `str` | What it does (1-2 sentences, plain language) |
| `tags` | `list[str]` | Searchable tags (from GitHub topics + extracted keywords) |
| `category` | `str` | Free-form category derived from GitHub topics (e.g., "testing", "devops", "documentation", "database") |
| `platforms` | `list[str]` | Compatible agents: claude-code, codex, gemini, cursor, etc. |
| `quality_score` | `float` | 0-100, computed by crawler scorer |
| `popularity` | `float` | Normalized from stars |
| `updated_at` | `str` | Last commit ISO timestamp |
| `source_url` | `str` | GitHub URL |
| `repo_full_name` | `str` | GitHub `owner/repo` |
| `is_file_based` | `bool` | Computed from `item_type in FILE_BASED_TYPES` |
| `install_method` | `str` | skill_file, pip, npm, mcp_config, hook_config, docker, manual |
| `install_command` | `str or None` | e.g., "pip install foo" |
| `install_content` | `str or None` | Full file content (for items from multi-item repos with readable content) |

## Retrieval Architecture Decision

### Why TF-IDF, Not Graph RAG

LightRAG (graph-based RAG with knowledge graph + vector retrieval) was evaluated for the retrieval layer.

Decision: pre-computed TF-IDF is the right choice for this catalog size and use case.

| Factor | TF-IDF (chosen) | Graph RAG (LightRAG) |
|--------|-----------------|---------------------|
| **Retrieval latency** | <10ms for 10,000 items | 2-15s (requires LLM for query interpretation) |
| **External dependencies** | None | LLM API or local model for every query |
| **Indexing cost** | Zero at runtime (pre-computed at build) | Expensive LLM entity extraction per document |
| **Offline capability** | Fully offline | No (needs LLM for queries) |
| **Setup complexity** | Zero config, loads from bundled JSON | Requires storage backend + LLM/embedding config |
| **Catalog size fit** | Ideal for <100K structured items | Designed for millions of unstructured documents |

**Key insight:** LightRAG excels at extracting structure from unstructured text. Our catalog already HAS structure: tags, categories, quality scores, platform compatibility, composability pairs. Adding graph RAG would introduce LLM latency at query time (2-15s per retrieval) with no quality gain over keyword matching on structured fields.

**Where LLM adds value:** Profile generation (L2) and rationale (L4). These are semantic tasks. Retrieval (L3) is a structured matching problem where TF-IDF on pre-tagged items is both faster and sufficient.

**Future option:** The pluggable `RetrievalBackend` ABC allows adding `EmbeddingRetrieval` or `HybridRetrieval` backends. `KeywordRetrieval` (TF-IDF) remains the zero-dependency default.

## Phase 1: Recommendation

Multi-layer engine. 2 LLM calls, 35-60 seconds.

### Layer 1: Context Extraction (no LLM, 5-10s)

Two extraction modes: **lightweight** (CLI, all sessions) and **standard** (web UI, selected sessions).

#### Lightweight Extraction (CLI recommend, all sessions)

For `vibelens recommend` which processes ALL local sessions (500+, 1GB+), the standard `extract_all_contexts()` path is too slow and produces too many tokens. Instead, use `extract_lightweight_digest()` in `services/recommendation/extraction.py`:

1. Get all session metadata from `LocalTrajectoryStore.list_metadata()` (cached, instant)
2. **Sessions WITH compaction agents (~80%)**: Read ONLY compaction JSONL files directly (skip main trajectory). Extract the AGENT step's summary text, truncate to 300 chars. Claude Code layout: `{uuid}/subagents/agent-acompact-*.jsonl`
3. **Sessions WITHOUT compaction (~20%)**: Use cached metadata only: `"Project: {path} | Tools: {count} | Duration: {dur} | Model: {model}"`
4. **Diversity sampling** (if digest exceeds token budget): Group by project, take up to 3 most recent per project, rank projects by session count, keep top N until under budget. Ensures coverage of all active projects with recency bias.

Output: 30-50K tokens for 500+ sessions. I/O: ~25 MB (compaction files only vs 1.3 GB for all sessions).

#### Standard Extraction (web UI, selected sessions)

For the web API (`POST /recommendation/analyze` with explicit `session_ids`), use existing `extract_all_contexts()` with `PRESET_RECOMMENDATION`:

```python
PRESET_RECOMMENDATION = ContextParams(
    user_prompt_max_chars=500,
    user_prompt_head_chars=400,
    user_prompt_tail_chars=100,
    agent_message_max_chars=0,
    agent_message_head_chars=0,
    agent_message_tail_chars=0,
    bash_command_max_chars=0,
    tool_arg_max_chars=0,
    error_truncate_chars=200,
    include_non_error_obs=False,
    observation_max_chars=0,
    shorten_home_prefix=True,
    path_max_segments=2,
)
```

**Compression ratio**: 99.9% reduction per session.

### Extraction Tier Comparison

| Tier | Use Case | Compression | Includes |
|------|----------|-------------|----------|
| `PRESET_RECOMMENDATION` | Phase 1 | 99.9% | Compaction summaries, user msgs, tool freq, metadata |
| `PRESET_CONCISE` | Creation/evolution proposals | 95% | User msgs (800ch), tool calls (name + key args), errors |
| `PRESET_MEDIUM` | Deep creation/evolution | 90% | User msgs (1500ch), tool calls + args, errors |
| `PRESET_DETAIL` | Friction analysis | 85% | Full steps except raw observations |

### Layer 2: LLM Profile Generation (1 call, 15-25s)

Input: 5-10K tokens of extracted signals. Output: structured JSON profile.

**UserProfile** (in `models/recommendation/profile.py`):

| Field | Type | Description |
|-------|------|-------------|
| `domains` | `list[str]` | "web-dev", "data-pipeline", "devops" |
| `languages` | `list[str]` | "python", "typescript" |
| `frameworks` | `list[str]` | "fastapi", "react", "docker" |
| `agent_platforms` | `list[str]` | "claude-code", "codex", "gemini" |
| `bottlenecks` | `list[str]` | "repeated test failures", "slow CI" |
| `workflow_style` | `str` | "iterative debugger, prefers small commits" |
| `search_keywords` | `list[str]` | 20-30 keywords designed to match catalog terms |

The `search_keywords` field bridges the semantic gap: the LLM translates noisy session patterns ("I keep fixing import errors") into catalog-friendly terms ("auto-import", "import-management").

The UserProfile is cached and optionally passed to Phase 2 (evolution) and Phase 3 (creation).

### Layer 3: Retrieval + Scoring (no LLM, <1s)

Two stages: candidate retrieval, then scoring.

**Retrieval Backends (pluggable):**

```python
class RetrievalBackend(ABC):
    def build_index(self, items: list[CatalogItem]) -> None: ...
    def search(self, query: str, top_k: int) -> list[tuple[CatalogItem, float]]: ...
```

| Backend | Default? | Dependencies | How it works |
|---------|----------|-------------|--------------|
| `KeywordRetrieval` | Yes | None | Pre-computed TF-IDF vectors. Query = search_keywords joined. Cosine similarity. |
| `EmbeddingRetrieval` | No | Embedding model or API | Pre-computed embeddings bundled. Query embedding via user's LLM API. |
| `HybridRetrieval` | No | Embedding model or API | Reciprocal rank fusion of keyword + embedding results. |

Default is `KeywordRetrieval` (zero external dependencies, fully offline).

Retrieval output: top-30 candidates with relevance scores.

**Scoring Pipeline (configurable):**

```python
class ScoringSignal(ABC):
    name: str
    weight: float
    def score(self, item: CatalogItem, profile: UserProfile) -> float: ...  # 0.0-1.0
```

| Signal | Weight | What it measures |
|--------|--------|-----------------|
| `relevance` | 0.40 | From retrieval backend |
| `quality` | 0.25 | Pre-computed quality score from catalog (0-100, normalized). Already includes stars, recency, forks, contributors — do NOT add these as separate runtime signals. |
| `platform_match` | 0.20 | Does item support user's agent? (binary: 1.0 or 0.0) |
| `popularity` | 0.10 | Normalized stars (for sort-by-popularity in UI; overlaps with quality but serves a distinct display purpose) |
| `composability` | 0.05 | Does item complement other high-scoring items? Uses pre-computed composability pairs. |

Final score = weighted sum. Top-15 pass to Layer 4.

### Layer 4: LLM Rationale Generation (1 call, 15-25s)

Input: UserProfile + top-15 CatalogItems. Output: per-item rationale.

```
One sentence (max 15 words).
- First bullet (max 10 words).
- Second bullet (max 10 words).
```

Plain language, no jargon. Written for non-technical users.

Output per item:
- `rationale`: personalized explanation tied to user's patterns
- `confidence`: 0.0-1.0 match strength

## Phase 2: Evolution (existing, generalized)

Improve installed file-based elements (skills, subagents, commands, hooks) after the user has used them for a while. Existing pipeline in `services/skill/evolution.py` is generalized to `services/evolution/pipeline.py` to handle all `ElementType` values.

**What changes from the current code:**
- `SkillEvolution` → `ElementEvolution` (with `element_type` field)
- `SkillEdit` → `ElementEdit`
- Pipeline logic is identical: proposal phase → edit generation. The element type determines which prompt templates to use and where to find the source file.
- For skills, source files are in `~/.claude/commands/`. For subagents, `~/.claude/commands/` (agent .md files). For hooks, the hooks section of settings files.

### Integration with Phase 1

- Evolution can optionally receive the cached UserProfile from Phase 1 to focus analysis.
- Items installed via Phase 1's installation plan become visible as evolution targets (only file-based items are evolvable).

## Phase 3: Creation (existing, generalized)

Generate new file-based elements for workflow patterns no catalog item covers. Existing pipeline in `services/skill/creation.py` is generalized to `services/creation/pipeline.py` to generate any `ElementType`.

**What changes from the current code:**
- `SkillCreation` → `ElementCreation` (with `element_type`, `target_path` fields)
- Pipeline logic is identical: proposal phase → content generation. The element type determines which prompt templates to use, what file structure to generate, and where to install.
- The LLM decides which element type best fits each uncovered pattern (e.g., a recurring Git workflow → command, a security review process → subagent).

### Integration with Phase 1

- Creation runs AFTER recommendation. The prompt includes recommended/installed items for dedup.
- The cached UserProfile's `bottlenecks` helps the LLM focus on uncovered gaps.

## Data Models

### New: `models/recommendation/`

**`catalog.py`:**

```python
class ItemType(StrEnum):
    # File-based — can be created and evolved locally
    SKILL = "skill"
    SUBAGENT = "subagent"
    COMMAND = "command"
    HOOK = "hook"
    # Repo-based — installed as-is from GitHub
    REPO = "repo"

FILE_BASED_TYPES: set[ItemType] = {
    ItemType.SKILL, ItemType.SUBAGENT, ItemType.COMMAND, ItemType.HOOK,
}

ITEM_TYPE_LABELS: dict[ItemType, str] = {
    ItemType.SKILL: "Skill",
    ItemType.SUBAGENT: "Expert Agent",
    ItemType.COMMAND: "Slash Command",
    ItemType.HOOK: "Automation",
    ItemType.REPO: "Repository",
}

class CatalogItem(BaseModel):
    item_id: str = Field(description="Unique identifier")
    item_type: ItemType = Field(description="Classified type")
    name: str = Field(description="Display name")
    description: str = Field(description="Plain language, 1-2 sentences")
    tags: list[str] = Field(description="Searchable tags")
    category: str = Field(description="Classification category")
    platforms: list[str] = Field(description="Compatible agent platforms")
    quality_score: float = Field(description="0-100 from crawler scorer")
    popularity: float = Field(description="Normalized from stars")
    updated_at: str = Field(description="Last commit ISO timestamp")
    source_url: str = Field(description="GitHub URL")
    repo_full_name: str = Field(description="GitHub owner/repo")
    install_method: str = Field(description="skill_file, pip, npm, mcp_config, etc.")
    install_command: str | None = Field(default=None, description="e.g. pip install foo")
    install_content: str | None = Field(default=None, description="Full file content for direct install")

    @computed_field
    @property
    def is_file_based(self) -> bool:
        """True for file-based types (skill, subagent, command, hook)."""
        return self.item_type in FILE_BASED_TYPES
```

**`profile.py`:**

```python
class UserProfile(BaseModel):
    domains: list[str] = Field(description="e.g. web-dev, data-pipeline")
    languages: list[str] = Field(description="e.g. python, typescript")
    frameworks: list[str] = Field(description="e.g. fastapi, react")
    agent_platforms: list[str] = Field(description="e.g. claude-code, codex")
    bottlenecks: list[str] = Field(description="Recurring friction: e.g. repeated test failures, slow CI")
    workflow_style: str = Field(description="e.g. iterative debugger, prefers small commits")
    search_keywords: list[str] = Field(description="20-30 catalog-friendly search terms")
```

**`results.py`:**

```python
class CatalogRecommendation(BaseModel):
    item_id: str = Field(description="CatalogItem reference")
    item_type: ItemType = Field(description="Item type")
    user_label: str = Field(description="User-facing type label")
    name: str = Field(description="Display name")
    description: str = Field(description="Plain language")
    rationale: str = Field(description="1 sentence + 1-2 bullets, personalized")
    confidence: float = Field(description="0.0-1.0")
    quality_score: float = Field(description="From catalog")
    score: float = Field(description="Composite from scoring pipeline")
    install_method: str = Field(description="How to install")
    install_command: str | None = Field(default=None, description="Install command")
    has_content: bool = Field(description="Whether install_content is bundled")
    source_url: str = Field(description="GitHub URL")

class RecommendationResult(BaseModel):
    analysis_id: str | None = Field(default=None, description="Set on persistence")
    session_ids: list[str] = Field(description="Sessions analyzed")
    skipped_session_ids: list[str] = Field(default_factory=list, description="Sessions not found")
    title: str = Field(description="Main finding, max 10 words")
    summary: str = Field(description="1-2 sentence narrative")
    user_profile: UserProfile = Field(description="Extracted profile from L2")
    recommendations: list[CatalogRecommendation] = Field(description="Ranked results")
    backend_id: BackendType = Field(description="Inference backend")
    model: str = Field(description="Model identifier")
    created_at: str = Field(description="ISO timestamp")
    metrics: Metrics = Field(description="Token usage and cost")
    duration_seconds: float | None = Field(default=None, description="Wall-clock time")
    catalog_version: str = Field(description="Catalog snapshot version used")
    is_example: bool = Field(default=False, description="Bundled example flag")
```

### Shared: `models/enums.py` (addition)

`ElementType` is added to the existing `enums.py` module. Used by both creation and evolution — neither package depends on the other.

```python
class ElementType(StrEnum):
    """File-based element types that can be created or evolved."""
    SKILL = "skill"           # SKILL.md — behavior rules and workflow instructions
    SUBAGENT = "subagent"     # AGENT.md — specialized AI expert configuration
    COMMAND = "command"        # command .md — slash command definitions
    HOOK = "hook"             # hook config — automation triggers
```

### New: `models/creation/`

Generalized from `models/skill/creation.py`. Handles creation of any file-based element type.

**`models.py`:**

```python
# ElementType imported from models/enums.py

class ElementCreation(BaseModel):
    element_type: ElementType = Field(description="Type of element being created")
    name: str = Field(description="Element name")
    description: str = Field(description="What it does, plain language")
    file_content: str = Field(description="Full file content to write")
    target_path: str = Field(description="Suggested install path, e.g. ~/.claude/commands/foo.md")
    rationale: str = Field(description="Why this element helps the user")
    tools_used: list[str] = Field(default_factory=list, description="Tools the element references")
    addressed_patterns: list[str] = Field(default_factory=list, description="Workflow patterns covered")
    confidence: float = Field(description="0.0-1.0")

class ElementCreationProposal(BaseModel):
    element_type: ElementType = Field(description="Type of element to create")
    name: str = Field(description="Proposed name")
    description: str = Field(description="What it would do")
    rationale: str = Field(description="Why it's needed")
    addressed_patterns: list[str] = Field(default_factory=list)
    relevant_session_indices: list[int] = Field(default_factory=list, description="Sessions relevant to this proposal")
    confidence: float = Field(default=0.0, description="0.0-1.0")
```

**`results.py`:**

```python
class CreationResult(BaseModel):
    analysis_id: str | None = Field(default=None, description="Set on persistence")
    session_ids: list[str] = Field(description="Sessions analyzed")
    skipped_session_ids: list[str] = Field(default_factory=list)
    title: str = Field(description="Main finding, max 10 words")
    workflow_patterns: list[WorkflowPattern] = Field(default_factory=list)
    creations: list[ElementCreation] = Field(description="Generated elements")
    backend_id: BackendType = Field(description="Inference backend")
    model: str = Field(description="Model identifier")
    created_at: str = Field(description="ISO timestamp")
    batch_count: int = Field(default=1)
    metrics: Metrics = Field(description="Token usage and cost")
    warnings: list[str] = Field(default_factory=list)
    duration_seconds: float | None = Field(default=None)
    is_example: bool = Field(default=False)
```

### New: `models/evolution/`

Generalized from `models/skill/evolution.py`. Handles evolution of any file-based element type.

**`models.py`:**

```python
# ElementType imported from models/enums.py

class ElementEdit(BaseModel):
    old_string: str = Field(description="Text to find in the element file")
    new_string: str = Field(description="Replacement text")
    replace_all: bool = Field(default=False, description="Replace all occurrences")

class ElementEvolution(BaseModel):
    element_type: ElementType = Field(description="Type of element being evolved")
    element_name: str = Field(description="Name of the element to modify")
    description: str = Field(description="What the evolution does")
    edits: list[ElementEdit] = Field(description="Granular edits to apply")
    rationale: str = Field(description="Why this improves the element")
    addressed_patterns: list[str] = Field(default_factory=list)
    confidence: float = Field(description="0.0-1.0")

class ElementEvolutionProposal(BaseModel):
    element_type: ElementType = Field(description="Type of element to evolve")
    element_name: str = Field(description="Which element to modify")
    description: str = Field(description="Proposed improvement")
    rationale: str = Field(description="Why it's needed")
    suggested_changes: str = Field(default="", description="High-level change description for deep-edit LLM call")
    addressed_patterns: list[str] = Field(default_factory=list)
    relevant_session_indices: list[int] = Field(default_factory=list, description="Sessions relevant to this proposal")
    confidence: float = Field(default=0.0, description="0.0-1.0")
```

**`results.py`:**

```python
class EvolutionResult(BaseModel):
    analysis_id: str | None = Field(default=None, description="Set on persistence")
    session_ids: list[str] = Field(description="Sessions analyzed")
    skipped_session_ids: list[str] = Field(default_factory=list)
    title: str = Field(description="Main finding, max 10 words")
    workflow_patterns: list[WorkflowPattern] = Field(default_factory=list)
    evolutions: list[ElementEvolution] = Field(description="Proposed edits")
    backend_id: BackendType = Field(description="Inference backend")
    model: str = Field(description="Model identifier")
    created_at: str = Field(description="ISO timestamp")
    batch_count: int = Field(default=1)
    metrics: Metrics = Field(description="Token usage and cost")
    warnings: list[str] = Field(default_factory=list)
    duration_seconds: float | None = Field(default=None)
    is_example: bool = Field(default=False)
```

### Retained: `models/skill/`

Only `info.py` and `source.py` remain. These handle skill discovery metadata (listing installed skills, tracking sources).

### Dissolved: `models/analysis/`

Every file moves to its owning domain:

| Former location | New location | Why |
|----------------|--------------|-----|
| `analysis/friction.py` | `models/friction/models.py` | Parallels `services/friction/` |
| `analysis/correlator.py` | `models/session/correlator.py` | Used by `services/session/correlator.py` |
| `analysis/phase.py` | `models/session/phase.py` | Used by `services/session/phase.py` |
| `analysis/tool_graph.py` | `models/session/tool_graph.py` | Used by `services/session/tool_graph.py` |
| `analysis/step_ref.py` | `models/step_ref.py` | Cross-cutting, used by friction + creation |

`WorkflowPattern` (currently in `models/skill/patterns.py`) moves to `models/session/` — it is a session insight model used by `CreationResult` and `EvolutionResult`.

**Deleted files from `models/skill/`:**
- `retrieval.py` — replaced by `models/recommendation/`
- `patterns.py` — `SkillMode` removed; `WorkflowPattern` moves to `models/session/`
- `creation.py` — replaced by `models/creation/`
- `evolution.py` — replaced by `models/evolution/`
- `results.py` — replaced by `models/creation/results.py` and `models/evolution/results.py`

## CLI Interface

### `vibelens recommend`

Runs the full recommendation pipeline on ALL local sessions and opens the results in the web UI.

```
vibelens recommend [--top-n 15] [--config path/to/config.yaml] [--no-open]
```

**Flow:**
1. Load settings. If no LLM backend configured, auto-discover available agent CLIs via `shutil.which()` and present an interactive picker.
2. Get all session metadata from `LocalTrajectoryStore`
3. Run lightweight extraction (compaction summaries + metadata, with diversity sampling if needed)
4. Run L2 profile → L3 retrieval+scoring → L4 rationale
5. Save result to `RecommendationStore`
6. Unless `--no-open`: start VibeLens server and open browser to `http://{host}:{port}?recommendation={analysis_id}`

**Backend auto-discovery:** When no backend is configured, scan `_CLI_BACKEND_REGISTRY` for available binaries. Present numbered choices with default model and estimated per-run cost. On selection, persist to `~/.vibelens/settings.json` via `set_llm_config()`.

### Frontend Recommendation View

When the app URL contains `?recommendation={analysis_id}`, show a full-page recommendation view:
- Header with profile summary (domains, languages, frameworks as pills), session count, cost, duration
- Scrollable card list with type badges, score bars, personalized rationale
- "View on GitHub" button per card (opens `source_url`)
- "Install" button per card (triggers `install-target-dialog` for file-based types, shows copyable command for repos)
- "Back to sessions" button to return to normal view

## API Endpoints

### Recommendation (new, separate routes)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/recommendation/analyze` | Start recommendation (background job) |
| `POST` | `/recommendation/estimate` | Pre-flight cost estimate |
| `GET` | `/recommendation/jobs/{job_id}` | Poll job status |
| `POST` | `/recommendation/jobs/{job_id}/cancel` | Cancel job |
| `GET` | `/recommendation/{analysis_id}` | Load result |
| `POST` | `/recommendation/{analysis_id}/install` | Generate installation plan |
| `GET` | `/recommendation/history` | List past recommendations |
| `DELETE` | `/recommendation/{analysis_id}` | Delete result |
| `GET` | `/recommendation/catalog/status` | Catalog version, item count |

### Install Endpoint

**POST `/recommendation/{analysis_id}/install`**

Request:
```json
{
  "selected_item_ids": ["test-runner", "modelcontextprotocol/servers/postgres"],
  "target_agent": "claude-code"
}
```

Response:
```json
{
  "installation_plan": "# VibeLens Installation Plan\n...",
  "filename": "vibelens-install-20260410.md",
  "file_path": "~/.vibelens/install-plans/vibelens-install-20260410.md"
}
```

### Creation (replaces /skills/analysis for creation mode)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/creation/analyze` | Start creation analysis |
| `POST` | `/creation/estimate` | Pre-flight cost estimate |
| `GET` | `/creation/jobs/{job_id}` | Poll job status |
| `POST` | `/creation/jobs/{job_id}/cancel` | Cancel |
| `GET` | `/creation/{analysis_id}` | Load result |
| `GET` | `/creation/history` | List past analyses |
| `DELETE` | `/creation/{analysis_id}` | Delete |
| `POST` | `/creation/proposals` | Generate creation proposals |
| `POST` | `/creation/generate` | Deep create from approved proposal |

**POST `/creation/analyze` request:**
```json
{
  "session_ids": ["abc123", "def456"],
  "element_types": ["skill", "command"],
  "max_creations": 5
}
```
`element_types` is optional. If omitted, the LLM decides which types to create. If provided, limits creation to the specified types.

### Evolution (replaces /skills/analysis for evolution mode)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/evolution/analyze` | Start evolution analysis |
| `POST` | `/evolution/estimate` | Pre-flight cost estimate |
| `GET` | `/evolution/jobs/{job_id}` | Poll job status |
| `POST` | `/evolution/jobs/{job_id}/cancel` | Cancel |
| `GET` | `/evolution/{analysis_id}` | Load result |
| `GET` | `/evolution/history` | List past analyses |
| `DELETE` | `/evolution/{analysis_id}` | Delete |

**POST `/evolution/analyze` request:**
```json
{
  "session_ids": ["abc123", "def456"],
  "element_names": ["test-runner", "security-review"],
  "element_types": ["skill", "subagent"]
}
```
`element_names` limits evolution to specific installed elements. `element_types` limits to specific types. Both are optional.

## Installation Plan Format

Agent-executable markdown. The user does NOT read this -- they hand it to their agent.

```markdown
# VibeLens Installation Plan
# Generated: 2026-04-10 14:30 UTC
# Target agent: Claude Code
# Items: 3

## Step 1: Install skill "test-runner"
Create file ~/.claude/commands/test-runner.md with this exact content:

[full SKILL.md content from install_content]

## Step 2: Configure MCP server "postgres-mcp"
Add the following entry to mcpServers in ~/.claude/settings.json:

[JSON config block from install_content]

## Step 3: Install CLI tool "ruff"
Run: pip install ruff

## Verification
After all steps, confirm each installation:
- ls ~/.claude/commands/test-runner.md
- Check that mcpServers in ~/.claude/settings.json contains "postgres-mcp"
- ruff --version
Report which items were installed successfully and which failed.
```

Items with `install_content` include the full file body inline. No network download needed. Items without it use `install_command` or link to `source_url`.

**Delivery options (single click each):**

| Option | What Happens | What User Does Next |
|--------|-------------|-------------------|
| **Copy to clipboard** | Full plan copied | Paste into agent chat |
| **Save as file** | Saved to `~/.vibelens/install-plans/` | Tell agent: "Follow the instructions in {path}" |

## User Flow

### CLI Flow (`vibelens recommend`)

Primary entry point. Runs the pipeline locally and opens results in the browser.

1. User runs `vibelens recommend` in terminal
2. If no LLM backend: interactive picker shows available agent CLIs (e.g., claude, gemini, codex)
3. Pipeline runs with progress output: loading sessions → extracting signals → generating profile → retrieving candidates → generating rationales
4. Result saved to store, browser opens to `?recommendation={analysis_id}`
5. User sees recommendation view with interactive cards, GitHub links, and install buttons

### Web UI Flow

**Stage 1: Onboarding Prompt**

**When**: First visit (no recommendation history). Also available on-demand from Skills panel.

```
Personalize your setup
We'll look at your recent sessions and suggest tools that fit how you work.
Takes about 1 minute. Runs in the background while you look around.

[Get Started]  [Maybe Later]
```

No jargon. No mention of "AI", "analysis", "LLM", or "recommendation engine".

### Stage 2: Background Execution (35-60s)

User navigates freely. Persistent status pill in header:

- "Reading your sessions..." (L1, 5-10s)
- "Understanding your workflow..." (L2, 15-25s)
- "Finding matching tools..." (L3+L4, 15-25s)

### Stage 3: Notification

Toast: "Done -- N tools found for your workflow"

Badge appears on Skills tab. Clicking either opens the report.

### Stage 4: Report Display

Non-technical reader. No raw scores, no source URLs in default view.

**Header:**
```
Based on your recent work, here are N tools that could help.
[summary sentence from RecommendationResult.summary]
```

**Grouping:** Cards grouped by user-facing label ("Skills", "Expert Agents", "Slash Commands", "Automations", "Repositories"). Within "Repositories", sub-grouped by `install_method` (e.g., MCP servers shown together). Sorted by composite score within group.

**Each card shows:**
- Name + one-line description
- Personalized rationale (1 sentence + 1-2 bullets)
- Type badge with user-friendly label
- Visual confidence indicator (green/yellow/gray dots)
- Checkbox for selection

**Expandable "Details":** Quality score, GitHub URL, last updated, repo name.

### Stage 5: Install Selected

User checks items -> "Install Selected" -> delivery dialog:

```
How do you want to install these?

[Copy to Clipboard]    Paste the instructions into your agent's chat.

[Save as File]         We'll save a file. Tell your agent to follow it.
```

### Stage 6: Next Steps

```
What would you like to do next?

[Improve Installed]    Fine-tune your skills, agents, and commands based
                       on how you actually use them. Best after a few days.

[Create Custom]        Build new skills, agents, commands, or hooks for
                       workflow patterns nothing in the catalog covers.

[Run Again]            Get fresh suggestions. Items you already
                       installed will be filtered out.
```

"Improve Installed" launches evolution (Phase 2). "Create Custom" launches creation (Phase 3). Both optionally receive the cached UserProfile from Phase 1.

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| No sessions | "Use your agent for a few sessions first, then come back." |
| No strong matches | "No strong matches found. Try Create Custom to build something specific for your workflow." |
| All items already installed | "You're all set! Try Improve Installed to fine-tune your tools." |
| Repeat recommendation | Filter installed items, highlight new catalog additions since last run |
| Demo mode | Mock recommendations, no real installation |
| LLM not configured | "Set up your LLM API key in Settings to get started." |
| Catalog missing or corrupt | Fall back to featured-skills.json (current 299 skills) |
| Catalog update fails | Use cached or bundled catalog silently, log warning |
| Evolution with no installed elements | "Install some tools first via Get Started." |
| Creation after recommendation | Dedup proposals against recommended + installed items |

## Performance Budget

| Phase | Duration | LLM Calls | Notes |
|-------|----------|-----------|-------|
| **Phase 1: Recommendation** | | | |
| L1: Context extraction (lightweight) | 2-5s | 0 | Compaction files only (~25 MB), diversity sampling if needed |
| L1: Context extraction (standard) | 5-10s | 0 | Full session parse, web UI with selected sessions |
| L2: Profile generation | 15-25s | 1 | Single call, 5-10K input tokens |
| L3: Retrieval + scoring | <10ms | 0 | Pre-computed TF-IDF, in-memory, 10,000 items |
| L4: Rationale generation | 15-25s | 1 | Single call, profile + 15 candidates |
| **Phase 1 total** | **35-60s** | **2** | Under 1-minute target |
| **Phase 2: Evolution** | 60-120s | 2-4 | Proposal + per-element edit calls |
| **Phase 3: Creation** | 60-120s | 2-4 | Proposal + per-element generation calls |
| **Catalog build** | ~2 hours | 0 | GitHub API only, runs in CI weekly |

## Migration Path

### Phase A: Models (no behavior change)

1. Add `ElementType` to `models/enums.py`.
2. Create `models/recommendation/` package with `catalog.py`, `profile.py`, `results.py`.
3. Create `models/creation/` package with `models.py` (ElementCreation, ElementCreationProposal) and `results.py` (CreationResult).
4. Create `models/evolution/` package with `models.py` (ElementEvolution, ElementEvolutionProposal, ElementEdit) and `results.py` (EvolutionResult).
5. Dissolve `models/analysis/`: move `friction.py` → `models/friction/`, move `correlator.py`/`phase.py`/`tool_graph.py` → `models/session/`, move `step_ref.py` → `models/step_ref.py`.
6. Move `WorkflowPattern` from `models/skill/patterns.py` → `models/session/`.
7. Delete `models/skill/retrieval.py`, `models/skill/patterns.py`, `models/skill/creation.py`, `models/skill/evolution.py`, `models/skill/results.py`.
8. Keep `models/skill/info.py` and `models/skill/source.py`.
9. Update all imports referencing old models.

### Phase B: Prompts (move + generalize)

10. Move `llm/prompts/` to `src/vibelens/prompts/` package.
11. Rename `skill_creation.py` → `creation.py`, `skill_evolution.py` → `evolution.py`.
12. Delete `skill_retrieval.py`, create `recommendation.py`.
13. Split `templates/skill/` → `templates/creation/` and `templates/evolution/`.
14. Create `templates/recommendation/`.
15. Update `PROMPT_REGISTRY` and all imports.

### Phase C: Services (behavior change)

16. Create `services/shared.py` with cross-pipeline utilities extracted from `services/skill/shared.py` (`parse_llm_output`, `merge_batch_refs`, `validate_patterns`).
17. Create `services/recommendation/` package with engine, retrieval, scoring, catalog, installer, store, mock.
18. Create `services/recommendation/crawler/` subpackage with github, classifier, scorer, builder, seeds.
19. Move `services/skill/download.py` and `services/skill/importer.py` to `services/recommendation/` (used by installer for all item types).
20. Create `services/creation/` from `services/skill/creation.py`. Generalize to handle all `ElementType` values.
21. Create `services/evolution/` from `services/skill/evolution.py`. Generalize to handle all `ElementType` values.
22. Delete remaining `services/skill/` files (retrieval.py, shared.py, store.py, mock.py, __init__.py).
23. Add `PRESET_RECOMMENDATION` to `services/context_params.py`.
24. Create `services/recommendation/extraction.py` with `extract_lightweight_digest()` and `_sample_sessions()` for compaction-first extraction with diversity sampling.

### Phase D: API + CLI + Config

25. Add `catalog_update_url`, `catalog_auto_update`, `catalog_check_interval_hours` fields to `config/settings.py`.
26. Create `api/recommendation.py` with recommendation, estimate, and install endpoints.
27. Split `api/skill_analysis.py` → `api/creation.py` and `api/evolution.py`.
28. Add `recommendation_router`, `creation_router`, `evolution_router` to `api/__init__.py`.
29. Split `schemas/skills.py` → `schemas/creation.py` and `schemas/evolution.py`. Create `schemas/recommendation.py`.
30. Add `get_recommendation_store()` to `deps.py`.
31. Add `build-catalog` and `update-catalog` commands to `cli.py`.
32. Add `recommend` command to `cli.py` with `--top-n`, `--config`, `--no-open` options.
33. Add `discover_and_select_backend()` function to `cli.py` for interactive backend auto-discovery via `shutil.which()`.
34. Merge `GEMINI_CLI` into `GEMINI` in `AgentType` and `SkillSourceType`. Add `"gemini_cli": "gemini"` to `LEGACY_BACKEND_ALIASES`.

### Phase E: Data migration + frontend

35. Migrate existing `SkillAnalysisResult` JSONs in `~/.vibelens/skill_analyses/`: read each file, map to `CreationResult` or `EvolutionResult` based on the `mode` field, write to new store paths. Unmigrated files are preserved but hidden from the new API.
36. `featured-skills.json` becomes catalog fallback only.
37. Frontend adds recommendation onboarding UI alongside existing creation/evolution tabs.
38. Split frontend skill analysis components into creation and evolution where applicable.
39. Create `frontend/src/components/recommendations/` with `recommendation-view.tsx`, `recommendation-card.tsx`, `recommendation-constants.ts` for interactive recommendation display with install actions and GitHub links.
40. Add `?recommendation={analysis_id}` URL parameter support to `app.tsx`.
41. Remove `gemini_cli` entries from `skill-constants.ts` (`SOURCE_COLORS`, `SOURCE_LABELS`, `SOURCE_DESCRIPTIONS`, `ALL_SYNC_TARGETS`).
