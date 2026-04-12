# Frontend Components Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `frontend/src/components/` — rename vague directories, split oversized files, extract shared primitives, clean up styles.ts — with zero visual or behavioral changes.

**Architecture:** Pure move/split/rename refactor. Each task moves or splits files in one feature area, updates all import paths, then verifies with `npm run build`. Tasks are ordered so that shared primitives are extracted first, then directories are restructured bottom-up (leaf features before root orchestrators).

**Tech Stack:** React, TypeScript, Tailwind CSS, Vite

**Spec:** `docs/superpowers/specs/2026-04-12-frontend-components-refactor-design.md`

---

### Task 1: Split styles.ts into styles.ts + constants.ts

Move non-visual constants out of `styles.ts` into a new `constants.ts` file. Update all imports.

**Files:**
- Modify: `frontend/src/styles.ts`
- Create: `frontend/src/constants.ts`
- Modify: All files that import the moved constants from `styles.ts`

- [ ] **Step 1: Identify all imports of the constants being moved**

Run:
```bash
cd frontend && grep -rn "SESSIONS_PER_PAGE\|SEARCH_DEBOUNCE_MS\|SCROLL_SUPPRESS_MS\|SHARE_STATUS_RESET_MS\|SHOW_ANALYSIS_DETAIL_SECTIONS\|SESSION_ID_SHORT\|SESSION_ID_MEDIUM\|PREVIEW_SHORT\|PREVIEW_MEDIUM\|PREVIEW_LONG\|LABEL_MAX_LENGTH" src/ --include="*.tsx" --include="*.ts" | grep -v "node_modules"
```

- [ ] **Step 2: Create `frontend/src/constants.ts`**

```typescript
// Display truncation lengths
export const SESSION_ID_SHORT = 8;
export const SESSION_ID_MEDIUM = 12;
export const PREVIEW_SHORT = 40;
export const PREVIEW_MEDIUM = 60;
export const PREVIEW_LONG = 150;
export const LABEL_MAX_LENGTH = 120;

// Timing constants
export const SHARE_STATUS_RESET_MS = 2000;
export const SCROLL_SUPPRESS_MS = 800;
export const SEARCH_DEBOUNCE_MS = 300;
export const SESSIONS_PER_PAGE = 100;

// Feature flags
export const SHOW_ANALYSIS_DETAIL_SECTIONS = false;
```

- [ ] **Step 3: Remove the moved constants from `styles.ts`**

Remove lines 64-79 from `styles.ts` (everything from `SESSION_ID_SHORT` through `SHOW_ANALYSIS_DETAIL_SECTIONS`). Keep all visual constants (TEXT_*, TOGGLE_*, CARD_DESCRIPTION, METRIC_LABEL, PHASE_STYLE, CATEGORY_STYLE, CATEGORY_LABELS, SEVERITY_COLORS, SIDEBAR_*, CHART).

- [ ] **Step 4: Update imports in all consuming files**

For each file found in Step 1, change:
```typescript
// Old:
import { SESSIONS_PER_PAGE, SEARCH_DEBOUNCE_MS } from "../styles";
// New:
import { SESSIONS_PER_PAGE, SEARCH_DEBOUNCE_MS } from "../constants";
```

If a file imports both style constants AND moved constants from `../styles`, split into two import lines — one from `../styles` and one from `../constants`.

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/styles.ts frontend/src/constants.ts frontend/src/components/
git commit -m "refactor: split non-visual constants from styles.ts into constants.ts"
```

---

### Task 2: Extract shared primitives from skill-shared.tsx to root

Promote `EmptyState`, `LoadingState`, and `ErrorBanner` from `skills/skill-shared.tsx` to root-level component files. Update all imports.

**Files:**
- Modify: `frontend/src/components/skills/skill-shared.tsx` (remove 3 components)
- Create: `frontend/src/components/empty-state.tsx`
- Create: `frontend/src/components/loading-state.tsx`
- Create: `frontend/src/components/error-banner.tsx`
- Modify: All files that import these components from `skill-shared`

- [ ] **Step 1: Identify all imports of EmptyState, LoadingState, ErrorBanner**

Run:
```bash
cd frontend && grep -rn "EmptyState\|LoadingState\|ErrorBanner" src/components/ --include="*.tsx" | grep -v "node_modules"
```

- [ ] **Step 2: Create `frontend/src/components/empty-state.tsx`**

```tsx
import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-2 text-center">
      <Icon className="w-8 h-8 text-faint" />
      <p className="text-sm text-muted">{title}</p>
      {subtitle && <p className="text-xs text-dimmed">{subtitle}</p>}
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend/src/components/loading-state.tsx`**

```tsx
import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-2">
      <Loader2 className="w-6 h-6 text-zinc-400 dark:text-cyan-400/60 animate-spin" />
      <p className="text-sm text-muted">{label}</p>
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend/src/components/error-banner.tsx`**

```tsx
import { AlertCircle, X } from "lucide-react";

export function ErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm border border-red-200 dark:border-red-800/40">
      <AlertCircle className="w-4 h-4 shrink-0" />
      <span className="flex-1">{message}</span>
      <button onClick={onDismiss} className="shrink-0 p-0.5 hover:bg-red-100 dark:hover:bg-red-900/50 rounded transition">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
```

- [ ] **Step 5: Remove the three components from `skill-shared.tsx`**

Remove the `EmptyState` function (lines 117-136), `LoadingState` function (lines 107-114), and `ErrorBanner` function (lines 94-104) from `skills/skill-shared.tsx`. Also remove the `AlertCircle` and `Loader2` imports if no longer used, and the `LucideIcon` type import if only EmptyState used it. Keep: `SkillSearchBar`, `SourceFilterBar`, `NoResultsState`, `SkillCount`.

- [ ] **Step 6: Update all imports**

For every file that imported these from skill-shared, update:
```typescript
// Old:
import { EmptyState, LoadingState, ErrorBanner } from "./skill-shared";
// New (from within skills/):
import { EmptyState } from "../empty-state";
import { LoadingState } from "../loading-state";
import { ErrorBanner } from "../error-banner";
```

Adjust relative paths based on the importing file's location. Files outside `skills/` that imported from `../skills/skill-shared` update to `./empty-state` etc.

- [ ] **Step 7: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/empty-state.tsx frontend/src/components/loading-state.tsx frontend/src/components/error-banner.tsx frontend/src/components/skills/skill-shared.tsx frontend/src/components/
git commit -m "refactor: promote EmptyState, LoadingState, ErrorBanner to shared root components"
```

---

### Task 3: Refactor confirm-dialog.tsx to use shared Modal primitives

Replace hand-rolled overlay with the shared `Modal` / `ModalHeader` / `ModalBody` / `ModalFooter` from `modal.tsx`.

**Files:**
- Modify: `frontend/src/components/confirm-dialog.tsx`

- [ ] **Step 1: Read modal.tsx to understand the shared API**

Read `frontend/src/components/modal.tsx` to confirm the `Modal`, `ModalHeader`, `ModalBody`, `ModalFooter` component signatures and available props (especially `onClose`, `maxWidth`).

- [ ] **Step 2: Rewrite confirm-dialog.tsx**

```tsx
import { Modal, ModalHeader, ModalBody, ModalFooter } from "./modal";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  loading = false,
}: ConfirmDialogProps) {
  return (
    <Modal onClose={onCancel} maxWidth="max-w-md">
      <ModalHeader onClose={onCancel}>
        <h2 className="text-sm font-semibold text-primary">{title}</h2>
      </ModalHeader>
      <ModalBody>
        <p className="text-sm text-secondary whitespace-pre-line">{message}</p>
      </ModalBody>
      <ModalFooter>
        <button
          onClick={onCancel}
          disabled={loading}
          className="px-3 py-1.5 text-xs text-muted hover:text-secondary border border-card hover:border-hover rounded transition disabled:opacity-50"
        >
          {cancelLabel}
        </button>
        <button
          onClick={onConfirm}
          disabled={loading}
          className="px-3 py-1.5 text-xs text-white bg-cyan-600 hover:bg-cyan-500 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Sending..." : confirmLabel}
        </button>
      </ModalFooter>
    </Modal>
  );
}
```

Note: Read `modal.tsx` first to confirm the ModalFooter renders children in a `flex justify-end gap-2` container. If it doesn't, add those classes to the footer buttons' wrapper. The existing footer styling uses `flex justify-end gap-2 px-5 py-3 border-t border-default` — ensure the Modal's ModalFooter provides equivalent styling.

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 4: Verify visual parity**

Open the app, trigger a confirm dialog (e.g., delete a skill), verify it looks identical: same padding, same button styles, same backdrop blur.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/confirm-dialog.tsx
git commit -m "refactor: rewrite confirm-dialog to use shared Modal primitives"
```

---

### Task 4: Rename `analysis/` to `dashboard/` + create `friction/` directory

Move dashboard files from `analysis/` to `dashboard/`, friction files to `friction/`, rename `analysis/tooltip.tsx` to `dashboard/chart-tooltip.tsx`. Update all imports.

**Files:**
- Move: All files from `frontend/src/components/analysis/` to `frontend/src/components/dashboard/` or `frontend/src/components/friction/`
- Rename: `analysis/tooltip.tsx` → `dashboard/chart-tooltip.tsx`
- Modify: All files importing from `analysis/`

- [ ] **Step 1: Identify all imports from `analysis/`**

Run:
```bash
cd frontend && grep -rn "from.*['\"].*analysis/" src/ --include="*.tsx" --include="*.ts" | grep -v node_modules
```

Also check imports from outside components/ (like app.tsx):
```bash
cd frontend && grep -rn "from.*analysis" src/app.tsx
```

- [ ] **Step 2: Create new directories**

```bash
mkdir -p frontend/src/components/dashboard
mkdir -p frontend/src/components/friction
```

- [ ] **Step 3: Move dashboard files**

```bash
cd frontend/src/components
git mv analysis/activity-heatmap.tsx dashboard/
git mv analysis/bar-row.tsx dashboard/
git mv analysis/chart-constants.ts dashboard/
git mv analysis/chart-utils.ts dashboard/
git mv analysis/dashboard-view.tsx dashboard/
git mv analysis/model-distribution-chart.tsx dashboard/
git mv analysis/peak-hours-chart.tsx dashboard/
git mv analysis/stat-card.tsx dashboard/
git mv analysis/tool-distribution-chart.tsx dashboard/
git mv analysis/usage-over-time-chart.tsx dashboard/
git mv analysis/tooltip.tsx dashboard/chart-tooltip.tsx
```

- [ ] **Step 4: Move friction files**

```bash
cd frontend/src/components
git mv analysis/friction-history.tsx friction/
git mv analysis/friction-panel.tsx friction/
```

- [ ] **Step 5: Remove empty analysis/ directory**

```bash
rmdir frontend/src/components/analysis
```

- [ ] **Step 6: Update intra-directory imports within dashboard/**

Inside `dashboard/` files, update any imports that referenced sibling files via `./`:
- `dashboard-view.tsx`: `import { useTooltip, ... } from "./tooltip"` → `from "./chart-tooltip"`
- Other dashboard files referencing `./tooltip` → `./chart-tooltip`

All other `./` imports within dashboard files stay the same since the files moved together.

- [ ] **Step 7: Update intra-directory imports within friction/**

Inside `friction/friction-panel.tsx`: `import { FrictionHistory } from "./friction-history"` — this should already work since both files moved together.

But `friction-panel.tsx` currently imports from `../analysis-welcome`, `../demo-banner`, `../loading-spinner`, `../cost-estimate-dialog`, `../tooltip`, `../bullet-text`, `../copy-button`, `../warnings-banner`. These all still work because friction/ is one level deeper than analysis/ was. Wait — analysis/ was already one level deep. Friction files were at `components/analysis/friction-panel.tsx` and imported from `../tooltip` (root tooltip) — that import path is still `../tooltip` from `components/friction/`. So these imports remain valid.

- [ ] **Step 8: Update all external imports**

Update every file identified in Step 1. Pattern changes:
```typescript
// In app.tsx:
import { DashboardView } from "./components/analysis/dashboard-view"
// →
import { DashboardView } from "./components/dashboard/dashboard-view"

import { FrictionPanel } from "./components/analysis/friction-panel"
// →
import { FrictionPanel } from "./components/friction/friction-panel"

// In files within components/ that import from ../analysis/:
import { ... } from "../analysis/dashboard-view"
// →
import { ... } from "../dashboard/dashboard-view"

import { ... } from "../analysis/friction-panel"
// →
import { ... } from "../friction/friction-panel"

import { ... } from "../analysis/friction-history"
// →
import { ... } from "../friction/friction-history"

// Chart tooltip (used by flow-diagram.tsx and step-timeline.tsx):
import { useTooltip, ... } from "../analysis/tooltip"
// →
import { useTooltip, ... } from "../dashboard/chart-tooltip"
```

- [ ] **Step 9: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 10: Commit**

```bash
git add -A frontend/src/components/analysis/ frontend/src/components/dashboard/ frontend/src/components/friction/ frontend/src/app.tsx frontend/src/components/
git commit -m "refactor: rename analysis/ to dashboard/, extract friction/ directory"
```

---

### Task 5: Rename `conversation/` to `session/` + move root session files

Rename the directory, rename `message-block.tsx` to `step-block.tsx`, move `session-list.tsx` and `search-options-dialog.tsx` from root into `session/`. Update all imports.

**Files:**
- Move: All files from `frontend/src/components/conversation/` to `frontend/src/components/session/`
- Rename: `conversation/message-block.tsx` → `session/step-block.tsx`
- Move: `frontend/src/components/session-list.tsx` → `frontend/src/components/session/session-list.tsx`
- Move: `frontend/src/components/search-options-dialog.tsx` → `frontend/src/components/session/search-options-dialog.tsx`
- Modify: All files importing from `conversation/`, `session-list`, `search-options-dialog`

- [ ] **Step 1: Identify all imports from conversation/, session-list, search-options-dialog**

Run:
```bash
cd frontend && grep -rn "from.*conversation/\|from.*['\"].*session-list['\"]" src/ --include="*.tsx" --include="*.ts" | grep -v node_modules
```
```bash
cd frontend && grep -rn "from.*search-options-dialog" src/ --include="*.tsx" --include="*.ts" | grep -v node_modules
```

- [ ] **Step 2: Create session/ directory and move files**

```bash
cd frontend/src/components
mkdir -p session
git mv conversation/content-renderer.tsx session/
git mv conversation/flow-diagram.tsx session/
git mv conversation/flow-layout.ts session/
git mv conversation/message-block.tsx session/step-block.tsx
git mv conversation/prompt-nav-panel.tsx session/
git mv conversation/session-view.tsx session/
git mv conversation/shared-session-view.tsx session/
git mv conversation/step-timeline.tsx session/
git mv conversation/sub-agent-block.tsx session/
git mv session-list.tsx session/
git mv search-options-dialog.tsx session/
rmdir conversation
```

- [ ] **Step 3: Update imports within session/ files**

Inside `session/session-view.tsx`, update:
```typescript
// Old:
import { StepBlock } from "./message-block";
// New:
import { StepBlock } from "./step-block";
```

All other intra-directory `./` imports within session/ files stay the same (they moved together).

Inside `session/session-list.tsx`, update the relative path for imports that changed depth:
```typescript
// Old (was at components/session-list.tsx):
import { SearchOptionsDialog } from "./search-options-dialog";
import { Tooltip } from "./tooltip";
// New (now at components/session/session-list.tsx):
import { SearchOptionsDialog } from "./search-options-dialog";  // same — moved together
import { Tooltip } from "../tooltip";  // now one level deeper
```

Update ALL imports in `session-list.tsx` from `../xxx` or `./xxx` patterns to account for the new depth:
- `from "../app"` → `from "../../app"`
- `from "../types"` → `from "../../types"`
- `from "../utils"` → `from "../../utils"`
- `from "../styles"` or `from "../constants"` → `from "../../styles"` or `from "../../constants"`
- `from "./tooltip"` → `from "../tooltip"`
- `from "./search-options-dialog"` stays `from "./search-options-dialog"` (moved together)

Same depth adjustments for `search-options-dialog.tsx` if it imports from root.

- [ ] **Step 4: Update all external imports**

```typescript
// In app.tsx:
import { SessionList, type ViewMode } from "./components/session-list"
// →
import { SessionList, type ViewMode } from "./components/session/session-list"

import { SessionView } from "./components/conversation/session-view"
// →
import { SessionView } from "./components/session/session-view"

import { SharedSessionView } from "./components/conversation/shared-session-view"
// →
import { SharedSessionView } from "./components/session/shared-session-view"

// In other components importing from conversation/:
import { StepBlock } from "../conversation/message-block"
// →
import { StepBlock } from "../session/step-block"

import { ... } from "../conversation/flow-diagram"
// →
import { ... } from "../session/flow-diagram"

// etc. for all conversation/* imports
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 6: Commit**

```bash
git add -A frontend/src/components/conversation/ frontend/src/components/session/ frontend/src/app.tsx frontend/src/components/
git commit -m "refactor: rename conversation/ to session/, rename message-block to step-block"
```

---

### Task 6: Create `upload/` directory (move + split upload-dialog.tsx)

Move `upload-dialog.tsx` from root to `upload/` directory. Extract constants and result stats into separate files.

**Files:**
- Move + Modify: `frontend/src/components/upload-dialog.tsx` → `frontend/src/components/upload/upload-dialog.tsx`
- Create: `frontend/src/components/upload/upload-constants.ts`
- Create: `frontend/src/components/upload/upload-result-stats.tsx`
- Modify: `frontend/src/app.tsx` (import path)

- [ ] **Step 1: Read full upload-dialog.tsx**

Read the entire file to identify exact line ranges for constants, ResultStats, and StatBox.

- [ ] **Step 2: Create upload/ directory**

```bash
mkdir -p frontend/src/components/upload
```

- [ ] **Step 3: Create `upload-constants.ts`**

Extract from upload-dialog.tsx: `AGENT_OPTIONS`, `OS_OPTIONS`, `AGENT_LABELS`, `DEFAULT_AGENT`, `DEFAULT_OS`, and the `Step` type, `WEB_EXPORT_STEPS` (if it exists as a constant).

```typescript
import type { AgentType, OSPlatform } from "../../types";

export type UploadStep = "select" | "upload" | "confirm" | "result";

export const AGENT_OPTIONS: { type: AgentType; label: string }[] = [
  { type: "claude_code", label: "Claude Code" },
  { type: "claude_code_web", label: "Claude Web" },
  { type: "codex", label: "Codex CLI" },
  { type: "gemini", label: "Gemini CLI" },
];

export const OS_OPTIONS: { platform: OSPlatform; label: string }[] = [
  { platform: "macos", label: "macOS" },
  { platform: "linux", label: "Linux" },
  { platform: "windows", label: "Windows" },
];

export const AGENT_LABELS: Record<AgentType, string> = {
  claude_code: "Claude Code",
  claude_code_web: "Claude Web",
  codex: "Codex CLI",
  gemini: "Gemini CLI",
};

export const DEFAULT_AGENT: AgentType = "claude_code";
export const DEFAULT_OS: OSPlatform = "macos";
```

- [ ] **Step 4: Create `upload-result-stats.tsx`**

Extract `ResultStats` and `StatBox` components from upload-dialog.tsx (approximately lines 557-633):

```tsx
import type { UploadResult } from "../../types";

export function ResultStats({ result }: { result: UploadResult }) {
  // Copy the exact ResultStats implementation from upload-dialog.tsx
  // (read the file in Step 1 to get the exact code)
}

function StatBox({ label, value }: { label: string; value: string | number }) {
  // Copy the exact StatBox implementation
}
```

- [ ] **Step 5: Move and slim upload-dialog.tsx**

```bash
git mv frontend/src/components/upload-dialog.tsx frontend/src/components/upload/upload-dialog.tsx
```

Update upload-dialog.tsx:
- Replace inline constants with imports from `./upload-constants`
- Replace inline ResultStats/StatBox with import from `./upload-result-stats`
- Update relative import paths (now one level deeper): `from "../app"` → `from "../../app"`, `from "./copy-button"` → `from "../copy-button"`, etc.

- [ ] **Step 6: Update external imports**

```typescript
// In app.tsx:
import { UploadDialog } from "./components/upload-dialog"
// →
import { UploadDialog } from "./components/upload/upload-dialog"
```

Check for any other files that import UploadDialog.

- [ ] **Step 7: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add -A frontend/src/components/upload-dialog.tsx frontend/src/components/upload/ frontend/src/app.tsx
git commit -m "refactor: move upload-dialog to upload/ directory, extract constants and result stats"
```

---

### Task 7: Create `llm/` directory (move + split llm-config.tsx)

Move `llm-config.tsx` from root to `llm/` directory. Extract constants/helpers and selector components.

**Files:**
- Move + Modify: `frontend/src/components/llm-config.tsx` → `frontend/src/components/llm/llm-config.tsx`
- Create: `frontend/src/components/llm/llm-config-constants.ts`
- Create: `frontend/src/components/llm/llm-config-selectors.tsx`
- Modify: Files importing `llm-config`

- [ ] **Step 1: Read full llm-config.tsx**

Read the entire file to identify exact line ranges for constants, ModelCombobox, CliModelSelector, BackendDropdown.

- [ ] **Step 2: Create llm/ directory**

```bash
mkdir -p frontend/src/components/llm
```

- [ ] **Step 3: Create `llm-config-constants.ts`**

Extract: `MODEL_PRESETS`, `BACKEND_OPTIONS`, `CLI_BACKENDS`, `ACCENT_STYLES` (type + object), `formatPrice`, `PricingLine`.

```typescript
export const MODEL_PRESETS = [
  "anthropic/claude-haiku-4-5",
  "anthropic/claude-sonnet-4-5",
  "openai/gpt-4.1",
  "openai/gpt-4.1-mini",
  "google/gemini-2.5-flash",
  "deepseek/deepseek-chat",
  "openrouter/anthropic/claude-sonnet-4-5",
];

export const BACKEND_OPTIONS = [
  { value: "litellm", label: "LiteLLM (recommended)" },
  { value: "aider", label: "Aider" },
  { value: "amp", label: "Amp" },
  { value: "claude_code", label: "Claude Code" },
  { value: "codex", label: "Codex" },
  { value: "cursor", label: "Cursor" },
  { value: "gemini", label: "Gemini CLI" },
  { value: "kimi", label: "Kimi" },
  { value: "opencode", label: "OpenCode" },
  { value: "openclaw", label: "OpenClaw" },
  { value: "disabled", label: "Disabled" },
];

export const CLI_BACKENDS = new Set([
  "aider", "amp", "claude_code", "codex", "cursor",
  "gemini", "kimi", "opencode", "openclaw",
]);

export type AccentColor = "amber" | "teal" | "cyan";

export const ACCENT_STYLES: Record<AccentColor, { focus: string; button: string; selected: string }> = {
  amber: {
    focus: "focus:border-amber-600",
    button: "bg-amber-600 hover:bg-amber-500",
    selected: "text-amber-700 dark:text-amber-400",
  },
  teal: {
    focus: "focus:border-teal-600",
    button: "bg-teal-600 hover:bg-teal-500",
    selected: "text-teal-700 dark:text-teal-400",
  },
  cyan: {
    focus: "focus:border-cyan-600",
    button: "bg-cyan-600 hover:bg-cyan-500",
    selected: "text-cyan-700 dark:text-cyan-400",
  },
};

export function formatPrice(price: number): string {
  return price < 0.01 ? price.toFixed(3) : price.toFixed(2);
}

export function PricingLine({ inputPrice, outputPrice }: { inputPrice: number; outputPrice: number }) {
  return (
    <p className="text-xs text-dimmed mt-1">
      ${formatPrice(inputPrice)} / ${formatPrice(outputPrice)} per MTok (in / out)
    </p>
  );
}
```

- [ ] **Step 4: Create `llm-config-selectors.tsx`**

Extract: `ModelCombobox`, `CliModelSelector`, `BackendDropdown`. These take props from the parent and manage their own dropdown state. Copy exact implementations from the original file. Import constants from `./llm-config-constants`.

- [ ] **Step 5: Move and slim llm-config.tsx**

```bash
git mv frontend/src/components/llm-config.tsx frontend/src/components/llm/llm-config.tsx
```

Update llm-config.tsx:
- Replace inline constants with imports from `./llm-config-constants`
- Replace inline selectors with imports from `./llm-config-selectors`
- Update relative import paths: `from "../types"` → `from "../../types"`, etc.

- [ ] **Step 6: Update external imports**

Find all files importing llm-config and update paths:
```bash
cd frontend && grep -rn "llm-config" src/ --include="*.tsx" --include="*.ts" | grep -v node_modules
```

- [ ] **Step 7: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add -A frontend/src/components/llm-config.tsx frontend/src/components/llm/ frontend/src/
git commit -m "refactor: move llm-config to llm/ directory, extract constants and selectors"
```

---

### Task 8: Split skill-analysis-views.tsx (1004 lines → 5 files)

Split the monolithic skill analysis view into an orchestrator plus 4 section files.

**Files:**
- Modify: `frontend/src/components/skills/skill-analysis-views.tsx` → rename to `skill-analysis-view.tsx`
- Create: `frontend/src/components/skills/skill-patterns-view.tsx`
- Create: `frontend/src/components/skills/skill-recommendations-view.tsx`
- Create: `frontend/src/components/skills/skill-creations-view.tsx`
- Create: `frontend/src/components/skills/skill-evolutions-view.tsx`
- Modify: Files importing from `skill-analysis-views`

- [ ] **Step 1: Read the full file**

Read `frontend/src/components/skills/skill-analysis-views.tsx` to identify exact line ranges for each section.

- [ ] **Step 2: Identify all imports of skill-analysis-views**

```bash
cd frontend && grep -rn "skill-analysis-views" src/ --include="*.tsx" --include="*.ts"
```

- [ ] **Step 3: Create `skill-patterns-view.tsx`**

Extract `PatternSection`, `PatternCard`, `StepRefList`, `JumpToStepButton` with their required imports. These components receive data via props — they don't call hooks or context.

- [ ] **Step 4: Create `skill-recommendations-view.tsx`**

Extract `RecommendationSection`, `RecommendationCard`, `ConfidenceBar` with their required imports. Note: `RecommendationCard` has state (expand/collapse) and calls `useDemoGuard()` hook.

- [ ] **Step 5: Create `skill-creations-view.tsx`**

Extract `CreationSection`, `CreatedSkillCard` with their required imports. `CreatedSkillCard` has significant state (editing, preview dialog, save flow).

- [ ] **Step 6: Create `skill-evolutions-view.tsx`**

Extract `EvolutionSection`, `EvolutionCard` with their required imports. Uses `EvolutionDiffView` from sibling file.

- [ ] **Step 7: Slim down orchestrator and rename**

```bash
cd frontend/src/components/skills
git mv skill-analysis-views.tsx skill-analysis-view.tsx
```

Keep in `skill-analysis-view.tsx`: `AnalysisLoadingState`, `AnalysisResultView`, `ResultHeader`, `SectionHeader`, `MetadataFooter`, helper functions (`formatDuration`, `getItemCount`), type exports (`SkillTab`), and constants (`CONFIDENCE_THRESHOLDS`, `MODE_TITLES`, `MODE_ITEM_LABELS`, `MODE_SUBLABELS`).

Add imports from the 4 new section files.

- [ ] **Step 8: Update external imports**

```typescript
// Old:
import { ... } from "./skill-analysis-views"
// New:
import { ... } from "./skill-analysis-view"
```

- [ ] **Step 9: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/components/skills/
git commit -m "refactor: split skill-analysis-views into orchestrator + 4 section files"
```

---

### Task 9: Split message-block.tsx into step-block + tool renderers

Split the 764-line message-block (already renamed to step-block.tsx in Task 5) into 3 focused files.

**Files:**
- Modify: `frontend/src/components/session/step-block.tsx` (slim down)
- Create: `frontend/src/components/session/tool-input-renderers.tsx`
- Create: `frontend/src/components/session/tool-output-renderers.tsx`

- [ ] **Step 1: Read the full file**

Read `frontend/src/components/session/step-block.tsx` to identify exact line ranges for tool rendering components.

- [ ] **Step 2: Create `tool-input-renderers.tsx`**

Extract: `ToolUseBlock`, `ToolInputRenderer`, `BashRenderer`, `EditRenderer`, `WriteRenderer`, `DiffLine`, and `getToolIconAndColor` helper. These are self-contained renderers that take `ToolCall` data as props.

Required imports: `lucide-react` icons, `diff` library (`createTwoFilesPatch`), types from `../../types`, `../../styles`.

- [ ] **Step 3: Create `tool-output-renderers.tsx`**

Extract: `ToolResultBlock`, `ToolOutput`, `tryFormatJson`, `getToolPreview`. These render `ObservationResult` data.

Required imports: `lucide-react` icons, `MarkdownRenderer` from `../markdown-renderer`, types from `../../types`.

- [ ] **Step 4: Slim down step-block.tsx**

Keep: `StepBlock` (dispatcher), `MessageBlock` (compat alias), `UserStep`, `SystemStep`, `SkillStep`, `AutoPromptStep`, `AgentStep`, `ConcurrentToolsBlock`, `TextBlock`, `ThinkingBlock`, and constants (`MAX_COLLAPSED_LINES`, `USER_PROMPT_COLLAPSE_LINE_THRESHOLD`).

Add imports from the 2 new files:
```typescript
import { ToolUseBlock, getToolIconAndColor } from "./tool-input-renderers";
import { ToolResultBlock } from "./tool-output-renderers";
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/session/
git commit -m "refactor: split step-block into tool-input-renderers and tool-output-renderers"
```

---

### Task 10: Split friction-panel.tsx into panel + sections + constants

Split the 761-line friction panel into focused files within the new `friction/` directory.

**Files:**
- Modify: `frontend/src/components/friction/friction-panel.tsx` (slim down)
- Create: `frontend/src/components/friction/friction-constants.ts`
- Create: `frontend/src/components/friction/friction-mitigations.tsx`
- Create: `frontend/src/components/friction/friction-types.tsx`

- [ ] **Step 1: Read the full file**

Read `frontend/src/components/friction/friction-panel.tsx` to identify exact line ranges for each section.

- [ ] **Step 2: Create `friction-constants.ts`**

Extract: `SEVERITY_LABELS`, `SEVERITY_DESCRIPTIONS`, `POLL_INTERVAL_MS`, `FRICTION_TUTORIAL`, `frictionTypeLabel`, `confidenceLevel`.

```typescript
export const SEVERITY_LABELS: Record<number, string> = {
  1: "Minor",
  2: "Low",
  3: "Moderate",
  4: "High",
  5: "Critical",
};

export const SEVERITY_DESCRIPTIONS: Record<number, string> = {
  1: "Minor — Small correction, resolved immediately",
  2: "Low — Needed to explain once more",
  3: "Moderate — Multiple corrections or visible frustration",
  4: "High — Had to take over or revert changes",
  5: "Critical — Gave up on the task entirely",
};

export const POLL_INTERVAL_MS = 3000;

export const FRICTION_TUTORIAL = {
  title: "How does this work?",
  description: "VibeLens reviews your coding sessions to find where things went wrong: getting stuck, repeating yourself, or fixing agent mistakes. You get practical tips to avoid those issues next time.",
};

export function frictionTypeLabel(typeName: string): string {
  return typeName
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function confidenceLevel(c: number): "high" | "medium" | "low" {
  if (c >= 0.7) return "high";
  if (c >= 0.4) return "medium";
  return "low";
}
```

- [ ] **Step 3: Create `friction-mitigations.tsx`**

Extract: `MitigationsSection`, `MitigationCard`, `ConfidenceBar`, `CostBadges`. These receive `Mitigation[]` data via props. Import `confidenceLevel` from `./friction-constants`.

- [ ] **Step 4: Create `friction-types.tsx`**

Extract: `FrictionTypesSection`, `FrictionTypeCard`, `FrictionRefList`, `FrictionStepButton`, `SeverityBadge`. Import `SEVERITY_LABELS`, `SEVERITY_DESCRIPTIONS`, `frictionTypeLabel` from `./friction-constants`.

- [ ] **Step 5: Slim down friction-panel.tsx**

Keep: `FrictionPanel` orchestrator, `ResultHeader`, `SectionHeader`, `AnalysisMeta`. Replace inline constants with imports from `./friction-constants`. Import section components from `./friction-mitigations` and `./friction-types`.

- [ ] **Step 6: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/friction/
git commit -m "refactor: split friction-panel into constants, mitigations, and types sections"
```

---

### Task 11: Split session-list.tsx and session-view.tsx

Extract sub-components from the two largest session files.

**Files:**
- Modify: `frontend/src/components/session/session-list.tsx`
- Create: `frontend/src/components/session/session-row.tsx`
- Create: `frontend/src/components/session/session-list-controls.tsx`
- Modify: `frontend/src/components/session/session-view.tsx`
- Create: `frontend/src/components/session/session-header.tsx`

- [ ] **Step 1: Read session-list.tsx and session-view.tsx**

Read both files to identify exact extraction boundaries.

- [ ] **Step 2: Create `session-row.tsx`**

Extract `SessionRow` component from session-list.tsx. It receives session data, selection state, and callbacks via props. Copy exact implementation including all imports it needs.

- [ ] **Step 3: Create `session-list-controls.tsx`**

Extract `AgentFilterDropdown` and `DonateButton` from session-list.tsx. Both are self-contained UI components with their own state.

- [ ] **Step 4: Slim session-list.tsx**

Replace extracted components with imports:
```typescript
import { SessionRow } from "./session-row";
import { AgentFilterDropdown, DonateButton } from "./session-list-controls";
```

- [ ] **Step 5: Create `session-header.tsx`**

Extract `MetaPill`, `TokenStat`, `CostStat`, `formatCreatedTime`, `_lookupFirstMessage` from session-view.tsx.

- [ ] **Step 6: Slim session-view.tsx**

Replace extracted components with imports:
```typescript
import { MetaPill, TokenStat, CostStat, formatCreatedTime, _lookupFirstMessage } from "./session-header";
```

- [ ] **Step 7: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/session/
git commit -m "refactor: extract session-row, session-list-controls, and session-header"
```

---

### Task 12: Split dashboard-view.tsx

Extract the `ProjectRow` component into its own file.

**Files:**
- Modify: `frontend/src/components/dashboard/dashboard-view.tsx`
- Create: `frontend/src/components/dashboard/project-row.tsx`

- [ ] **Step 1: Read dashboard-view.tsx**

Read the file to identify `ProjectRow` and `METRIC_LABEL` usage.

- [ ] **Step 2: Create `project-row.tsx`**

Extract `ProjectRow` component and `DEFAULT_PROJECT_COUNT` constant. Copy exact implementation.

- [ ] **Step 3: Slim dashboard-view.tsx**

Replace with import:
```typescript
import { ProjectRow } from "./project-row";
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: Zero TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/dashboard/
git commit -m "refactor: extract ProjectRow from dashboard-view"
```

---

### Task 13: Rebuild static assets and final verification

Rebuild the frontend and verify everything works end-to-end.

**Files:**
- Rebuild: `src/vibelens/static/` (frontend build output)

- [ ] **Step 1: Full build**

```bash
cd frontend && npm run build
```

Expected: Zero TypeScript errors, successful build.

- [ ] **Step 2: Copy built assets**

The Vite build outputs to `src/vibelens/static/`. Verify the build output is correct:
```bash
ls -la src/vibelens/static/assets/
```

- [ ] **Step 3: Run the app and smoke test**

```bash
cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run vibelens serve
```

Verify:
- Dashboard loads with charts
- Session list shows sessions
- Click a session → session view renders steps
- Open friction panel → loads analysis
- Open skills panel → shows tabs
- Upload dialog opens
- LLM config opens
- Settings dialog opens
- Confirm dialog works (try deleting a skill)

- [ ] **Step 4: Commit static assets**

```bash
git add src/vibelens/static/
git commit -m "build: rebuild frontend static assets after components refactor"
```

- [ ] **Step 5: Final commit log review**

```bash
git log --oneline -15
```

Verify all 13 commits are present and logically ordered.
