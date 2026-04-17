import { useEffect, useState } from "react";
import type { ExtensionSyncTarget } from "../../../types";
import { extensionEndpoint, normalizeSyncTargets } from "./extension-endpoints";

/** Extension types with typed list endpoints that expose sync_targets. */
export const SYNC_TARGET_TYPES = ["skill", "subagent", "command", "hook"] as const;

type SyncTargetsByType = Record<string, ExtensionSyncTarget[]>;

/**
 * Fetch per-type sync targets once. Each typed list endpoint
 * (/api/skills, /api/subagents, /api/commands, /api/hooks) exposes
 * `sync_targets`; this hook normalizes them into the shared
 * ExtensionSyncTarget shape, keyed by extension_type.
 */
export function useSyncTargetsByType(
  fetchWithToken: (url: string, init?: RequestInit) => Promise<Response>,
): SyncTargetsByType {
  const [syncTargetsByType, setSyncTargetsByType] = useState<SyncTargetsByType>({});

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      SYNC_TARGET_TYPES.map(async (type) => {
        const endpoint = extensionEndpoint(type);
        if (!endpoint) return [type, [] as ExtensionSyncTarget[]] as const;
        try {
          const res = await fetchWithToken(`${endpoint}?page_size=1`);
          if (!res.ok) return [type, [] as ExtensionSyncTarget[]] as const;
          const data = await res.json();
          return [type, normalizeSyncTargets(type, data)] as const;
        } catch {
          return [type, [] as ExtensionSyncTarget[]] as const;
        }
      }),
    ).then((entries) => {
      if (!cancelled) setSyncTargetsByType(Object.fromEntries(entries));
    });
    return () => { cancelled = true; };
  }, [fetchWithToken]);

  return syncTargetsByType;
}
