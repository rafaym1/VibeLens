# Personalization Pipeline

Three-phase pipeline that recommends, evolves, and creates AI tools from user session history. Uses a curated catalog of 6,000+ items spanning skills, subagents, commands, hooks, and repos (including MCP servers).

## Purpose

Turn session history into a personalized agent setup through three phases:

1. **Recommend**: Search a catalog of AI tools. Return ranked matches with LLM-generated rationale. Install items directly to the user's agent.
2. **Evolve**: Improve installed file-based elements (skills, subagents, commands, hooks) based on observed usage patterns. Detect conflicts between element instructions and actual behavior, then generate granular edits.
3. **Create**: Generate new file-based elements for workflow patterns no catalog item covers.

The pipeline is the primary onboarding experience. Users follow a funnel: Recommend -> Install -> Evolve -> Create.

## Architecture

```
Phase 1: RECOMMEND                    Phase 2: EVOLVE              Phase 3: CREATE
                                      (after days of usage)        (fill remaining gaps)

sessions --L1--> signals --L2--> profile --L3--> candidates --L4--> recommendations
           local    LLM     retrieval   LLM      installed elements       uncovered patterns
           2-5s   15-25s     <10ms    15-25s         |                      |
                                                     v                      v
                                                proposals -> edits    proposals -> element files
                                                (2-4 LLM calls)      (2-4 LLM calls)
```

Phase 1 uses 2 LLM calls, 35-60 seconds. Phases 2 and 3 each use 2-4 LLM calls (proposal + deep generation per element).

## Project Structure

All paths relative to `src/vibelens/`.

```
catalog/                              # Build-time: catalog assembly from curated sources
├── builder.py                        # Orchestrate: collect -> dedup -> score -> validate -> write
├── dedup.py                          # Deduplicate by normalized (name, item_type)
├── frontmatter.py                    # YAML frontmatter parser for source files
├── scoring.py                        # Heuristic quality scoring (description, source, stars, recency, diversity)
└── sources/                          # One parser per curated data source
    ├── buildwithclaude.py            # Parse buildwithclaude marketplace
    ├── featured.py                   # Parse Skills Hub featured list
    └── templates.py                  # Parse claude-code-templates collection

data/
└── catalog.json                      # Bundled catalog snapshot (~6,000 items, ~7 MB)

models/
├── enums.py                          # ElementType (shared by creation + evolution), AgentType, etc.
├── step_ref.py                       # Cross-cutting step locator (used by friction, creation, evolution)
├── recommendation/
│   ├── catalog.py                    # CatalogItem, ItemType, FILE_BASED_TYPES, ITEM_TYPE_LABELS
│   ├── profile.py                    # UserProfile
│   └── results.py                    # RecommendationResult, CatalogRecommendation, RationaleItem, RationaleOutput
├── creation/
│   ├── creation.py                   # ElementCreation, ElementCreationProposal, ElementCreationProposalOutput/Result
│   └── results.py                    # CreationAnalysisResult
├── evolution/
│   ├── evolution.py                  # ElementEvolution, ElementEvolutionProposal, ElementEvolutionProposalOutput/Result, ElementEdit
│   └── results.py                    # EvolutionAnalysisResult
├── friction/
│   └── models.py                     # FrictionAnalysisResult, FrictionType, FrictionCost, Mitigation
├── session/
│   ├── patterns.py                   # WorkflowPattern (used by creation + evolution results)
│   ├── correlator.py                 # CorrelatedGroup, CorrelatedSession
│   ├── phase.py                      # PhaseSegment
│   └── tool_graph.py                 # ToolDependencyGraph, ToolEdge
├── skill/
│   ├── info.py                       # SkillInfo (discovery metadata)
│   └── source.py                     # SkillSource, SkillSourceType
├── dashboard/                        # Dashboard stats models (unchanged)
└── trajectories/                     # ATIF v1.6 trajectory models (unchanged)

services/
├── recommendation/
│   ├── engine.py                     # L1-L4 orchestration: analyze_recommendation, estimate_recommendation
│   ├── extraction.py                 # extract_lightweight_digest, find_compaction_files
│   ├── retrieval.py                  # RetrievalBackend ABC, KeywordRetrieval (TF-IDF)
│   ├── scoring.py                    # score_candidates (weighted multi-signal scoring)
│   ├── catalog.py                    # CatalogSnapshot, load_catalog (bundled + user cache)
│   ├── store.py                      # RecommendationStore (AnalysisStore subclass)
│   └── mock.py                       # build_mock_recommendation_result
├── catalog/
│   └── install.py                    # install_catalog_item: write files, merge hooks/MCP config
├── creation/
│   ├── store.py                      # CreationAnalysisStore
│   └── mock.py                       # build_mock_creation_result
├── evolution/
│   ├── store.py                      # EvolutionAnalysisStore
│   └── mock.py                       # build_mock_evolution_result
├── skill/
│   ├── creation.py                   # analyze_skill_creation (proposal + deep generation)
│   ├── evolution.py                  # analyze_skill_evolution (proposal + deep editing)
│   ├── retrieval.py                  # Skill retrieval pipeline
│   ├── shared.py                     # parse_llm_output, cross-pipeline utilities
│   ├── download.py                   # GitHub file download
│   ├── importer.py                   # Agent CLI import
│   ├── store.py                      # SkillAnalysisStore
│   └── mock.py                       # Demo data
├── analysis_shared.py                # Shared extraction, formatting, logging for all pipelines
├── analysis_store.py                 # AnalysisStore base class
├── context_extraction.py             # extract_all_contexts
├── context_params.py                 # PRESET_RECOMMENDATION, PRESET_CONCISE, PRESET_MEDIUM, PRESET_DETAIL
├── job_tracker.py                    # Background job management (submit, poll, cancel)
└── session/                          # Session CRUD, correlator, phases, tool graph (unchanged)

prompts/
├── recommendation.py                 # RECOMMENDATION_PROFILE_PROMPT, RECOMMENDATION_RATIONALE_PROMPT
├── creation.py                       # SKILL_CREATION_PROPOSAL_PROMPT, SKILL_CREATION_GENERATE_PROMPT, synthesis
├── evolution.py                      # SKILL_EVOLUTION_PROPOSAL_PROMPT, SKILL_EVOLUTION_GENERATE_PROMPT, synthesis
├── friction_analysis.py              # Friction analysis prompts
└── templates/
    ├── recommendation/               # profile_system/user.j2, rationale_system/user.j2
    ├── creation/                     # proposal + generation system/user.j2, synthesis system/user.j2
    ├── evolution/                    # proposal + generation system/user.j2, synthesis system/user.j2
    └── friction/                     # analysis + synthesis system/user.j2

api/
├── recommendation.py                 # Recommendation endpoints (analyze, estimate, history, load, delete)
├── catalog.py                        # Catalog browsing (list, search, filter, install, meta)
├── creation.py                       # Creation analysis endpoints
├── evolution.py                      # Evolution analysis endpoints
├── friction.py                       # Friction analysis endpoints (unchanged)
└── skill_management.py               # Skill CRUD endpoints (unchanged)

schemas/
├── recommendation.py                 # RecommendationAnalyzeRequest, CatalogStatusResponse
├── catalog.py                        # CatalogListResponse, CatalogInstallRequest/Response, CatalogMetaResponse
├── creation.py                       # CreationAnalysisRequest, CreationAnalysisMeta
├── evolution.py                      # EvolutionAnalysisRequest, EvolutionAnalysisMeta
└── (other existing schemas)
```

### Design Rationale

**Why separate recommendation, creation, and evolution?**

Each is a distinct pipeline with its own models, prompts, and API routes. Recommendation covers ALL tool types (including repo-based items). Creation generates new file-based elements. Evolution improves existing ones. Keeping them as separate packages makes each pipeline independently understandable.

**Shared types:**
- `ElementType` lives in `models/enums.py` (shared by creation and evolution). Not in `models/creation/` -- that would make evolution depend on creation.
- `WorkflowPattern` lives in `models/session/patterns.py` (session insight model used by creation and evolution results).
- `StepRef` lives in `models/step_ref.py` (cross-cutting, used by friction, creation, and evolution).

## Catalog

### Sources

The catalog is built from three curated data sources, each with a dedicated parser in `catalog/sources/`:

| Source | Directory | Description | Approximate Items |
|--------|-----------|-------------|-------------------|
| `buildwithclaude` | `hub/buildwithclaude/` | Curated marketplace: agents, commands, hooks, MCP configs | ~2,200 |
| `claude-code-templates` | `hub/claude-code-templates/` | Agents, commands, skills across 26 domains | ~3,500 |
| `skills-hub` | `hub/skills-hub/` | Official Anthropic Skills Hub featured list | ~300 |

Source parsers read directory trees, parse YAML frontmatter from `.md` files, and emit `CatalogItem` instances with `item_type`, `tags`, `category`, `install_content`, and other metadata.

### Build Pipeline

CLI entry point: `python -m vibelens.catalog --hub-dir <path> [--output catalog.json] [--existing <path>] [--stats]`

Steps:
1. Parse each source directory into raw `CatalogItem` lists.
2. Deduplicate by normalized `(name, item_type)` pairs. On collision, keep the item with richer metadata (prefers `install_content` > none, longer description > shorter). Merge tags from all duplicates.
3. Score quality using weighted heuristic signals (see Quality Scoring below).
4. Validate source URLs via async HEAD requests (50 concurrent, 5s timeout). Drop items with broken URLs.
5. Optionally merge with an existing catalog (hand-curated items keep their original scores).
6. Write `catalog.json`.

Output: `src/vibelens/data/catalog.json` (bundled with each release).

### ItemType

Items are divided into two categories based on how they are defined and installed:

**File-based:** Defined by one or more local files. Users can create, edit, and evolve these directly. These are the targets for Phase 2 (evolution) and Phase 3 (creation).

**Repo-based:** Defined by an entire repository. Installed via package managers, Docker, or config changes.

| ItemType | Category | User-Facing Label | Install Method |
|----------|----------|-------------------|----------------|
| `skill` | file-based | Skill | Write `.md` to `~/.claude/commands/` |
| `subagent` | file-based | Expert Agent | Write `.md` to `~/.claude/commands/` |
| `command` | file-based | Slash Command | Write `.md` to `~/.claude/commands/` |
| `hook` | file-based | Automation | Add to settings hooks array |
| `repo` | repo-based | Repository | pip/npm/brew install, mcp_config, clone |

User-facing labels avoid jargon. The UI never shows raw ItemType values.

### CatalogItem

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | Unique identifier (e.g. `bwc:skill-name` or `cct:agents/agent-name`) |
| `item_type` | `ItemType` | Classified type |
| `name` | `str` | Display name |
| `description` | `str` | What it does (1-2 sentences, plain language) |
| `tags` | `list[str]` | Searchable tags |
| `category` | `str` | Classification category (e.g. "testing", "devops", "documentation") |
| `platforms` | `list[str]` | Compatible agents: `claude_code`, `codex`, `gemini`, etc. |
| `quality_score` | `float` | 0-100, computed by build-time scorer |
| `popularity` | `float` | Normalized from stars (0.0-1.0) |
| `updated_at` | `str` | Last commit ISO timestamp |
| `source_url` | `str` | GitHub URL |
| `repo_full_name` | `str` | GitHub `owner/repo` |
| `install_method` | `str` | `skill_file`, `pip`, `npm`, `mcp_config`, `hook_config`, etc. |
| `install_command` | `str \| None` | CLI install command, e.g. `pip install foo` |
| `install_content` | `str \| None` | Full file content for direct install |
| `is_file_based` | `bool` (computed) | True for file-based types |

### Quality Scoring

Build-time scoring in `catalog/scoring.py`. Each signal produces a 0.0-1.0 value. The weighted sum is mapped to the 50-100 range: `final = 50 + weighted_sum * 50`.

| Signal | Weight | Measurement |
|--------|--------|-------------|
| Description richness | 30% | `min(len(description) / 200, 1.0)` |
| Source quality | 25% | `featured: 0.7`, `bwc: 0.5`, `cct: 0.3` |
| Stars/popularity | 20% | Pre-normalized popularity (0.0-1.0) |
| Recency | 15% | Exponential decay from last commit: `e^(-0.01 * days)` |
| Category diversity | 10% | Boost of 0.2 for items in sparse categories (< 5 items) |

### Bundled Snapshot

Each VibeLens release ships `data/catalog.json`:

```json
{
  "version": "2026-04-10",
  "schema_version": 1,
  "items": [ ... ]
}
```

`schema_version` (integer) enables forward compatibility. New fields are always optional.

### Runtime Loading

`services/recommendation/catalog.py` loads the best available catalog:

1. Check bundled `data/catalog.json` (always available as fallback).
2. Check `~/.vibelens/catalog/catalog.json` (user-cached download).
3. Use whichever has the newer `version` date.

The `CatalogSnapshot` model provides an in-memory item index for fast lookup by `item_id`.

### Catalog Browsing API

The `api/catalog.py` router provides search, filter, and install endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/catalog` | List items with search, filters, sort, pagination |
| `GET` | `/catalog/meta` | Categories list and profile availability flag |
| `GET` | `/catalog/{item_id}` | Full item detail including install_content |
| `POST` | `/catalog/{item_id}/install` | Install item to target agent platform |

**List parameters:** `search`, `item_type`, `category`, `platform`, `sort` (quality/name/popularity/recent/relevance), `page`, `per_page` (max 200).

**Relevance sorting** uses search keywords from the most recent recommendation profile (if available).

### Direct Installation

`services/catalog/install.py` installs catalog items directly to agent platform directories:

| Item Type | Action |
|-----------|--------|
| `skill`, `subagent`, `command` | Write `install_content` to `~/.claude/commands/{name}.md` |
| `hook` | Parse hook JSON from `install_content`, merge into `settings.json` hooks |
| `repo` with `mcp_config` | Parse MCP JSON from `install_content`, merge into `settings.json` mcpServers |

Currently supports `claude_code` platform. Returns the installed path. Supports `overwrite` flag to replace existing files.

### [Planned] GitHub Crawler

A future enhancement to discover items automatically from GitHub. Would crawl public repos using GitHub Search API with topic-based queries (e.g. `topic:mcp-server`, `topic:claude-code`), keyword queries (e.g. `"SKILL.md" in:path`), and organization queries. Would auto-classify discovered repos/files into `ItemType` and compute quality scores from GitHub metrics (stars, forks, recency, contributors). This would expand the catalog beyond the current curated sources.

### Retrieval Architecture Decision: TF-IDF over Graph RAG

LightRAG (graph-based RAG) was evaluated for the retrieval layer.

Decision: TF-IDF is the right choice for this catalog size and use case.

| Factor | TF-IDF (chosen) | Graph RAG |
|--------|-----------------|-----------|
| Retrieval latency | <10ms for 6,000 items | 2-15s (requires LLM for query interpretation) |
| External dependencies | scikit-learn only | LLM API for every query |
| Indexing cost | Zero at runtime (built on demand from loaded catalog) | Expensive LLM entity extraction per document |
| Offline capability | Fully offline | No (needs LLM for queries) |
| Setup complexity | Zero config | Requires storage backend + LLM config |

**Where LLM adds value:** Profile generation (L2) and rationale (L4). These are semantic tasks. Retrieval (L3) is a structured matching problem where TF-IDF on pre-tagged items is faster and sufficient.

**Future option:** The pluggable `RetrievalBackend` ABC allows adding `EmbeddingRetrieval` or `HybridRetrieval` backends. `KeywordRetrieval` (TF-IDF) remains the zero-dependency default.

## Phase 1: Recommendation

Multi-layer engine in `services/recommendation/engine.py`. 2 LLM calls, 35-60 seconds.

### Layer 1: Context Extraction (no LLM)

Two extraction modes: **lightweight** (CLI, all sessions) and **standard** (web UI, selected sessions).

#### Lightweight Extraction (CLI recommend, all sessions)

For `vibelens recommend` which processes all local sessions, `extract_lightweight_digest()` in `services/recommendation/extraction.py`:

1. Get all session metadata from stores via `list_all_metadata()`.
2. **Sessions with compaction agents (~80%)**: Read compaction JSONL files directly (skip main trajectory). Extract the assistant summary text, truncate to 300 chars. Claude Code layout: `{uuid}/subagents/agent-acompact-*.jsonl`.
3. **Sessions without compaction (~20%)**: Use metadata + first user message (min 15 chars). Format: `Project: {name} | Tools: {count} | Duration: {min}min | Model: {model}\nTask: {first_message}`.
4. **Diversity sampling** (if digest exceeds 80K token budget): Group by project, take up to 3 most recent per project, rank projects by session count, keep top N until under budget.

#### Standard Extraction (web UI, selected sessions)

For `POST /recommendation/analyze` with explicit `session_ids`, use `extract_all_contexts()` with `PRESET_RECOMMENDATION`:

| Parameter | Value |
|-----------|-------|
| `user_prompt_max_chars` | 500 |
| `agent_message_max_chars` | 0 (skip) |
| `bash_command_max_chars` | 0 (skip) |
| `tool_arg_max_chars` | 0 (skip) |
| `error_truncate_chars` | 200 |
| `include_non_error_obs` | False |
| `shorten_home_prefix` | True |
| `path_max_segments` | 2 |

Compression ratio: ~99.9% reduction per session.

### Layer 2: LLM Profile Generation (1 call, 15-25s)

Input: session digest. Output: structured JSON `UserProfile`.

#### UserProfile

| Field | Type | Description |
|-------|------|-------------|
| `domains` | `list[str]` | e.g. "web-dev", "data-pipeline", "devops" |
| `languages` | `list[str]` | e.g. "python", "typescript" |
| `frameworks` | `list[str]` | e.g. "fastapi", "react", "docker" |
| `agent_platforms` | `list[str]` | e.g. "claude-code", "codex", "gemini" |
| `bottlenecks` | `list[str]` | e.g. "repeated test failures", "slow CI" |
| `workflow_style` | `str` | e.g. "iterative debugger, prefers small commits" |
| `search_keywords` | `list[str]` | 20-30 catalog-friendly search terms |

The `search_keywords` field bridges the semantic gap: the LLM translates noisy session patterns ("I keep fixing import errors") into catalog-friendly terms ("auto-import", "import-management").

### Layer 3: Retrieval + Scoring (no LLM, <10ms)

Two stages: candidate retrieval, then scoring.

**Retrieval:** `KeywordRetrieval` in `services/recommendation/retrieval.py`. Builds a TF-IDF index from item `name + description + tags` using scikit-learn. Query = joined `search_keywords`. Cosine similarity. Returns top-30 candidates.

**Scoring:** `score_candidates()` in `services/recommendation/scoring.py`. Configurable weighted signals:

| Signal | Weight | Measurement |
|--------|--------|-------------|
| `relevance` | 0.40 | TF-IDF cosine similarity from retrieval |
| `quality` | 0.25 | Pre-computed quality score normalized to 0.0-1.0 |
| `platform_match` | 0.20 | Binary: 1.0 if user's agent platform matches, else 0.0 |
| `popularity` | 0.10 | Pre-normalized stars |
| `composability` | 0.05 | Reserved for future composability pairs (currently 0.0) |

Platform matching normalizes naming variants (e.g. `claude-code` vs `claude_code`) via `PLATFORM_ALIASES`.

Final score = weighted sum. Top-15 pass to Layer 4.

### Layer 4: LLM Rationale Generation (1 call, 15-25s)

Input: UserProfile + top-15 CatalogItems. Output: per-item rationale.

#### RationaleItem

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | CatalogItem reference |
| `rationale` | `str` | One sentence (max 15 words), then 1-2 bullets (max 10 words each) |
| `confidence` | `float` | Match confidence 0.0-1.0 |

Items without a matching rationale get a generic fallback: "Matches your workflow." with confidence 0.5.

### RecommendationResult

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | `str \| None` | Set on persistence |
| `session_ids` | `list[str]` | Sessions analyzed |
| `skipped_session_ids` | `list[str]` | Sessions not found |
| `title` | `str` | e.g. "Top 15 recommendations for your workflow" |
| `summary` | `str` | 1-2 sentence narrative |
| `user_profile` | `UserProfile` | Extracted profile from L2 |
| `recommendations` | `list[CatalogRecommendation]` | Ranked results |
| `backend_id` | `BackendType` | Inference backend |
| `model` | `str` | Model identifier |
| `created_at` | `str` | ISO timestamp |
| `metrics` | `Metrics` | Token usage and cost |
| `duration_seconds` | `float \| None` | Wall-clock time |
| `catalog_version` | `str` | Catalog snapshot version used |
| `is_example` | `bool` | Bundled example flag |

### CatalogRecommendation

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | CatalogItem reference |
| `item_type` | `ItemType` | Item type |
| `user_label` | `str` | User-facing type label |
| `name` | `str` | Display name |
| `description` | `str` | Plain language |
| `rationale` | `str` | Personalized: 1 sentence + 1-2 bullets |
| `confidence` | `float` | 0.0-1.0 |
| `quality_score` | `float` | From catalog |
| `score` | `float` | Composite from scoring pipeline |
| `install_method` | `str` | How to install |
| `install_command` | `str \| None` | Install command |
| `has_content` | `bool` | Whether install_content is bundled |
| `source_url` | `str` | GitHub URL |

### Recommendation API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/recommendation/estimate` | Pre-flight cost estimate |
| `POST` | `/recommendation/analyze` | Start recommendation (background job) |
| `GET` | `/recommendation/jobs/{job_id}` | Poll job status |
| `POST` | `/recommendation/jobs/{job_id}/cancel` | Cancel job |
| `GET` | `/recommendation/history` | List past recommendations |
| `GET` | `/recommendation/catalog/status` | Catalog version and item count |
| `GET` | `/recommendation/{analysis_id}` | Load result |
| `DELETE` | `/recommendation/{analysis_id}` | Delete result |

**POST `/recommendation/analyze` request:**
```json
{
  "session_ids": ["abc123", "def456"]
}
```

Returns `AnalysisJobResponse` with `job_id` and `status`. Poll via `/jobs/{job_id}` until completed, then load result via `/{analysis_id}`.

## Phase 2: Evolution

Improve installed file-based elements after the user has used them for a while. Pipeline in `services/skill/evolution.py`.

Two-step LLM pipeline:
1. **Proposal**: Analyze sessions + installed element content. Detect conflicts between element instructions and actual behavior. Produce lightweight proposals.
2. **Deep edit**: For each approved proposal, generate granular `ElementEdit` operations (old_string/new_string, like the Edit tool).

### ElementEvolutionProposal

| Field | Type | Description |
|-------|------|-------------|
| `element_type` | `ElementType` | Type of element to evolve |
| `element_name` | `str` | Name of the existing element |
| `description` | `str` | Proposed improvement (max 30 words) |
| `rationale` | `str` | 1 sentence + 1-2 bullets, plain language |
| `suggested_changes` | `str` | High-level change description for the deep-edit LLM call |
| `addressed_patterns` | `list[str]` | Workflow pattern titles this proposal addresses |
| `relevant_session_indices` | `list[int]` | 0-indexed session indices |
| `confidence` | `float` | 0.0-1.0 |

### ElementEvolution

| Field | Type | Description |
|-------|------|-------------|
| `element_type` | `ElementType` | Type of element being evolved |
| `element_name` | `str` | Name of the element |
| `description` | `str` | What the evolution does (max 30 words) |
| `edits` | `list[ElementEdit]` | Ordered granular edits to apply |
| `rationale` | `str` | 1 sentence + 1-2 bullets, plain language |
| `addressed_patterns` | `list[str]` | Workflow pattern titles addressed |
| `confidence` | `float` | 0.0-1.0 |

### ElementEdit

| Field | Type | Description |
|-------|------|-------------|
| `old_string` | `str` | Text to find in the element file (empty for append) |
| `new_string` | `str` | Replacement text (empty for deletion) |
| `replace_all` | `bool` | Replace all occurrences (default false) |

### EvolutionAnalysisResult

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | `str \| None` | Set on persistence |
| `session_ids` | `list[str]` | Sessions analyzed |
| `skipped_session_ids` | `list[str]` | Sessions not found |
| `title` | `str` | Main finding, max 10 words |
| `workflow_patterns` | `list[WorkflowPattern]` | Detected patterns |
| `evolutions` | `list[ElementEvolution]` | Proposed edits |
| `backend_id` | `BackendType` | Inference backend |
| `model` | `str` | Model identifier |
| `created_at` | `str` | ISO timestamp |
| `batch_count` | `int` | Number of LLM batches |
| `metrics` | `Metrics` | Token usage and cost |
| `warnings` | `list[str]` | Non-fatal issues |
| `duration_seconds` | `float \| None` | Wall-clock duration |
| `is_example` | `bool` | Bundled example flag |

### Evolution API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/evolution/estimate` | Pre-flight cost estimate |
| `POST` | `/evolution` | Start evolution analysis (background job) |
| `GET` | `/evolution/jobs/{job_id}` | Poll job status |
| `POST` | `/evolution/jobs/{job_id}/cancel` | Cancel job |
| `GET` | `/evolution/history` | List past analyses |
| `GET` | `/evolution/{analysis_id}` | Load result |
| `DELETE` | `/evolution/{analysis_id}` | Delete result |

**POST `/evolution` request:**
```json
{
  "session_ids": ["abc123", "def456"],
  "skill_names": ["test-runner", "security-review"]
}
```

`skill_names` limits evolution to specific installed elements. Optional -- omit to analyze all installed skills.

## Phase 3: Creation

Generate new file-based elements for workflow patterns no catalog item covers. Pipeline in `services/skill/creation.py`.

Two-step LLM pipeline:
1. **Proposal**: Analyze sessions, detect recurring workflow patterns, propose lightweight element ideas (name + description + rationale).
2. **Deep creation**: For each approved proposal, generate the full SKILL.md content including YAML frontmatter.

### ElementCreationProposal

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Proposed element name in kebab-case |
| `description` | `str` | Specific trigger description for YAML frontmatter (max 30 words) |
| `rationale` | `str` | 1 sentence + 1-2 bullets, plain language |
| `addressed_patterns` | `list[str]` | Workflow pattern titles addressed |
| `relevant_session_indices` | `list[int]` | 0-indexed session indices |
| `confidence` | `float` | 0.0-1.0 |

### ElementCreation

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Element name in kebab-case |
| `description` | `str` | Trigger description for YAML frontmatter (max 30 words) |
| `skill_md_content` | `str` | Full SKILL.md content including YAML frontmatter |
| `rationale` | `str` | 1 sentence + 1-2 bullets, plain language |
| `tools_used` | `list[str]` | Tool names referenced (e.g. Read, Edit, Bash) |
| `addressed_patterns` | `list[str]` | Workflow pattern titles addressed |
| `confidence` | `float` | 0.0-1.0 |

### CreationAnalysisResult

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | `str \| None` | Set on persistence |
| `session_ids` | `list[str]` | Sessions analyzed |
| `skipped_session_ids` | `list[str]` | Sessions not found |
| `title` | `str` | Main finding, max 10 words |
| `workflow_patterns` | `list[WorkflowPattern]` | Detected patterns |
| `creations` | `list[ElementCreation]` | Generated elements |
| `backend_id` | `BackendType` | Inference backend |
| `model` | `str` | Model identifier |
| `created_at` | `str` | ISO timestamp |
| `batch_count` | `int` | Number of LLM batches |
| `metrics` | `Metrics` | Token usage and cost |
| `warnings` | `list[str]` | Non-fatal issues |
| `duration_seconds` | `float \| None` | Wall-clock duration |
| `is_example` | `bool` | Bundled example flag |

### Creation API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/creation/estimate` | Pre-flight cost estimate |
| `POST` | `/creation` | Start creation analysis (background job) |
| `GET` | `/creation/jobs/{job_id}` | Poll job status |
| `POST` | `/creation/jobs/{job_id}/cancel` | Cancel job |
| `GET` | `/creation/history` | List past analyses |
| `GET` | `/creation/{analysis_id}` | Load result |
| `DELETE` | `/creation/{analysis_id}` | Delete result |

**POST `/creation` request:**
```json
{
  "session_ids": ["abc123", "def456"]
}
```

## Shared Infrastructure

### Context Extraction Presets

`services/context_params.py` defines frozen presets controlling how session trajectories are compressed for each pipeline:

| Preset | Use Case | Compression |
|--------|----------|-------------|
| `PRESET_RECOMMENDATION` | Phase 1 profile generation | ~99.9% (user messages only, 500 chars max) |
| `PRESET_CONCISE` | Quick overviews, skill retrieval | ~95% (user messages 800 chars, tool names) |
| `PRESET_MEDIUM` | Creation/evolution proposals | ~90% (user messages 1500 chars, tool args) |
| `PRESET_DETAIL` | Friction analysis | ~85% (full steps except raw observations) |

### Analysis Shared

`services/analysis_shared.py` provides common functions used by all analysis pipelines:
- `extract_all_contexts()` -- load sessions and compress via a `ContextParams` preset
- `format_batch_digest()` -- format context set into LLM-ready text
- `truncate_digest_to_fit()` -- truncate to stay within model context window
- `build_system_kwargs()` -- prepare system prompt template variables
- `save_analysis_log()` -- write prompts and outputs to timestamped log directory
- `require_backend()` -- get the configured inference backend or raise

### Job Tracker

`services/job_tracker.py` manages background analysis jobs (shared by recommendation, creation, evolution):
- `submit_job()` -- launch an async coroutine as a background task
- `get_job()` -- poll job status (running, completed, failed, cancelled)
- `mark_completed()` / `mark_failed()` -- update job state
- `cancel_job()` -- cancel a running job

### Analysis Store

`services/analysis_store.py` defines the `AnalysisStore` base class. Subclasses:
- `RecommendationStore` in `services/recommendation/store.py`
- `CreationAnalysisStore` in `services/creation/store.py`
- `EvolutionAnalysisStore` in `services/evolution/store.py`
- `SkillAnalysisStore` in `services/skill/store.py`

Each store persists results as JSON files and provides `save()`, `load()`, `list_analyses()`, and `delete()` methods.

### Dependency Injection

`deps.py` provides singleton getters:
- `get_recommendation_store()` -- `RecommendationStore` (used by recommendation API and catalog relevance sorting)
- `get_skill_analysis_store()` -- `SkillAnalysisStore` (used by creation and evolution API routes for persistence)
- `get_creation_store()` -- `CreationAnalysisStore` (registered, not yet consumed)
- `get_evolution_store()` -- `EvolutionAnalysisStore` (registered, not yet consumed)

## CLI Interface

### `vibelens recommend`

Runs the full recommendation pipeline on all local sessions and opens results in the browser.

```
vibelens recommend [--top-n 15] [--config path/to/config.yaml] [--no-open]
```

**Flow:**
1. Load settings. If no LLM backend configured, auto-discover available agent CLIs via `shutil.which()` and present an interactive picker.
2. Get all session metadata from local stores.
3. Run lightweight extraction (compaction summaries + metadata, with diversity sampling if needed).
4. Run L2 profile -> L3 retrieval+scoring -> L4 rationale.
5. Save result to `RecommendationStore`.
6. Unless `--no-open`: start VibeLens server and open browser to results.

### `vibelens build-catalog` [Planned]

Stub command. Intended to orchestrate a full catalog build from curated sources with optional GitHub token for API-enhanced scoring. Currently prints a placeholder message.

### `vibelens update-catalog` [Planned]

Stub command. Intended to download the latest catalog from a remote URL and save to `~/.vibelens/catalog/`. Currently checks for `catalog_update_url` in settings but does not perform the download.

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| No sessions | "Use your agent for a few sessions first, then come back." |
| No strong matches | "No strong matches found." (empty recommendations list) |
| No catalog available | 404 from catalog endpoints; recommendation returns empty result |
| LLM not configured | 503 from analyze/estimate endpoints |
| Demo/test mode | Returns mock results without LLM calls |
| Catalog item already installed | Install endpoint returns 409 unless `overwrite=true` |
| Item has no install_content | Install endpoint returns 400 |
| Unknown platform | Install endpoint returns 400 with available platforms |
| Broken source URLs | Filtered out during catalog build (URL validation step) |

## Performance Budget

| Phase | Duration | LLM Calls | Notes |
|-------|----------|-----------|-------|
| **Phase 1: Recommendation** | | | |
| L1: Context extraction (lightweight) | 2-5s | 0 | Compaction files only, diversity sampling if needed |
| L1: Context extraction (standard) | 5-10s | 0 | Full session parse, web UI with selected sessions |
| L2: Profile generation | 15-25s | 1 | Single call, session digest input |
| L3: Retrieval + scoring | <10ms | 0 | TF-IDF cosine similarity, in-memory, ~6,000 items |
| L4: Rationale generation | 15-25s | 1 | Single call, profile + 15 candidates |
| **Phase 1 total** | **35-60s** | **2** | |
| **Phase 2: Evolution** | 60-120s | 2-4 | Proposal + per-element edit calls |
| **Phase 3: Creation** | 60-120s | 2-4 | Proposal + per-element generation calls |
