import { Check, Loader2, Monitor, Upload } from "lucide-react";
import { useCallback, useState } from "react";
import type { SkillSourceInfo } from "../../types";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "../modal";
import { SOURCE_LABELS } from "./skill-constants";

interface SkillUpdateDialogProps {
  skillName: string;
  initialContent: string;
  agentSources: SkillSourceInfo[];
  onUpdate: (content: string, targets: string[]) => void;
  onCancel: () => void;
  updating: boolean;
}

/**
 * Combined editor + target selection modal for applying evolution edits.
 * Users can review/tweak the merged SKILL.md content and choose which
 * agent interfaces to sync the updated skill to.
 */
export function SkillUpdateDialog({
  skillName,
  initialContent,
  agentSources,
  onUpdate,
  onCancel,
  updating,
}: SkillUpdateDialogProps) {
  const [content, setContent] = useState(initialContent);
  const [selectedTargets, setSelectedTargets] = useState<Set<string>>(new Set());

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

  const handleUpdate = useCallback(() => {
    onUpdate(content, [...selectedTargets]);
  }, [onUpdate, content, selectedTargets]);

  return (
    <Modal onClose={onCancel} maxWidth="max-w-4xl">
      <ModalHeader title={`Update: ${skillName}`} onClose={onCancel} />
      <ModalBody>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full min-h-[300px] bg-canvas text-secondary text-xs font-mono p-4 rounded-lg border border-card focus:border-amber-600/50 focus:outline-none resize-y leading-relaxed"
          spellCheck={false}
        />

        {/* Central store — always selected */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-teal-50 dark:bg-teal-900/15 border border-teal-200 dark:border-teal-800/40">
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
                      ? "bg-control border-amber-600/40"
                      : "bg-subtle border-card hover:border-hover"
                  }`}
                >
                  <div className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition ${
                    isSelected
                      ? "bg-amber-600 border-amber-500"
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
      </ModalBody>
      <ModalFooter>
        <button
          onClick={onCancel}
          disabled={updating}
          className="px-3 py-1.5 text-xs text-muted hover:text-secondary border border-card hover:border-hover rounded transition disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={handleUpdate}
          disabled={updating}
          className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 rounded transition disabled:opacity-50"
        >
          {updating
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <Upload className="w-3.5 h-3.5" />}
          {selectedTargets.size > 0
            ? `Update & Sync to ${selectedTargets.size}`
            : "Update"}
        </button>
      </ModalFooter>
    </Modal>
  );
}
