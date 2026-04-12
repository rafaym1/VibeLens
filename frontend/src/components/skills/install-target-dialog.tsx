import { Check, Download, Loader2, Monitor } from "lucide-react";
import { useCallback, useState } from "react";
import type { SkillSourceInfo } from "../../types";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "../modal";
import { SOURCE_LABELS } from "./skill-constants";

interface InstallTargetDialogProps {
  skillName: string;
  agentSources: SkillSourceInfo[];
  onInstall: (targets: string[]) => void;
  onCancel: () => void;
}

/**
 * Dialog asking users which agent interfaces to install a skill to.
 * Always installs to the central store; optionally syncs to agent interfaces.
 */
export function InstallTargetDialog({
  skillName,
  agentSources,
  onInstall,
  onCancel,
}: InstallTargetDialogProps) {
  const [selectedTargets, setSelectedTargets] = useState<Set<string>>(new Set());
  const [installing, setInstalling] = useState(false);

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

  const handleInstall = useCallback(async () => {
    setInstalling(true);
    await onInstall([...selectedTargets]);
  }, [onInstall, selectedTargets]);

  return (
    <Modal onClose={onCancel} maxWidth="max-w-md">
      <ModalHeader title={`Install "${skillName}"`} onClose={onCancel} />
      <ModalBody>
        <p className="text-sm text-muted leading-relaxed">
          The skill will be saved to the VibeLens central store. Optionally sync it to your agent interfaces:
        </p>

        {/* Central store — always selected */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-teal-900/15 border border-accent-teal">
          <Check className="w-4 h-4 text-accent-teal shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-secondary">Central Store</p>
            <p className="text-xs text-dimmed">~/.vibelens/skills/</p>
          </div>
          <span className="text-[10px] text-accent-teal font-medium px-1.5 py-0.5 rounded bg-accent-teal-subtle">Always</span>
        </div>

        {/* Agent interface checkboxes */}
        {agentSources.length > 0 && (
          <div className="space-y-2">
            {agentSources.map((src) => {
              const isSelected = selectedTargets.has(src.key);
              return (
                <button
                  key={src.key}
                  onClick={() => toggleTarget(src.key)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border transition text-left ${
                    isSelected
                      ? "bg-control border-teal-600/40"
                      : "bg-subtle border-card hover:border-hover"
                  }`}
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
                  <span className="text-[10px] text-dimmed">
                    {src.skill_count} skill{src.skill_count !== 1 ? "s" : ""}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {agentSources.length === 0 && (
          <p className="text-xs text-dimmed italic">
            No agent interfaces detected. The skill will only be saved to the central store.
          </p>
        )}
      </ModalBody>
      <ModalFooter>
        <button
          onClick={onCancel}
          disabled={installing}
          className="px-3 py-1.5 text-xs text-muted hover:text-secondary border border-card hover:border-hover rounded transition disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={handleInstall}
          disabled={installing}
          className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded transition disabled:opacity-50"
        >
          {installing
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <Download className="w-3.5 h-3.5" />}
          {selectedTargets.size > 0
            ? `Install & Sync to ${selectedTargets.size} interface${selectedTargets.size !== 1 ? "s" : ""}`
            : "Install to Central"}
        </button>
      </ModalFooter>
    </Modal>
  );
}
