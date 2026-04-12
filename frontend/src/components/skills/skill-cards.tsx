import {
  Check,
  Code2,
  Loader2,
  Package,
  Pencil,
  Share2,
  FileText,
  Tag,
  Trash2,
  Wrench,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDemoGuard } from "../../hooks/use-demo-guard";
import type { SkillInfo, SkillSourceInfo } from "../../types";
import { InstallLocallyDialog } from "../install-locally-dialog";
import { MarkdownRenderer } from "../markdown-renderer";
import { Modal, ModalHeader, ModalBody } from "../modal";
import { Tooltip } from "../tooltip";
import { SourceBadge, SubdirList, TagList, TagPill, ToolBadge, ToolList } from "./skill-badges";
import { SOURCE_LABELS } from "./skill-constants";

/** Compact card for a locally installed skill in the list view. */
export function SkillCard({
  skill,
  onEdit,
  onDelete,
  onViewDetail,
}: {
  skill: SkillInfo;
  onEdit: (skill: SkillInfo) => void;
  onDelete: (name: string) => void;
  onViewDetail: (skill: SkillInfo) => void;
}) {
  const tags = (skill.metadata?.tags as string[]) || [];
  const lineCount = (skill.metadata?.line_count as number) || 0;
  const allowedTools = (skill.metadata?.allowed_tools as string[]) || [];

  return (
    <div className="border border-card rounded-lg bg-panel hover:bg-control/80 transition">
      <div className="flex items-start">
        <button
          onClick={() => onViewDetail(skill)}
          className="flex-1 text-left px-4 py-3 flex items-start gap-3 min-w-0"
        >
          <div className="shrink-0 mt-0.5 p-1.5 rounded-md bg-accent-teal-subtle">
            <Package className="w-4 h-4 text-accent-teal" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-sm font-semibold text-primary">{skill.name}</span>
              {skill.sources
                .filter((s) => s.source_type !== "central")
                .map((src) => (
                  <SourceBadge key={src.source_type} sourceType={src.source_type} sourcePath={src.source_path} />
                ))}
              {lineCount > 0 && (
                <span className="text-xs text-muted">{lineCount} lines</span>
              )}
            </div>
            <p className="text-sm text-secondary mt-1 line-clamp-2">
              {skill.description || "No description"}
            </p>
            <TagList tags={tags} />
            <ToolList tools={allowedTools} />
          </div>
        </button>
        <div className="flex items-center gap-1 px-2 py-3 shrink-0">
          <Tooltip text="Edit skill">
            <button
              onClick={() => onEdit(skill)}
              className="p-1.5 text-dimmed hover:text-accent-teal hover:bg-control-hover rounded transition"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip text="Delete skill">
            <button
              onClick={() => onDelete(skill.name)}
              className="p-1.5 text-dimmed hover:text-red-600 dark:hover:text-red-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 rounded transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}

/** Full-screen detail popup for a locally installed skill, with sync controls. */
export function SkillDetailPopup({
  skill: initialSkill,
  agentSources,
  onClose,
  fetchWithToken,
  onRefresh,
}: {
  skill: SkillInfo;
  agentSources: SkillSourceInfo[];
  onClose: () => void;
  fetchWithToken: (url: string, init?: RequestInit) => Promise<Response>;
  onRefresh: () => void;
}) {
  const { guardAction, showInstallDialog, setShowInstallDialog } = useDemoGuard();
  const [skill, setSkill] = useState<SkillInfo>(initialSkill);
  const [content, setContent] = useState<string | null>(null);
  const [loadingContent, setLoadingContent] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const tags = useMemo(() => (skill.metadata?.tags as string[]) || [], [skill.metadata]);
  const allowedTools = useMemo(() => (skill.metadata?.allowed_tools as string[]) || [], [skill.metadata]);
  const subdirs = useMemo(() => (skill.metadata?.subdirs as string[]) || [], [skill.metadata]);
  const lineCount = (skill.metadata?.line_count as number) || 0;

  useEffect(() => {
    (async () => {
      try {
        const res = await fetchWithToken(`/api/skills/local/${skill.name}`);
        if (res.ok) {
          const data = await res.json();
          setContent(data.content || "");
        }
      } catch {
        /* ignore */
      } finally {
        setLoadingContent(false);
      }
    })();
  }, [fetchWithToken, skill.name]);

  const handleSync = useCallback(
    async (targetKey: string) => {
      setSyncing(targetKey);
      setSyncMessage(null);
      try {
        const res = await fetchWithToken(`/api/skills/sync/${skill.name}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ targets: [targetKey] }),
        });
        if (res.ok) {
          const data = await res.json();
          const result = data.results?.[targetKey];
          if (result?.synced) {
            setSyncMessage(`Synced to ${SOURCE_LABELS[targetKey] || targetKey}`);
            if (data.skill) setSkill(data.skill as SkillInfo);
            onRefresh();
          } else {
            setSyncMessage(`Failed: ${result?.error || "Unknown error"}`);
          }
        }
      } catch (err) {
        setSyncMessage(`Error: ${err}`);
      } finally {
        setSyncing(null);
      }
    },
    [fetchWithToken, skill.name, onRefresh],
  );

  return (
    <Modal onClose={onClose} maxWidth="max-w-3xl">
      <ModalHeader onClose={onClose}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent-teal-subtle">
            <Package className="w-5 h-5 text-accent-teal" />
          </div>
          <div>
            <h2 className="text-lg font-bold font-mono text-primary">{skill.name}</h2>
            {lineCount > 0 && (
              <span className="text-xs text-secondary">{lineCount} lines in SKILL.md</span>
            )}
          </div>
        </div>
      </ModalHeader>

      <ModalBody>
        {/* Skill Description */}
        <div>
          <SectionTitle icon={<FileText className="w-4 h-4" />} label="Skill Description" />
          <p className="text-sm text-secondary leading-relaxed">
            {skill.description || "No description"}
          </p>
        </div>

        {/* Metadata grid: tags, tools, subdirs */}
        {(tags.length > 0 || allowedTools.length > 0 || subdirs.length > 0) && (
          <div className="rounded-lg border border-card bg-panel divide-y divide-card">
            {/* Tags + Tools row */}
            {(tags.length > 0 || allowedTools.length > 0) && (
              <div className="px-4 py-3 flex flex-wrap gap-x-6 gap-y-2">
                {tags.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <SectionLabel icon={<Tag className="w-3 h-3" />} label="Tags" inline />
                    {tags.map((tag) => <TagPill key={tag} tag={tag} />)}
                  </div>
                )}
                {allowedTools.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <SectionLabel icon={<Wrench className="w-3 h-3" />} label="Tools" inline />
                    {allowedTools.map((tool) => <ToolBadge key={tool} tool={tool} />)}
                  </div>
                )}
              </div>
            )}

            {/* Subdirectories */}
            {subdirs.length > 0 && (
              <div className="px-4 py-3">
                <SectionLabel label="Directories" inline />
                <SubdirList dirs={subdirs} />
              </div>
            )}
          </div>
        )}

        {/* Sync to agent interfaces — show all agents from backend */}
        {agentSources.length > 0 && (
          <div className="rounded-lg border border-teal-200 dark:border-teal-800/40 bg-teal-50 dark:bg-teal-950/10 px-4 py-3">
            <SectionTitle icon={<Share2 className="w-4 h-4" />} label="Sync to Agent Interfaces" />
            <div className="flex flex-wrap gap-2">
              {agentSources.map((src) => {
                const installedSource = skill.sources.find((s) => s.source_type === src.key);
                const isSynced = !!installedSource || skill.skill_targets.includes(src.key);
                const hasDir = !!src.skills_dir;
                const tooltipText = isSynced
                  ? installedSource?.source_path ?? `Synced to ${src.label}`
                  : hasDir
                    ? `Sync to ${src.skills_dir}`
                    : `${src.label} not installed on this system`;
                return (
                  <Tooltip key={src.key} text={tooltipText}>
                    <button
                      onClick={() => guardAction(() => handleSync(src.key))}
                      disabled={syncing === src.key || (!isSynced && !hasDir)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border transition ${
                        isSynced
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-700/30"
                          : hasDir
                            ? "bg-control/60 text-muted border-hover/60 hover:text-accent-teal hover:border-accent-teal-focus/50 hover:bg-teal-50 dark:hover:bg-teal-950/20"
                            : "bg-subtle text-faint border-card cursor-not-allowed"
                      } disabled:opacity-50`}
                    >
                      {syncing === src.key ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : isSynced ? (
                        <Check className="w-3 h-3" />
                      ) : (
                        <Share2 className="w-3 h-3" />
                      )}
                      {src.label}
                    </button>
                  </Tooltip>
                );
              })}
            </div>
            {syncMessage && (
              <p className="text-xs text-emerald-600/80 dark:text-emerald-400/70 mt-1.5">{syncMessage}</p>
            )}
          </div>
        )}

        {/* Skill Content */}
        <div>
          <SectionTitle icon={<Code2 className="w-4 h-4" />} label="Skill Content" />
          {loadingContent ? (
            <div className="flex items-center gap-2 py-4">
              <Loader2 className="w-4 h-4 text-zinc-400 dark:text-cyan-400/60 animate-spin" />
              <span className="text-xs text-dimmed">Loading...</span>
            </div>
          ) : content ? (
            <div className="bg-control/80 rounded-lg p-4 max-h-80 overflow-y-auto border border-card">
              <MarkdownRenderer content={_stripFrontmatter(content)} />
            </div>
          ) : (
            <p className="text-xs text-dimmed italic">No content</p>
          )}
        </div>
      </ModalBody>

      {showInstallDialog && (
        <InstallLocallyDialog onClose={() => setShowInstallDialog(false)} />
      )}
    </Modal>
  );
}

/** Prominent section title with icon for major sections in detail popups. */
function SectionTitle({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2 mb-2.5">
      <span className="text-accent-teal">{icon}</span>
      <span className="text-sm font-semibold text-primary">{label}</span>
    </div>
  );
}

/** Small label used as section header or inline label inside detail popups. */
function SectionLabel({ icon, label, inline }: { icon?: React.ReactNode; label: string; inline?: boolean }) {
  return (
    <div className={`flex items-center gap-1.5 text-xs text-muted shrink-0 ${inline ? "" : "mb-2"}`}>
      {icon}
      <span>{label}</span>
    </div>
  );
}

/** Strip YAML frontmatter (--- ... ---) from SKILL.md content for rendering. */
function _stripFrontmatter(text: string): string {
  const match = text.match(/^---\n[\s\S]*?\n---\n?/);
  return match ? text.slice(match[0].length).trimStart() : text;
}
