/** Badge colors for catalog item types. */
export const ITEM_TYPE_COLORS: Record<string, string> = {
  skill: "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-700/30",
  subagent: "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-900/30 dark:text-violet-400 dark:border-violet-700/30",
  command: "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-900/30 dark:text-sky-400 dark:border-sky-700/30",
  hook: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700/30",
  repo: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-700/30",
};

/** Human-readable labels for item types. */
export const ITEM_TYPE_LABELS: Record<string, string> = {
  skill: "Skill",
  subagent: "Agent",
  command: "Command",
  hook: "Hook",
  repo: "MCP",
};

/** Platform display labels. */
export const PLATFORM_LABELS: Record<string, string> = {
  claude_code: "Claude Code",
  codex: "Codex",
  gemini: "Gemini",
};

/** Items per page for catalog browsing. */
export const CATALOG_PAGE_SIZE = 50;
