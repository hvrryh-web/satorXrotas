/**
 * RAT-OS BFF aggregator (Phase 2+).
 *
 * Why a BFF exists separately from upstream services/api:
 * - Aggregates calls across vaultbrain + api + agent-gateway into webapp-shaped payloads.
 * - Hides server-only secrets that should not be exposed via NEXT_PUBLIC_*/VITE_*.
 * - Implements RAT-OS-specific server-side logic (e.g. DOCX export, premium gate enforcement)
 *   without polluting upstream services.
 *
 * Phase 0: not implemented. This file declares the contract surface only.
 */

export interface RatOsApi {
  readonly version: string;
  health(): Promise<{ status: 'ok' | 'degraded'; commit: string }>;
}

export const VERSION = '0.0.0';
