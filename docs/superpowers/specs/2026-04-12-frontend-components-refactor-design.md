# Frontend Components Refactor Design Spec

## Goal

Restructure `frontend/src/components/` to fix vague directory names, split oversized files, extract shared primitives, and move feature containers out of the root into proper feature directories. Pure structural refactor with zero visual or behavioral changes.

## Scope

- Rename directories: `analysis/` to `dashboard/`, `conversation/` to `session/`
- Create new feature directories: `friction/`, `upload/`, `llm/`
- Split 8 oversized files (>500 lines) along natural boundaries
- Promote 3 shared primitives from `skills/skill-shared.tsx` to root
- Refactor `confirm-dialog.tsx` to use shared Modal primitives
- Rename vague files: `analysis/tooltip.tsx` to `chart-tooltip.tsx`, `message-block.tsx` to `step-block.tsx`
- Update all import paths across the codebase
- Verify zero TypeScript errors after each change

## Non-Goals

- No visual changes (styles, colors, layout)
- No behavioral changes (state management, API calls, routing)
- No new features or functionality
- No changes to `styles.ts`, `index.css`, `types.ts`, or backend code
- No test creation (this is a move/split refactor; app.tsx integration test via `npm run build` is sufficient)

---

## 1. Directory Renames

### `analysis/` to `dashboard/`

The current `analysis/` directory mixes dashboard charts with friction analysis. "Analysis" is overloaded in VibeLens (friction analysis, skill analysis, recommendation analysis). Renaming to `dashboard/` makes the contents self-describing.

**Files staying in `dashboard/`:** activity-heatmap.tsx, bar-row.tsx, chart-constants.ts, chart-utils.ts, dashboard-view.tsx, model-distribution-chart.tsx, peak-hours-chart.tsx, stat-card.tsx, tool-distribution-chart.tsx, usage-over-time-chart.tsx

**File renamed:** `analysis/tooltip.tsx` becomes `dashboard/chart-tooltip.tsx` to disambiguate from the root `tooltip.tsx`.

**Files moving out:** `friction-history.tsx` and `friction-panel.tsx` move to new `friction/` directory.

### `conversation/` to `session/`

The app uses "session" terminology everywhere (session list, session view, session ID). The directory name should match.

**All 9 files move as-is**, with one rename: `message-block.tsx` becomes `step-block.tsx` (the app's data model calls them "steps", not "messages").

---

## 2. New Feature Directories

### `friction/` (new)

Friction analysis is a distinct feature from the dashboard. It gets its own directory.

**Contents after splitting:**

| File | Source | Contents |
|------|--------|----------|
| `friction-constants.ts` | Extracted from friction-panel.tsx | `SEVERITY_LABELS`, `SEVERITY_DESCRIPTIONS`, `FRICTION_TUTORIAL`, `POLL_INTERVAL_MS` |
| `friction-panel.tsx` | Slimmed from 761 lines | `FrictionPanel` orchestrator, `ResultHeader`, `SectionHeader`, `AnalysisMeta` (~350 lines) |
| `friction-mitigations.tsx` | Extracted from friction-panel.tsx | `MitigationsSection`, `MitigationCard`, `ConfidenceBar`, `CostBadges` (~150 lines) |
| `friction-types.tsx` | Extracted from friction-panel.tsx | `FrictionTypesSection`, `FrictionTypeCard`, `FrictionRefList`, `FrictionStepButton`, `SeverityBadge` (~120 lines) |
| `friction-history.tsx` | Moved from analysis/ | No changes needed |

### `upload/` (new)

The upload dialog is a self-contained multi-step wizard. It doesn't belong in root.

| File | Source | Contents |
|------|--------|----------|
| `upload-constants.ts` | Extracted from upload-dialog.tsx | `AGENT_OPTIONS`, `OS_OPTIONS`, `AGENT_LABELS`, `WEB_EXPORT_STEPS` |
| `upload-dialog.tsx` | Slimmed from 633 lines | `UploadDialog` orchestrator + `WebExportInstructions`, `SelectorRow` (~500 lines) |
| `upload-result-stats.tsx` | Extracted from upload-dialog.tsx | `ResultStats`, `StatBox` (~80 lines) |

### `llm/` (new)

LLM configuration is a distinct feature with its own form, selectors, and constants.

| File | Source | Contents |
|------|--------|----------|
| `llm-config-constants.ts` | Extracted from llm-config.tsx | `MODEL_PRESETS`, `BACKEND_OPTIONS`, `CLI_BACKENDS`, `ACCENT_STYLES`, `formatPrice`, `PricingLine` |
| `llm-config-selectors.tsx` | Extracted from llm-config.tsx | `ModelCombobox`, `CliModelSelector`, `BackendDropdown` (~250 lines) |
| `llm-config.tsx` | Slimmed from 609 lines | `LLMConfigForm`, `LLMConfigSection` (~280 lines) |

---

## 3. File Splits

### 3.1 `skill-analysis-views.tsx` (1004 lines to 5 files)

| New File | Exports | ~Lines |
|----------|---------|--------|
| `skill-analysis-view.tsx` | `AnalysisLoadingState`, `AnalysisResultView`, `ResultHeader`, `SectionHeader`, `MetadataFooter`, helpers | ~170 |
| `skill-patterns-view.tsx` | `PatternSection`, `PatternCard`, `StepRefList`, `JumpToStepButton` | ~90 |
| `skill-recommendations-view.tsx` | `RecommendationSection`, `RecommendationCard`, `ConfidenceBar` | ~200 |
| `skill-creations-view.tsx` | `CreationSection`, `CreatedSkillCard` | ~190 |
| `skill-evolutions-view.tsx` | `EvolutionSection`, `EvolutionCard` | ~260 |

The orchestrator (`skill-analysis-view.tsx`) imports and renders the four section components. Each section is self-contained with its own card components.

### 3.2 `message-block.tsx` (764 lines to 3 files in `session/`)

| New File | Exports | ~Lines |
|----------|---------|--------|
| `step-block.tsx` | `StepBlock`, `MessageBlock` (compat alias), `UserStep`, `SystemStep`, `SkillStep`, `AutoPromptStep`, `AgentStep`, `ConcurrentToolsBlock`, `TextBlock`, `ThinkingBlock` | ~300 |
| `tool-input-renderers.tsx` | `ToolUseBlock`, `ToolInputRenderer`, `BashRenderer`, `EditRenderer`, `WriteRenderer`, `DiffLine`, `getToolIconAndColor` | ~200 |
| `tool-output-renderers.tsx` | `ToolResultBlock`, `ToolOutput`, `tryFormatJson`, `getToolPreview` | ~180 |

### 3.3 `session-view.tsx` (935 lines to 2 files)

| New File | Exports | ~Lines |
|----------|---------|--------|
| `session-view.tsx` | `SessionView` orchestrator | ~700 |
| `session-header.tsx` | `MetaPill`, `TokenStat`, `CostStat`, share link modal | ~200 |

### 3.4 `friction-panel.tsx` (761 lines to 4 files)

See Section 2 (`friction/` directory) above.

### 3.5 `dashboard-view.tsx` (722 lines to 2 files)

| New File | Exports | ~Lines |
|----------|---------|--------|
| `dashboard-view.tsx` | `DashboardView` orchestrator | ~640 |
| `project-row.tsx` | `ProjectRow`, `METRIC_LABEL` | ~80 |

### 3.6 `session-list.tsx` (616 lines to 3 files in `session/`)

| New File | Exports | ~Lines |
|----------|---------|--------|
| `session-list.tsx` | `SessionList` orchestrator | ~350 |
| `session-row.tsx` | `SessionRow` | ~95 |
| `session-list-controls.tsx` | `AgentFilterDropdown`, `DonateButton` | ~75 |

### 3.7 `upload-dialog.tsx` (633 lines to 3 files)

See Section 2 (`upload/` directory) above.

### 3.8 `llm-config.tsx` (609 lines to 3 files)

See Section 2 (`llm/` directory) above.

---

## 4. Shared Primitive Extraction

Three components in `skills/skill-shared.tsx` are generic UI primitives used (or usable) across features. Promote them to root-level files.

| Component | Current Location | New File | Used By |
|-----------|-----------------|----------|---------|
| `EmptyState` | `skills/skill-shared.tsx` | `empty-state.tsx` | skills, friction, dashboard (potential) |
| `LoadingState` | `skills/skill-shared.tsx` | `loading-state.tsx` | skills, friction, recommendations |
| `ErrorBanner` | `skills/skill-shared.tsx` | `error-banner.tsx` | skills, friction |

After extraction, `skills/skill-shared.tsx` retains only skill-specific components: `SkillSearchBar`, `SourceFilterBar`, `NoResultsState`.

The existing skill files that import these will update imports to point to the root-level files.

---

## 5. Confirm Dialog Refactor

`confirm-dialog.tsx` currently hand-rolls a modal overlay:
```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center">
  <div className="fixed inset-0 bg-black/50" />
  <div className="relative bg-panel rounded-xl ...">
```

Refactor to use the shared `Modal` / `ModalHeader` / `ModalBody` / `ModalFooter` primitives, matching all other dialogs in the codebase.

---

## 6. Import Path Updates

Every file that imports from `analysis/`, `conversation/`, or any moved/renamed component must have its import paths updated.

**Affected import patterns:**

| Old Pattern | New Pattern |
|-------------|-------------|
| `../analysis/dashboard-view` | `../dashboard/dashboard-view` |
| `../analysis/friction-panel` | `../friction/friction-panel` |
| `../analysis/friction-history` | `../friction/friction-history` |
| `../analysis/tooltip` | `../dashboard/chart-tooltip` |
| `../conversation/session-view` | `../session/session-view` |
| `../conversation/message-block` | `../session/step-block` |
| `../conversation/*` | `../session/*` |
| `../upload-dialog` | `../upload/upload-dialog` |
| `../llm-config` | `../llm/llm-config` |
| `../session-list` | `../session/session-list` |
| `../search-options-dialog` | `../session/search-options-dialog` |
| `./skill-analysis-views` | `./skill-analysis-view` |

**Files outside `components/` that import from it:**
- `app.tsx` — imports session-list, session-view, dashboard-view, friction-panel, skills-panel, upload-dialog, llm-config, settings-dialog, etc.
- Any hooks or utils that reference component paths.

**Verification:** `npm run build` must produce zero TypeScript errors after all import updates.

---

## 7. Final Directory Tree

```
components/
├── dashboard/                  (13 files, was analysis/)
│   ├── activity-heatmap.tsx
│   ├── bar-row.tsx
│   ├── chart-constants.ts
│   ├── chart-tooltip.tsx
│   ├── chart-utils.ts
│   ├── dashboard-view.tsx
│   ├── model-distribution-chart.tsx
│   ├── peak-hours-chart.tsx
│   ├── project-row.tsx          NEW (split)
│   ├── stat-card.tsx
│   ├── tool-distribution-chart.tsx
│   └── usage-over-time-chart.tsx
│
├── friction/                   (5 files, NEW)
│   ├── friction-constants.ts    NEW (split)
│   ├── friction-history.tsx     (moved)
│   ├── friction-mitigations.tsx NEW (split)
│   ├── friction-panel.tsx       (moved + slimmed)
│   └── friction-types.tsx       NEW (split)
│
├── session/                    (15 files, was conversation/)
│   ├── content-renderer.tsx
│   ├── flow-diagram.tsx
│   ├── flow-layout.ts
│   ├── prompt-nav-panel.tsx
│   ├── search-options-dialog.tsx (moved from root)
│   ├── session-header.tsx       NEW (split)
│   ├── session-list-controls.tsx NEW (split)
│   ├── session-list.tsx         (moved from root + slimmed)
│   ├── session-row.tsx          NEW (split)
│   ├── session-view.tsx         (moved + slimmed)
│   ├── shared-session-view.tsx
│   ├── step-block.tsx           (renamed from message-block + slimmed)
│   ├── step-timeline.tsx
│   ├── sub-agent-block.tsx
│   ├── tool-input-renderers.tsx NEW (split)
│   └── tool-output-renderers.tsx NEW (split)
│
├── skills/                     (20 files)
│   ├── explore-skills-tab.tsx
│   ├── install-target-dialog.tsx
│   ├── local-skills-tab.tsx
│   ├── skill-analysis-view.tsx  (renamed + slimmed)
│   ├── skill-badges.tsx
│   ├── skill-cards.tsx
│   ├── skill-constants.ts
│   ├── skill-creations-view.tsx NEW (split)
│   ├── skill-edit-utils.ts
│   ├── skill-editor-dialog.tsx
│   ├── skill-evolution-diff.tsx
│   ├── skill-evolutions-view.tsx NEW (split)
│   ├── skill-patterns-view.tsx  NEW (split)
│   ├── skill-preview-dialog.tsx
│   ├── skill-recommendations-view.tsx NEW (split)
│   ├── skill-shared.tsx         (slimmed)
│   ├── skill-update-dialog.tsx
│   ├── skills-history.tsx
│   ├── skills-panel.tsx
│   └── sync-after-save-dialog.tsx
│
├── upload/                     (3 files, NEW)
│   ├── upload-constants.ts      NEW (split)
│   ├── upload-dialog.tsx        (moved + slimmed)
│   └── upload-result-stats.tsx  NEW (split)
│
├── llm/                        (3 files, NEW)
│   ├── llm-config-constants.ts  NEW (split)
│   ├── llm-config-selectors.tsx NEW (split)
│   └── llm-config.tsx           (moved + slimmed)
│
├── recommendations/            (3 files, unchanged)
│   ├── recommendation-card.tsx
│   ├── recommendation-constants.ts
│   └── recommendation-view.tsx
│
├── tutorial/                   (2 files, unchanged)
│   ├── spotlight-tour.tsx
│   └── tour-steps.ts
│
└── (root — 17 files, global primitives and cross-feature dialogs)
    ├── analysis-welcome.tsx
    ├── bullet-text.tsx
    ├── collapsible-pill.tsx
    ├── confirm-dialog.tsx       (refactored)
    ├── copy-button.tsx
    ├── cost-estimate-dialog.tsx
    ├── demo-banner.tsx
    ├── donate-consent-dialog.tsx
    ├── empty-state.tsx          NEW (promoted)
    ├── error-banner.tsx         NEW (promoted)
    ├── install-locally-dialog.tsx
    ├── loading-spinner.tsx
    ├── loading-state.tsx        NEW (promoted)
    ├── markdown-renderer.tsx
    ├── modal.tsx
    ├── resize-handle.tsx
    ├── settings-dialog.tsx
    ├── tooltip.tsx
    └── warnings-banner.tsx

Total: 81 files across 8 directories + root (was 64 files across 5 directories + root)
Net new files: 17 (all from splits/promotions; no new functionality)
Deleted files: 3 (original unsplit files replaced by their splits) + old dirs cleaned up

---

## 8. Constraints

- Every change must maintain `npm run build` with zero TypeScript errors
- No visual or behavioral changes — pixel-identical output
- The `MessageBlock` export name must remain available as an alias from `step-block.tsx` for backward compatibility (grep codebase for usage first; remove alias if unused externally)
- Import updates must be complete — no broken references
- Feature folders must be self-contained: a feature dir should not import from another feature dir's internal files (cross-feature sharing goes through root-level components)
