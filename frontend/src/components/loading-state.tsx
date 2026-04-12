import { Loader2 } from "lucide-react";

/** Centered spinner with a label, shown while data is loading. */
export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-16">
      <Loader2 className="w-6 h-6 text-zinc-400 dark:text-cyan-400/60 animate-spin" />
      <span className="ml-2 text-sm text-dimmed">{label}</span>
    </div>
  );
}
