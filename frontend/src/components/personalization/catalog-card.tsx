import { Check, Download, ExternalLink, Loader2, Star } from "lucide-react";
import { formatCount } from "./catalog-format";
import { useCallback, useState } from "react";
import { useAppContext } from "../../app";
import type { CatalogItemSummary } from "../../types";
import { Tooltip } from "../tooltip";
import {
  CARD_VIEW_MAX_TAGS,
  ITEM_TYPE_COLORS,
  ITEM_TYPE_LABELS,
  LIST_VIEW_MAX_TAGS,
  type CatalogViewMode,
} from "./catalog-constants";

export function TypeBadge({ itemType }: { itemType: string }) {
  const color = ITEM_TYPE_COLORS[itemType] || ITEM_TYPE_COLORS.skill;
  const label = ITEM_TYPE_LABELS[itemType] || itemType;
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${color}`}>
      {label}
    </span>
  );
}

function TagList({ tags, max }: { tags: string[]; max: number }) {
  if (tags.length === 0) return null;
  const visible = tags.slice(0, max);
  const overflow = tags.length - max;
  return (
    <div className="flex flex-wrap gap-1 mt-1.5">
      {visible.map((tag) => (
        <span
          key={tag}
          className="text-[10px] px-1.5 py-0.5 rounded-full bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
        >
          {tag}
        </span>
      ))}
      {overflow > 0 && (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500">
          +{overflow}
        </span>
      )}
    </div>
  );
}

function InstallButton({
  installing,
  onInstall,
}: {
  installing: boolean;
  onInstall: (e: React.MouseEvent) => void;
}) {
  return (
    <button
      onClick={onInstall}
      disabled={installing}
      className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-white bg-teal-600 hover:bg-teal-500 rounded transition disabled:opacity-50"
    >
      {installing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
      Install
    </button>
  );
}

function QualityBar({ score }: { score: number }) {
  return (
    <Tooltip text={`Quality: ${score}/100`}>
      <span className="flex items-center gap-1">
        <span className="inline-block w-12 h-1 rounded-full bg-zinc-200 dark:bg-zinc-700 overflow-hidden">
          <span className="block h-full bg-teal-500 rounded-full" style={{ width: `${score}%` }} />
        </span>
        {Math.round(score)}
      </span>
    </Tooltip>
  );
}

interface CatalogCardProps {
  item: CatalogItemSummary;
  isInstalled: boolean;
  onInstalled: (itemId: string) => void;
  onViewDetail: (item: CatalogItemSummary) => void;
  viewMode?: CatalogViewMode;
}

export function CatalogCard({
  item,
  isInstalled,
  onInstalled,
  onViewDetail,
  viewMode = "list",
}: CatalogCardProps) {
  const { fetchWithToken } = useAppContext();
  const [installing, setInstalling] = useState(false);
  const [installed, setInstalled] = useState(isInstalled);
  const [error, setError] = useState<string | null>(null);

  const handleInstall = useCallback(
    async (e: React.MouseEvent) => {
      e.stopPropagation();
      setInstalling(true);
      setError(null);
      try {
        const res = await fetchWithToken(`/api/catalog/${encodeURIComponent(item.item_id)}/install`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target_platform: "claude_code" }),
        });
        if (res.status === 409) {
          const retry = await fetchWithToken(`/api/catalog/${encodeURIComponent(item.item_id)}/install`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_platform: "claude_code", overwrite: true }),
          });
          if (!retry.ok) throw new Error((await retry.json().catch(() => ({}))).detail || `HTTP ${retry.status}`);
        } else if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `HTTP ${res.status}`);
        }
        setInstalled(true);
        onInstalled(item.item_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setInstalling(false);
      }
    },
    [fetchWithToken, item.item_id, onInstalled],
  );

  const borderClass = installed
    ? "border-emerald-300/40 bg-emerald-50/50 dark:border-emerald-800/40 dark:bg-emerald-950/20"
    : "border-card bg-panel hover:bg-control/80";

  if (viewMode === "card") {
    return (
      <div
        className={`border rounded-lg transition cursor-pointer flex flex-col h-full ${borderClass}`}
        onClick={() => onViewDetail(item)}
      >
        <div className="px-4 pt-3 pb-2 flex flex-col flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-semibold text-primary truncate">{item.name}</span>
            <TypeBadge itemType={item.item_type} />
            {installed && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-700/30 font-medium">
                Installed
              </span>
            )}
          </div>
          <p className="text-sm text-secondary mt-1 line-clamp-3">{item.description}</p>
          <TagList tags={item.tags} max={CARD_VIEW_MAX_TAGS} />
          {error && <p className="text-[10px] text-red-500 mt-1">{error}</p>}
          <div className="flex items-center justify-between mt-auto pt-3 text-[10px] text-muted">
            <div className="flex items-center gap-2">
              <span>{item.category}</span>
              {item.stars > 0 && (
                <span className="flex items-center gap-0.5">
                  <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                  {formatCount(item.stars)}
                </span>
              )}
              {item.language && <span>{item.language}</span>}
            </div>
            <div className="flex items-center gap-2">
              <QualityBar score={item.quality_score} />
              {item.source_url && (
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-1 text-faint hover:text-secondary rounded transition"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
              {item.is_file_based && !installed && (
                <InstallButton installing={installing} onInstall={handleInstall} />
              )}
              {installed && (
                <span className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                  <Check className="w-3 h-3" />
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`border rounded-lg transition cursor-pointer ${borderClass}`}
      onClick={() => onViewDetail(item)}
    >
      <div className="px-4 py-3 flex items-start gap-3 min-w-0">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-semibold text-primary truncate">{item.name}</span>
            <TypeBadge itemType={item.item_type} />
            {installed && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-700/30 font-medium">
                Installed
              </span>
            )}
          </div>
          <p className="text-sm text-secondary mt-1 line-clamp-2">{item.description}</p>
          <TagList tags={item.tags} max={LIST_VIEW_MAX_TAGS} />
          <div className="flex items-center gap-3 mt-2 text-[10px] text-muted">
            <span>{item.category}</span>
            <QualityBar score={item.quality_score} />
            {item.stars > 0 && (
              <span className="flex items-center gap-0.5">
                <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                {formatCount(item.stars)}
              </span>
            )}
            {item.language && <span>{item.language}</span>}
          </div>
          {error && <p className="text-[10px] text-red-500 mt-1">{error}</p>}
        </div>
        <div className="shrink-0 flex items-center gap-1.5 mt-1">
          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-1.5 text-faint hover:text-secondary rounded transition"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
          {item.is_file_based && !installed && (
            <InstallButton installing={installing} onInstall={handleInstall} />
          )}
          {installed && (
            <span className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
              <Check className="w-3 h-3" />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
