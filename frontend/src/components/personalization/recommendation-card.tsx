import { Copy, ExternalLink } from "lucide-react";
import type { CatalogRecommendation } from "../../types";
import { ITEM_TYPE_COLORS, ITEM_TYPE_LABELS, scoreColor } from "./recommendation-constants";

const MAX_VISIBLE_TAGS = 4;

interface RecommendationCardProps {
  recommendation: CatalogRecommendation;
  rank: number;
  onInstall: (rec: CatalogRecommendation) => void;
}

function QualityBadge({ score }: { score: number }) {
  const label = score >= 80 ? "High" : score >= 50 ? "Good" : "Low";
  const color =
    score >= 80
      ? "text-emerald-600 dark:text-emerald-400"
      : score >= 50
        ? "text-amber-600 dark:text-amber-400"
        : "text-zinc-500 dark:text-zinc-400";
  return (
    <span className={`text-xs font-medium tabular-nums ${color}`}>
      {label} ({score})
    </span>
  );
}

export function RecommendationCard({ recommendation: rec, rank, onInstall }: RecommendationCardProps) {
  const typeColor = ITEM_TYPE_COLORS[rec.item_type] ?? ITEM_TYPE_COLORS.skill;
  const typeLabel = ITEM_TYPE_LABELS[rec.item_type] ?? rec.user_label;
  const barColor = scoreColor(rec.score);
  const confidencePct = Math.round(rec.confidence * 100);
  const tags: string[] = (rec as CatalogRecommendation & { tags?: string[] }).tags?.slice(0, MAX_VISIBLE_TAGS) ?? [];
  const canInstall = rec.has_content || rec.install_command;

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800/50 p-4 space-y-3">
      {/* Header: rank + type badge + name */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-sm font-medium text-zinc-400 dark:text-zinc-500 w-6 shrink-0">
          #{rank}
        </span>
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full border shrink-0 ${typeColor}`}>
          {typeLabel}
        </span>
        <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 truncate">
          {rec.name}
        </h3>
      </div>

      {/* Description */}
      <p className="text-sm text-zinc-600 dark:text-zinc-300">{rec.description}</p>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 text-xs rounded-full bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Rationale callout */}
      <div className="rounded-md bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 px-3 py-2">
        <p className="text-sm text-zinc-700 dark:text-zinc-300 italic">{rec.rationale}</p>
      </div>

      {/* Quality score + confidence bar */}
      <div className="flex items-center gap-3">
        <QualityBadge score={rec.quality_score} />
        <div className="flex-1 h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-700 overflow-hidden">
          <div className={`h-full rounded-full ${barColor}`} style={{ width: `${confidencePct}%` }} />
        </div>
        <span className="text-xs text-zinc-500 dark:text-zinc-400 tabular-nums shrink-0">
          {confidencePct}% match
        </span>
      </div>

      {/* Install button */}
      {canInstall && (
        <button
          onClick={() => onInstall(rec)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-teal-600 hover:bg-teal-500 text-white transition-colors"
        >
          <Copy className="w-4 h-4" />
          Install
        </button>
      )}

      {/* Source URL */}
      {rec.source_url && (
        <a
          href={rec.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400 hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          Source
        </a>
      )}
    </div>
  );
}
