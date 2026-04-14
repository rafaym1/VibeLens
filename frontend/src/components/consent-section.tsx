import { Coins, HardDrive, Send, Shield } from "lucide-react";

const ANALYSIS_CONSENT_ITEMS: { icon: React.ReactNode; text: string }[] = [
  {
    icon: <Send className="w-4 h-4 text-violet-600 dark:text-violet-400 shrink-0 mt-0.5" />,
    text: "Your session data, including conversations, tool calls, and file paths, will be sent to a third-party AI provider for analysis.",
  },
  {
    icon: <Coins className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />,
    text: "This analysis will incur costs on your configured LLM API key.",
  },
  {
    icon: <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />,
    text: "VibeLens runs locally. Data is processed by the LLM provider for the API call but is not stored remotely.",
  },
  {
    icon: <HardDrive className="w-4 h-4 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />,
    text: "Analysis results are saved locally on your machine and can be deleted at any time.",
  },
];

export function ConsentSection({
  agreed,
  onAgreeChange,
}: {
  agreed: boolean;
  onAgreeChange: (checked: boolean) => void;
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-semibold text-primary">
        By proceeding, you acknowledge that:
      </p>
      <div className="space-y-2">
        {ANALYSIS_CONSENT_ITEMS.map((item, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-md bg-control/40 border border-card px-3.5 py-2.5"
          >
            {item.icon}
            <span className="text-sm text-secondary leading-relaxed">{item.text}</span>
          </div>
        ))}
      </div>
      <label className="flex items-center gap-3 cursor-pointer rounded-lg border border-hover bg-control/60 px-4 py-3 hover:border-teal-600/40 hover:bg-control/80 transition">
        <input
          type="checkbox"
          checked={agreed}
          onChange={(e) => onAgreeChange(e.target.checked)}
          className="w-4 h-4 rounded border-hover bg-control text-teal-500 focus:ring-teal-500 focus:ring-offset-0 cursor-pointer"
        />
        <span className="text-sm font-medium text-primary select-none">
          I understand and agree to proceed
        </span>
      </label>
    </div>
  );
}
