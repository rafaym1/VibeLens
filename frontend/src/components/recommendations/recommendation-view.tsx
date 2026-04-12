import { ArrowLeft, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type { CatalogRecommendation, RecommendationResult } from "../../types";
import { useAppContext } from "../../app";
import { RecommendationCard } from "./recommendation-card";

interface RecommendationViewProps {
  analysisId: string;
  onBack: () => void;
}

export function RecommendationView({ analysisId, onBack }: RecommendationViewProps) {
  const { fetchWithToken } = useAppContext();
  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchWithToken(`/recommendation/${analysisId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load recommendation: ${res.status}`);
        return res.json();
      })
      .then((data) => setResult(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [analysisId, fetchWithToken]);

  const handleInstall = useCallback((rec: CatalogRecommendation) => {
    if (rec.install_command) {
      navigator.clipboard.writeText(rec.install_command);
    }
    // TODO: integrate with install-target-dialog for file-based installs
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-400 dark:text-cyan-400/60" />
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{error ?? "No result found"}</p>
        <button onClick={onBack} className="text-sm text-cyan-600 dark:text-cyan-400 hover:underline">
          Back to sessions
        </button>
      </div>
    );
  }

  const costStr = result.metrics?.cost_usd != null ? `$${result.metrics.cost_usd.toFixed(2)}` : "";
  const durationStr = result.duration_seconds != null ? `${result.duration_seconds}s` : "";
  const metaParts = [
    `${result.session_ids.length} sessions analyzed`,
    durationStr,
    result.model,
    costStr,
  ].filter(Boolean);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="border-b border-zinc-200 dark:border-zinc-700 px-6 py-4 space-y-2 shrink-0">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to sessions
        </button>
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">{result.title}</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-300">{result.summary}</p>

        {/* Profile pills */}
        <div className="flex flex-wrap gap-1.5">
          {result.user_profile.domains.map((d) => (
            <span key={d} className="px-2 py-0.5 text-xs rounded-full bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400">
              {d}
            </span>
          ))}
          {result.user_profile.languages.map((l) => (
            <span key={l} className="px-2 py-0.5 text-xs rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
              {l}
            </span>
          ))}
          {result.user_profile.frameworks.map((f) => (
            <span key={f} className="px-2 py-0.5 text-xs rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400">
              {f}
            </span>
          ))}
        </div>

        <p className="text-xs text-zinc-400 dark:text-zinc-500">{metaParts.join(" · ")}</p>
      </div>

      {/* Card list */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {result.recommendations.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400 text-center py-8">
            No recommendations found.
          </p>
        ) : (
          result.recommendations.map((rec, idx) => (
            <RecommendationCard
              key={rec.item_id}
              recommendation={rec}
              rank={idx + 1}
              onInstall={handleInstall}
            />
          ))
        )}
      </div>
    </div>
  );
}
