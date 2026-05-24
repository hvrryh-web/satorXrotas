[Ver001.000]

# Data Flow — NJZ RAT-OS

> Sequence diagrams + state ownership for the most common interactions. Pairs with `SYSTEM_OVERVIEW.md`.

## Convention

```
Actor / surface       →  emits or initiates
Module package        ▲  produces value
Adapter               │  network boundary
Upstream service      ●  persistent / authoritative
```

---

## Flow 1 — Start a Focus Session

```
User              apps/web                @njz-os/focus-engine    vaultbrain-client    services/vaultbrain
 │                  │                           │                       │                    │
 │ tap "Start" ────►│                           │                       │                    │
 │                  │ startSession({mode}) ────►│                       │                    │
 │                  │                           │ stateMachine.start    │                    │
 │                  │                           │ emit('session.start') │                    │
 │                  │◄── { sessionId, state } ──│                       │                    │
 │                  │ POST /sessions/start ────────────────────────────►│                    │
 │                  │                           │                       │ persist ──────────►●
 │                  │◄── 201 { id, timeline } ───────────────────────────                    │
 │                  │ subscribe(WS) ───────────────────────────────────►│                    │
 │                  │                           │                       │ (tick events) ────►│
 │                  │ render countdown          │                       │                    │
 │                  │                           │                       │                    │
 │ session ends ───►│                           │                       │                    │
 │                  │ emit('session.complete') ►│                       │                    │
 │                  │                           │ progression.award(xp) │                    │
 │                  │ POST /progression/event ─────────────────────────►│                    │
 │                  │                           │                       │ persist ──────────►●
 │                  │ update PolyCo decorations │                       │                    │
```

Key points:

- Focus engine is *local-first*: countdown runs against `Date.now()`, not server time.
- Vaultbrain is the source of truth for cross-device sync.
- Progression events are emitted at session boundaries (start, complete, abandon), not every tick.

---

## Flow 2 — Soundscape Playback with Deep Canvas

```
User              apps/web        @njz-os/audio-engine                 polyworld canvas
 │                  │                     │                                  │
 │ pick track ─────►│                     │                                  │
 │                  │ play({track}) ─────►│                                  │
 │                  │                     │ AudioContext.resume()            │
 │                  │                     │ load stems → loop graph          │
 │                  │                     │ analyserNode.connect()           │
 │                  │                     │                                  │
 │                  │ open Deep Canvas ──────────────────────────────────────►│
 │                  │                                                        │ requestAnimationFrame
 │                  │                                                        │ FFT.getByteFrequencyData()
 │                  │                                                        │ paint based on band energy
 │                  │                                                        │
 │ session ends ───►│                                                        │
 │                  │ snapshot canvas to PNG ◄──────────────────────────────│
 │                  │ save to vaultbrain user.gallery                        │
```

Key points:

- Audio runs entirely client-side. No server in the loop for playback.
- Web Audio `AnalyserNode` feeds the canvas; FFT runs at 60fps on the main thread (mobile-acceptable for current track count).
- Generative artwork is captured via `canvas.toBlob` at session end and persisted to vaultbrain.

---

## Flow 3 — Cross-Device Sync

```
Device A                 vaultbrain         Device B
   │                          │                  │
   │ session.complete ───────►●                  │
   │                          │ broadcast event  │
   │                          │ ────────────────►│ update streak counter
   │                          │                  │ animate Office decoration
```

Vaultbrain pushes events over WebSocket to all connected sessions for the user. Subscription set up at adapter init.

---

## Flow 4 — Write + Export a Manuscript

```
User       apps/web       @njz-os/writing       api-client       services/api
 │           │                  │                    │                 │
 │ type ────►│                  │                    │                 │
 │           │ autosave (1s) ─►│                    │                 │
 │           │                  │ PATCH /manuscripts/{id} ─────────────►● update content
 │           │                  │                    │                 │
 │ export ──►│                  │                    │                 │
 │           │ exportToPdf ───►│                    │                 │
 │           │                  │ render (client)    │                 │
 │           │ download         │                    │                 │
```

PDF/EPUB rendering is client-side (no server roundtrip). DOCX export (premium) uses server-side `pandoc` via `services/api` for fidelity.

---

## Flow 5 — Distraction Blocker (Web)

```
User       Service Worker          @njz-os/focus-engine          apps/web
 │            │                            │                         │
 │ start ──── │ ◄──────────────────────────│                         │
 │            │ install rules              │                         │
 │            │                            │                         │
 │ tries to load blocked URL              │                         │
 │            │ intercept → block          │                         │
 │            │ navigate to /focus-active ──────────────────────────►│ render motivational screen
 │                                                                    │ POST /block-attempts → vaultbrain
 │            │ session ends               │                         │
 │            │ uninstall rules            │                         │
```

Native (iOS/Android) blocker is Phase 3 and uses Screen Time API / DigitalWellbeing APIs through native wrappers.

---

## State Ownership Matrix

| Data | Owner | Persistence | Sync |
|------|-------|-------------|------|
| Current focus session timeline | `@njz-os/focus-engine` (in-memory) | Vaultbrain on boundaries | Real-time WS |
| Streak state | Vaultbrain | Yes | Real-time WS |
| XP totals | Vaultbrain | Yes | Real-time WS |
| Cognitive profile vector | Vaultbrain | Yes | On-demand |
| Manuscripts | `services/api` (Postgres) | Yes | On-demand |
| Blocker schedule | Vaultbrain | Yes | On-demand |
| Soundscape favorites | Vaultbrain | Yes | On-demand |
| PolyCo.World scene | Vaultbrain (snapshots) + client (live) | Yes | On-demand |
| Generative canvas artwork | Vaultbrain (PNG blobs) | Yes | On-demand |
| Learning card progress | Vaultbrain | Yes | On-demand |
| Subscription tier | Vaultbrain (cached) + Identity (truth) | Yes | On-demand |

## Failure-Mode Behaviour

| Service down | RAT-OS behaviour |
|--------------|------------------|
| Vaultbrain unreachable | Continue local-first; queue events; flush on reconnect; show "syncing…" badge |
| Agent gateway unreachable | AI helpers disabled; rest of app functional |
| API unreachable | Cold reads from TanStack Query cache; mutations fail with retry-now toast |
| Identity unreachable (no fresh token) | Allow session for token's lifetime; force re-auth on expiry |

## See Also

- `MODULE_BOUNDARIES.md` — what can import what.
- `contracts/events/progression-events.json` — canonical event list.
- `ADR-0003-vaultbrain-as-state-backend.md`.
