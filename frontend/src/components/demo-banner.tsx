import { Info } from "lucide-react";

export function DemoBanner() {
  return (
    <div className="px-3 py-2 rounded-lg bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800/40">
      <div className="flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-accent-cyan shrink-0 mt-0.5" />
        <p className="text-xs text-accent-cyan/90">
          This is sample data for demonstration.{" "}
          Install VibeLens locally (<code className="px-1 py-0.5 bg-control rounded text-[11px]">pip install vibelens</code>)
          to run real LLM-powered analysis on your own sessions.
        </p>
      </div>
    </div>
  );
}
