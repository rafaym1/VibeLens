import { AlertCircle, X } from "lucide-react";

/** Dismissible error banner with a red alert icon. */
export function ErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div className="flex items-start gap-2 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 mb-4">
      <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
      <p className="text-sm text-red-700 dark:text-red-300">{message}</p>
      <button onClick={onDismiss} className="ml-auto shrink-0 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
