/** Color classes for recommendation item type badges. */
export const ITEM_TYPE_COLORS: Record<string, string> = {
  skill: "bg-cyan-100 text-cyan-800 border-cyan-300 dark:bg-cyan-900/30 dark:text-cyan-400 dark:border-cyan-700/30",
  subagent: "bg-violet-100 text-violet-800 border-violet-300 dark:bg-violet-900/30 dark:text-violet-400 dark:border-violet-700/30",
  command: "bg-teal-100 text-teal-800 border-teal-300 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-700/30",
  hook: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700/30",
  repo: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700/30",
};

/** Human-readable labels for item types. */
export const ITEM_TYPE_LABELS: Record<string, string> = {
  skill: "Skill",
  subagent: "Sub-agent",
  command: "Command",
  hook: "Hook",
  repo: "Repository",
};

/** Score bar color based on score value. */
export function scoreColor(score: number): string {
  if (score >= 0.7) return "bg-emerald-500 dark:bg-emerald-400";
  if (score >= 0.4) return "bg-amber-500 dark:bg-amber-400";
  return "bg-zinc-400 dark:bg-zinc-500";
}
