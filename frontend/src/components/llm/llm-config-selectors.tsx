import { ChevronDown } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import type { CliBackendModels } from "../../types";
import {
  ACCENT_STYLES,
  BACKEND_OPTIONS,
  MODEL_PRESETS,
  PricingLine,
  formatPrice,
  type AccentColor,
} from "./llm-config-constants";

export function ModelCombobox({
  value,
  onChange,
  accentColor = "cyan",
}: {
  value: string;
  onChange: (v: string) => void;
  accentColor?: AccentColor;
}) {
  const [open, setOpen] = useState(false);
  const [dropUp, setDropUp] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const accent = ACCENT_STYLES[accentColor];
  const query = value.toLowerCase();
  const filteredPresets = MODEL_PRESETS.filter((p) => p.toLowerCase().includes(query));

  // Flip dropdown upward when insufficient space below
  const DROPDOWN_HEIGHT = 192;
  const updateDropDirection = useCallback(() => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    setDropUp(spaceBelow < DROPDOWN_HEIGHT && rect.top > spaceBelow);
  }, []);

  return (
    <div className="relative" ref={containerRef}>
      <div className="flex">
        <input
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            updateDropDirection();
            setOpen(true);
          }}
          onFocus={() => {
            updateDropDirection();
            setOpen(true);
          }}
          placeholder="Type or select a model..."
          className={`w-full px-3 py-2 bg-control border border-card rounded-lg text-sm text-secondary placeholder-zinc-500 focus:outline-none ${accent.focus} pr-8`}
        />
        <button
          type="button"
          onClick={() => {
            updateDropDirection();
            setOpen((v) => !v);
          }}
          className="absolute right-0 inset-y-0 px-2 flex items-center text-dimmed hover:text-secondary hover:bg-control/30 rounded-r-lg transition"
        >
          <ChevronDown className={`w-3.5 h-3.5 transition ${open ? "rotate-180" : ""}`} />
        </button>
      </div>
      {open && filteredPresets.length > 0 && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <ul
            className={`absolute z-20 w-full max-h-48 overflow-y-auto bg-control border border-card rounded-lg shadow-xl ${
              dropUp ? "bottom-full mb-1" : "top-full mt-1"
            }`}
          >
            {filteredPresets.map((preset) => (
              <li key={preset}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(preset);
                    setOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-control-hover transition ${
                    value === preset ? accent.selected : "text-secondary"
                  }`}
                >
                  {preset}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export function CliModelSelector({
  backendId,
  value,
  onChange,
  cliModels,
  accentColor = "cyan",
}: {
  backendId: string;
  value: string;
  onChange: (v: string) => void;
  cliModels: Record<string, CliBackendModels>;
  accentColor?: AccentColor;
}) {
  const [open, setOpen] = useState(false);
  const accent = ACCENT_STYLES[accentColor];
  const meta = cliModels[backendId];

  if (!meta || meta.models.length === 0) {
    return (
      <p className="text-xs text-dimmed">
        No model selection available for this backend.
      </p>
    );
  }

  const selectedModel = meta.models.find((m) => m.name === value);

  if (meta.supports_freeform) {
    return (
      <div>
        <div className="relative">
          <div className="flex">
            <input
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onFocus={() => setOpen(true)}
              placeholder={meta.default_model ?? "model name"}
              className={`w-full px-3 py-2 bg-control border border-card rounded-lg text-sm text-secondary placeholder-zinc-500 focus:outline-none ${accent.focus} pr-8`}
            />
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="absolute right-0 inset-y-0 px-2 flex items-center text-dimmed hover:text-secondary hover:bg-control/30 rounded-r-lg transition"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>
          {open && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
              <ul className="absolute z-20 mt-1 w-full max-h-64 overflow-y-auto bg-control border border-card rounded-lg shadow-xl">
                {meta.models.map((m) => (
                  <li key={m.name}>
                    <button
                      type="button"
                      onClick={() => { onChange(m.name); setOpen(false); }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-control-hover transition flex justify-between ${
                        value === m.name ? accent.selected : "text-secondary"
                      }`}
                    >
                      <span>{m.name}</span>
                      {m.input_per_mtok != null && (
                        <span className="text-dimmed text-xs">${formatPrice(m.input_per_mtok)} / ${formatPrice(m.output_per_mtok!)}</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
        {selectedModel?.input_per_mtok != null && (
          <PricingLine inputPrice={selectedModel.input_per_mtok} outputPrice={selectedModel.output_per_mtok!} />
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className={`w-full flex items-center justify-between px-3 py-2 bg-control border border-card rounded-lg text-sm text-secondary focus:outline-none ${accent.focus} transition`}
        >
          <span>{value || meta.default_model || "Select model"}</span>
          <ChevronDown className={`w-3.5 h-3.5 text-dimmed transition ${open ? "rotate-180" : ""}`} />
        </button>
        {open && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
            <ul className="absolute z-20 mt-1 w-full max-h-64 overflow-y-auto bg-control border border-card rounded-lg shadow-xl">
              {meta.models.map((m) => (
                <li key={m.name}>
                  <button
                    type="button"
                    onClick={() => { onChange(m.name); setOpen(false); }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-control-hover transition flex justify-between ${
                      value === m.name ? accent.selected : "text-secondary"
                    }`}
                  >
                    <span>{m.name}</span>
                    {m.input_per_mtok != null && (
                      <span className="text-dimmed text-xs">${formatPrice(m.input_per_mtok)} / ${formatPrice(m.output_per_mtok!)}</span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
      {selectedModel?.input_per_mtok != null && (
        <PricingLine inputPrice={selectedModel.input_per_mtok} outputPrice={selectedModel.output_per_mtok!} />
      )}
    </div>
  );
}

export function BackendDropdown({
  value,
  onChange,
  accentColor = "cyan",
}: {
  value: string;
  onChange: (v: string) => void;
  accentColor?: AccentColor;
}) {
  const [open, setOpen] = useState(false);
  const accent = ACCENT_STYLES[accentColor];
  const selected = BACKEND_OPTIONS.find((o) => o.value === value);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`w-full flex items-center justify-between px-3 py-2 bg-control border border-card rounded-lg text-sm text-secondary focus:outline-none ${accent.focus} transition`}
      >
        <span>{selected?.label ?? value}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-dimmed transition ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <ul className="absolute z-20 mt-1 w-full max-h-64 overflow-y-auto bg-control border border-card rounded-lg shadow-xl">
            {BACKEND_OPTIONS.map((opt) => (
              <li key={opt.value}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-control-hover transition ${
                    value === opt.value ? accent.selected : "text-secondary"
                  }`}
                >
                  {opt.label}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
