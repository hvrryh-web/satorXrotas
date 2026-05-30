/**
 * PRX-25-EPIC-01 — Offline queue (in-memory scaffold).
 *
 * Events recorded while the client is offline (no network, no auth)
 * persist in this queue and are flushed FIFO when the client reports
 * back online. PRX-25-ENH-01 will swap the in-memory store for IndexedDB
 * via idb-keyval; the public surface here stays stable.
 *
 * Idempotency keys (UUID v7) are attached at enqueue time so server-side
 * de-duplication is robust even if the queue drains across reconnects.
 */

import { z } from 'zod';

export const queuedItemSchema = z.object({
  id: z.string().uuid(),
  kind: z.string(),
  payload: z.unknown(),
  enqueuedAt: z.string().datetime(),
  attempts: z.number().int().min(0),
});

export type QueuedItem = z.infer<typeof queuedItemSchema>;

export interface QueueStore {
  enqueue(item: QueuedItem): Promise<void>;
  drain(): Promise<QueuedItem[]>;
  ack(id: string): Promise<void>;
  size(): Promise<number>;
}

export function createInMemoryQueue(): QueueStore {
  const items = new Map<string, QueuedItem>();
  return {
    async enqueue(item) {
      items.set(item.id, item);
    },
    async drain() {
      return Array.from(items.values()).sort((a, b) =>
        a.enqueuedAt.localeCompare(b.enqueuedAt)
      );
    },
    async ack(id) {
      items.delete(id);
    },
    async size() {
      return items.size;
    },
  };
}

let uuidCounter = 0;
/**
 * UUID v7 (time-ordered). Real UUID v7 is spec'd to use ms timestamp +
 * random; this is a lightweight Node/browser-portable implementation
 * suitable for an idempotency key. Order-preserving across reconnects.
 */
export function uuidV7(): string {
  const ms = Date.now();
  uuidCounter = (uuidCounter + 1) & 0xfff;
  const counter = uuidCounter;
  const rand = Math.floor(Math.random() * 0xffffffff);
  const hex = (n: number, w: number): string => n.toString(16).padStart(w, '0');
  const msHex = hex(ms, 12);
  const r1 = hex(counter, 3);
  const r2 = hex(rand & 0xffff, 4);
  const r3 = hex((rand >>> 16) & 0xffff, 4);
  const r4 = hex(Math.floor(Math.random() * 0xffffffff), 8);
  return (
    msHex.slice(0, 8) +
    '-' +
    msHex.slice(8, 12) +
    '-' +
    '7' + // version
    r1 +
    '-' +
    '8' + // variant high nibble (10x)
    r2.slice(1) +
    '-' +
    r3 +
    r4
  );
}
