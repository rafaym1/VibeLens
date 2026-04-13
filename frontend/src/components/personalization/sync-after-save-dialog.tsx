import { Check, Loader2, Monitor, Share2, X } from "lucide-react";
import { useCallback, useState } from "react";
import type { SkillSourceInfo } from "../../types";
import { Modal, ModalBody, ModalFooter } from "../modal";
import { SOURCE_LABELS } from "./skill-constants";

interface SyncAfterSaveDialogProps {
  skillName: string;
  agentSources: SkillSourceInfo[];
  fetchWithToken: (url: string, init?: RequestInit) => Promise<Response>;
  onClose: () => void;
}

/**
 * Dialog shown after saving a skill edit, asking whether to sync
 * the updated skill to other agent interfaces.
 */
export function SyncAfterSaveDialog({
  skillName,
  agentSources,
  fetchWithToken,
  onClose,
}: SyncAfterSaveDialogProps) {
  const [selectedTargets, setSelectedTargets] = useState<Set<string>>(new Set());
  const [syncing, setSyncing] = useState(false);
  const [syncDone, setSyncDone] = useState(false);

  const toggleTarget = useCallback((key: string) => {
    setSelectedTargets((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const handleSync = useCallback(async () => {
    if (selectedTargets.size === 0) {
      onClose();
      return;
    }
    setSyncing(true);
    try {
      await fetchWithToken(`/api/skills/sync/${skillName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ targets: [...selectedTargets] }),
      });
      setSyncDone(true);
      setTimeout(onClose, 800);
    } catch {
      onClose();
    }
  }, [fetchWithToken, skillName, selectedTargets, onClose]);

  return (
    <Modal onClose={onClose} maxWidth="max-w-md">
      <div className="flex items-center justify-between px-5 py-4 border-b border-default shrink-0">
        <div className="flex items-center gap-2.5">
          <Share2 className="w-4 h-4 text-accent-teal" />
          <h2 className="text-sm font-semibold text-primary">
            Sync changes to agent interfaces?
          </h2>
        </div>
        <button onClick={onClose} className="text-dimmed hover:text-secondary transition">
          <X className="w-4 h-4" />
        </button>
      </div>
      <ModalBody>
        <p className="text-sm text-muted leading-relaxed">
          You updated <span className="font-mono text-secondary">{skillName}</span>.
          Would you like to sync the changes to your agent interfaces?
        </p>

        {agentSources.length > 0 && (
          <div className="space-y-2">
            {agentSources.map((src) => {
              const isSelected = selectedTargets.has(src.key);
              return (
                <button
                  key={src.key}
                  onClick={() => toggleTarget(src.key)}
                  disabled={syncing || syncDone}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border transition text-left ${
                    isSelected
                      ? "bg-control border-teal-600/40"
                      : "bg-subtle border-card hover:border-hover"
                  } disabled:opacity-60`}
                >
                  <div className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition ${
                    isSelected
                      ? "bg-teal-600 border-teal-500"
                      : "border-hover"
                  }`}>
                    {isSelected && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <Monitor className="w-4 h-4 text-muted shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-secondary">
                      {SOURCE_LABELS[src.key] || src.label}
                    </p>
                    <p className="text-xs text-dimmed truncate">{src.skills_dir}</p>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </ModalBody>
      <ModalFooter>
        <button
          onClick={onClose}
          disabled={syncing}
          className="px-3 py-1.5 text-xs text-muted hover:text-secondary border border-card hover:border-hover rounded transition disabled:opacity-50"
        >
          Skip
        </button>
        <button
          onClick={handleSync}
          disabled={syncing || syncDone}
          className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded transition disabled:opacity-50"
        >
          {syncDone
            ? (<><Check className="w-3.5 h-3.5" /> Synced</>)
            : syncing
              ? (<Loader2 className="w-3.5 h-3.5 animate-spin" />)
              : (<><Share2 className="w-3.5 h-3.5" /> Sync</>)}
        </button>
      </ModalFooter>
    </Modal>
  );
}
