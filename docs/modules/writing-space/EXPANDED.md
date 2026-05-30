[Ver001.000]

# Writing Space — Expanded Module Documentation

> **Phase-2 W** in the Stage 3 documentation sprint continuation.
> Implementation-ready spec for the next agent picking up Writing Space.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Writing Space |
| **Slug (code)** | `writing-space` |
| **Status** | Documented (Accepted); implementation pending Phase 2 |
| **Owner role** | Implementer (with Designer for typography + Critic for export-fidelity tests) |
| **Channel** | `packages-engines` + `web-app` |
| **Gate protected** | `G2.writing-space` (currently LOCKED) |
| **Phase** | 2 (Phase 1 exit gates this; G2.* unlocks once D7 ≥ 18% and 5,000 MAU per `docs/product/OKRS.md`) |
| **Source ADRs** | **None Phase-1**. Recommends new ADR-0015 (editor stack — Tiptap vs Lexical vs Slate vs ProseMirror direct). Earlier PS-004 referenced "ADR-0011" but that slot is now Distraction Blocker — see §11 |
| **Source PS** | `docs/prototype-systems/PS-004-writing-space.md` |
| **Parent docs** | PRD §3.4 (Writing Space spec), `docs/product/MARKET_REVIEW.md` (Gap 5 — mobile writing tools are weak), `docs/product/PERSONAS.md` (Creative Professional persona § primary modules) |
| **Plan reference** | Stage 3 continuation per `.agents/handoff/stage-3-doc-expansion-next-session.md` |

Writing Space is the **Creative Professional persona's daily anchor**. Per
the market review's Gap 5 — "no mobile writing app combines desktop-class
project management with a truly mobile-first experience" — RAT-OS ships a
distraction-free chapter editor that wins specifically on mobile (where
Scrivener doesn't ship, Ulysses is Apple-only, iA Writer is minimalist
but not chapter-oriented).

The implementation must satisfy four structural properties:

1. **Mobile-first by default.** Touch-zone-aware margins, thumb-typing
   line spacing, pinch-zoom font scaling. Desktop is a wider variant of
   the same layout, not the source-of-truth shape.
2. **Local-first writing.** The editor writes to IndexedDB on every
   keystroke; vaultbrain sync happens at autosave intervals (10 s
   debounce) and on chapter transitions. A user with no network can
   write for hours without data loss.
3. **Export fidelity is a feature, not a finishing touch.** EPUB and
   DOCX exports get golden tests against reference manuscripts. PDF
   uses client-side rendering for free tier; server-side for premium
   custom-cover and KDP-compliant builds.
4. **Voice-to-text is degradable.** Native `SpeechRecognition` APIs
   differ across iOS/Android/Chrome/Firefox; UI never blocks input on
   voice; keyboard is always primary.

## 2. Architecture

```
apps/web/src/modules/writing-space/
  ├─ WriteRoute.tsx                   (was PhaseStub)
  ├─ Dashboard.tsx                    /write — manuscript grid
  ├─ ManuscriptView.tsx               /write/:id — chapter list + word-count
  ├─ ChapterEditor.tsx                /write/:id/c/:chapterId — full-screen
  └─ components/
       ├─ ManuscriptCard.tsx
       ├─ ChapterList.tsx              draggable, reorderable
       ├─ WritingCalendar.tsx          heat map of daily word counts
       ├─ EditorToolbar.tsx            B/I/H1-H3/lists/quote (rich-text)
       ├─ DictateButton.tsx            voice-to-text
       ├─ ExportDialog.tsx
       ├─ CoverPicker.tsx              10 templates + custom upload
       └─ CharacterPlacesPanel.tsx     character + setting trackers

packages/@njz-os/writing/src/
  ├─ manuscript.ts                    (existing) types
  ├─ export.ts                        (existing) types
  ├─ editor/
  │   ├─ adapter.ts                   Editor library facade (ADR-0015)
  │   ├─ schema.ts                    ProseMirror-style document schema
  │   ├─ autosave.ts                  Debounced IndexedDB → vaultbrain
  │   ├─ word-count.ts                Live + per-chapter counters
  │   └─ conflict.ts                  Last-write-wins + conflict markers
  └─ export/
       ├─ pdf.ts                       Client-side render (free)
       ├─ epub.ts                      Client-side render (premium)
       ├─ docx.ts                      Server-side via Phase-2 BFF (premium)
       ├─ markdown.ts                  Client-side (free)
       └─ txt.ts                       Client-side (free)

packages/adapters/vaultbrain-client/   metadata + small content snapshots
packages/adapters/api-client/          full chapter text persistence (Postgres)
```

Trade-offs already decided (PS-004):

- Mobile-first layout (PRD §3.4.2 — touch-zone-aware margins).
- Space Grotesk headings + Inter body (matches design tokens in `@njz-os/ui`).
- Three themes: light (warm paper), dark (deep charcoal), sepia (amber tint).
- Hide-UI / tap-to-reveal full-screen mode.

Trade-offs deferred to a Phase-2 ADR (recommended ADR-0015):

- **Editor library:** Tiptap (ProseMirror wrapper, React-friendly) vs
  Lexical (Meta's framework, smaller bundle, less mature) vs Slate
  (React-native, lighter mobile story) vs raw ProseMirror (max control,
  most code). Recommendation: **Tiptap** for mobile-first + React +
  rich-text breadth; falls back to Lexical if bundle size dominates.

Architecture extensions for implementation:

- **Chapter-level CRDT vs LWW.** Phase 2 ships last-write-wins with
  conflict markers (`>>>>>>> Concurrent edit at HH:MM`). Phase 4 may
  upgrade to a CRDT (Yjs / Automerge) if cross-device editing becomes
  common. Document the limitation in UI.
- **Hybrid storage:** chapter *metadata* (title, order, word count,
  status) lives in vaultbrain (small, sync-frequent); chapter *content*
  (Markdown body) lives in `services/api` Postgres (larger, sync on
  boundaries). The split is per PS-004.
- **Autosave triggers:** keystroke debounce (10 s), explicit "Save"
  button, route blur (e.g., navigating to another chapter), tab
  visibility change to hidden, online event after offline.

## 3. Domain types & contracts

### Existing types (`@njz-os/writing/src/manuscript.ts`, `export.ts`)

`Manuscript`, `Chapter`, `ChapterStatus`, `ExportFormat`, `ExportOptions`
are defined at Phase-0 stubs. Lane W extends these as follows.

```ts
// packages/@njz-os/writing/src/manuscript.ts (extend)
export interface ChapterContent {
  chapterId: string;
  markdown: string;            // canonical body — Markdown, never HTML
  updatedAt: string;
  wordCount: number;
  conflictMarkers?: ConflictMarker[];
}

export interface ConflictMarker {
  startOffset: number;
  endOffset: number;
  conflictingVersion: string;  // the rejected branch's text
  resolvedAt?: string;
}

export interface ManuscriptMetadata {
  // Same Manuscript fields, excluding chapter content
}
```

### Editor adapter surface (`packages/@njz-os/writing/src/editor/adapter.ts`)

```ts
// Insulates the rest of the app from the chosen editor lib (ADR-0015).
export interface EditorAdapter {
  mount(el: HTMLElement, opts: EditorMountOptions): EditorHandle;
}

export interface EditorMountOptions {
  initialMarkdown: string;
  onChange: (markdown: string, wordCount: number) => void;
  onSelectionChange?: (selection: { from: number; to: number }) => void;
  readOnly?: boolean;
  theme: 'light' | 'dark' | 'sepia';
  fontSizePx: number;
  lineHeight: 1.2 | 1.5 | 2.0;
}

export interface EditorHandle {
  getMarkdown(): string;
  setMarkdown(md: string): void;
  focus(): void;
  insertAtCursor(text: string): void;          // for dictation
  unmount(): void;
}
```

### Autosave controller (`autosave.ts`)

```ts
export interface AutosaveController {
  start(handle: EditorHandle, chapterId: string): void;
  flush(): Promise<void>;     // forces sync now
  stop(): void;
}

export function createAutosave(opts: {
  intervalMs?: number;        // default 10_000
  apiClient: ApiClient;       // for chapter content (Postgres)
  vaultbrain: VaultbrainClient; // for metadata + snapshots
}): AutosaveController;
```

Autosave path:

```
keystroke
  → debounce 500 ms
  → write to IndexedDB (apps/web local store)
  → debounce 10 s
  → write Markdown to services/api `PUT /manuscripts/{m}/chapters/{c}/content`
  → publish vaultbrain event `writing.autosave` (small metadata; no content)
```

### Export surface

```ts
// packages/@njz-os/writing/src/export.ts (extend)
export interface ExportRenderer {
  format: ExportFormat;
  render(manuscript: Manuscript, opts: ExportOptions): Promise<Blob>;
}

export const renderers: Record<ExportFormat, ExportRenderer>;
// Free: md, txt, pdf (client), share-to-web (URL)
// Premium: epub, docx (server-side via BFF)
```

### Vaultbrain endpoints

| Method | Path | When |
|--------|------|------|
| POST | `/users/{u}/manuscripts` | create manuscript |
| GET | `/users/{u}/manuscripts` | dashboard list |
| GET | `/users/{u}/manuscripts/{m}` | single manuscript metadata + chapter list |
| PUT | `/users/{u}/manuscripts/{m}` | update title, target, deadline |
| DELETE | `/users/{u}/manuscripts/{m}` | archive (soft-delete) |
| POST | `/users/{u}/manuscripts/{m}/chapters` | add chapter (returns id + order) |
| PUT | `/users/{u}/manuscripts/{m}/chapters/{c}` | reorder, rename, status |
| DELETE | `/users/{u}/manuscripts/{m}/chapters/{c}` | remove chapter |

### services/api endpoints (chapter *content* — Postgres truth)

| Method | Path | When |
|--------|------|------|
| GET | `/manuscripts/{m}/chapters/{c}/content` | hydrate editor on mount |
| PUT | `/manuscripts/{m}/chapters/{c}/content` | autosave |
| GET | `/manuscripts/{m}/export?format=docx` | server-side DOCX render (premium) |

Both endpoint sets sit behind `packages/adapters/{vaultbrain-client,api-client}`. The
`api-client` already exists from Lane F's Phase-0 stub.

## 4. Implementation walkthrough — task by task

### Task W1 — Pick editor stack (ADR-0015 first)

Open ADR-0015 weighing Tiptap / Lexical / Slate / ProseMirror direct.
Recommended decision (per §1 trade-off and §2 rationale): **Tiptap**.
Land the ADR before any code. This unblocks every subsequent task.

Commit (post-ADR-acceptance): no code yet — just the ADR.

### Task W2 — Editor adapter against the chosen lib

`pnpm --filter @njz-os/writing add @tiptap/react @tiptap/starter-kit @tiptap/extension-markdown` (or equivalents per chosen lib).

Implement `EditorAdapter` per §3 surface. Mount in a sandbox test page;
verify cursor + word count + Markdown round-trip.

Commit: `feat(writing): editor adapter (Tiptap-backed)`.

### Task W3 — Autosave + offline queue

`autosave.ts` per §3. IndexedDB layer via Dexie (or raw IndexedDB if
bundle-sensitive). Verify offline write → online flush.

Commit: `feat(writing): autosave with IndexedDB + vaultbrain sync`.

### Task W4 — Chapter list + manuscript shell

`ManuscriptView.tsx` mounts the chapter list (draggable, status per
chapter) and the word-count dashboard. `Dashboard.tsx` (`/write`) shows
the manuscript grid with cover thumbnails + sort/search/tag.

Commit: `feat(web/writing): manuscript dashboard + chapter list`.

### Task W5 — Full-screen editor route + theme + zoom

`ChapterEditor.tsx` mounts `EditorAdapter` full-screen with hide-UI /
tap-to-reveal toolbar. Theme switcher (light/dark/sepia). Pinch-zoom on
mobile maps to `fontSizePx` 12–24. Line spacing toggle.

Commit: `feat(web/writing): full-screen editor with theme + zoom`.

### Task W6 — Voice-to-text dictation

`DictateButton.tsx` wraps the browser's `SpeechRecognition` API
(prefixed `webkitSpeechRecognition` on iOS Safari). Continuous
dictation mode (Brainstorm Mode per PRD §3.4.5). Punctuation
auto-insertion via lightweight client-side post-processing. Errors
highlighted for quick correction.

Degradation matrix: unsupported browser ⇒ button disabled with
tooltip "Voice not supported on this browser".

Commit: `feat(web/writing): voice-to-text dictation with degradation`.

### Task W7 — Export renderers (free tier)

PDF, Markdown, plain-text, share-to-web. PDF via `pdfmake` or `jsPDF`
(client-side). Markdown is the canonical body — direct download.
Share-to-web posts to `services/api` `/manuscripts/{m}/share` and
returns a public URL with optional password protection.

Commit: `feat(writing): free-tier exports (pdf, md, txt, web)`.

### Task W8 — Export renderers (premium tier)

EPUB via `epub-gen` or `epub-press` (client-side OK). DOCX via the
Phase-2 BFF (`services/rat-os-api`) calling `pandoc` server-side for
fidelity. Cover image upload to vaultbrain blob storage.

Tier-gating via Lane E's `useTier()`.

Commit: `feat(writing): premium exports (epub client, docx server)`.

### Task W9 — Character + setting trackers, writing calendar

`CharacterPlacesPanel.tsx` — minimal CRUD (name, description, notes).
`WritingCalendar.tsx` — daily word-count heat map (52 weeks × 7 days).
Both consume vaultbrain.

Commit: `feat(writing): character/place trackers + writing calendar`.

### Task W10 — Tests + a11y + gate flip

Vitest covers chapter reorder, export round-trip, conflict marker
insertion. Playwright E2E: write 1000 words on mobile (touch events
simulated), close tab, reopen, verify content present. Golden export
tests against reference manuscripts (validate PDF, EPUB, DOCX).

A8-style gate flip (Task W10 last subtask) reserved for orchestrator.

Commit: `test(writing): unit + E2E + golden export tests`.

## 5. Telemetry & analytics events

| Event `kind` | When | Payload |
|--------------|------|---------|
| `writing.manuscript.create` | new manuscript | `{ userId, manuscriptId, targetWords }` |
| `writing.chapter.create` | new chapter | `{ userId, manuscriptId, chapterId }` |
| `writing.chapter.complete` | status → 'complete' | `{ userId, chapterId, wordCount }` |
| `writing.session.tick` | per autosave with words written | `{ userId, manuscriptId, chapterId, wordsThisSession, sessionMs }` |
| `writing.daily-goal.hit` | per-day word-count threshold met | `{ userId, dailyWords, target }` |
| `writing.export` | export rendered | `{ userId, manuscriptId, format, tier }` |
| `writing.manuscript.publish-to-web` | share URL generated | `{ userId, manuscriptId, urlId, passwordProtected }` |
| `writing.manuscript.50k` | first time crossing 50K words | `{ userId, manuscriptId }` — unlocks Author's Quill in PolyCo.World |

Extends `contracts/events/progression-events.json` — coordinate with
Lane F's continuous tasks (or via a follow-up Lane-F mini-PR).

OKR mapping (`docs/product/OKRS.md`):

- **O2.1 KR1** — Phase 2 launch of Writing Space module hits the
  module-launch box once `G2.writing-space` is OPEN.
- PRD §2.3.2 target — "Writing Space 20% of DAU @ Month 6, 40 min avg
  session, 15% on 7-day streak" — `writing.session.tick` durations
  drive both DAU% and session-length; `writing.daily-goal.hit`
  consecutive days drive streak.

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest | chapter reorder integrity; conflict-marker insertion; word-count accuracy across edge cases (em-dash, hyphenated, CJK if scope allows) |
| Unit | Vitest | each export renderer produces a non-empty Blob with expected MIME type |
| Integration | Vitest + msw | autosave → IndexedDB → vaultbrain → api-client (mocked) round trip |
| Golden | Vitest + epubcheck / docx-validator / qpdf | reference manuscripts → exports validate against external linters |
| E2E | Playwright (mobile viewport) | write 1000 words, close tab, reopen, verify content present |
| E2E | Playwright | export → download → re-import via Markdown shows identical body |
| Cross-browser | Playwright (Chromium, Firefox, WebKit) | core editor works everywhere; voice degrades gracefully |
| Mobile | manual iPhone 12 + mid-range Android | touch-zone margins; pinch-zoom font scaling; soft keyboard doesn't cover cursor |
| a11y | axe + manual | editor accessible to screen reader; toolbar buttons labelled; export dialog keyboard-only |
| Perf | Lighthouse | ≥ 85 on `/write/:id/c/:chapter` with a 10K-word chapter loaded |

Golden test corpus lives in `tests/fixtures/manuscripts/` — three
reference manuscripts (short story, novella sample, technical doc with
footnotes) authored in Markdown + reference outputs (PDF, EPUB, DOCX)
checked in.

## 7. Accessibility plan (WCAG 2.2 AA)

| Component | Requirement |
|-----------|-------------|
| `ChapterEditor` | Tab key works inside editor (escape-via-Esc focusable for keyboard users); on-screen toolbar reachable; screen reader announces "Editing chapter X — Y words" |
| `EditorToolbar` | Each button has `aria-label`; current style state exposed via `aria-pressed` |
| `DictateButton` | `aria-label="Start dictation"`; announces "Listening" / "Stopped" via `aria-live` |
| `ChapterList` | Drag handle keyboard-operable via Up/Down arrows (not just pointer); current position announced |
| `Dashboard` | Cards have `aria-label` summarising manuscript title + word count + status |
| `ExportDialog` | Modal with focus trap; Esc closes; format radio group `fieldset` + `legend` |
| `ManuscriptView` | `WritingCalendar` heat-map provides a `<table>` equivalent for screen readers |
| `CoverPicker` | Each template `aria-label`led; custom-upload button forwards keyboard focus |
| Reduced motion | Disable chapter-list reorder animation under `prefers-reduced-motion: reduce` |
| Color contrast | All three themes pass 4.5:1 body / 3:1 large-text |

Voice-to-text accessibility nuance: dictation is itself an
accessibility feature for users who can't type easily. The keyboard
fallback must always work alongside.

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Editor-lib choice (ADR-0015) blocks Phase-2 start | H | M | Recommend Tiptap and accept; revisit only if bundle ≥ 200 KB minified |
| Cross-device autosave race produces conflict markers user-visible | M | M | LWW with markers per PS-004; CRDT upgrade in Phase 4 if real-world conflicts > 5% of edits |
| Export fidelity edge cases (footnotes, italic in heading, em-dash) | M | M | Golden tests against reference corpus; pre-merge regression check |
| Voice-to-text variance across devices | M | L | Degrade gracefully; never block typing on dictation availability |
| Mobile soft keyboard covers cursor during writing | M | M | `scrollIntoView` on cursor change; manual smoke per release |
| Content licensing for cover templates | L | L | All 10 templates original or CC0; CI validator (Lane C) enforces |
| Pinch-zoom interferes with mobile-native gestures | M | L | Use `font-size` + CSS `transform` carefully; opt-out via setting |
| `services/api` chapter-content endpoint latency under burst typing | M | M | Debounce autosave (10 s); IndexedDB queues offline; flush on online event |
| User exports a 50K-word manuscript to PDF on mobile → freezes UI | M | M | Run PDF renderer in a Web Worker; show progress; cancel button |
| DOCX server-side render (Phase-2 BFF) increases Phase-2 infra cost | M | L | Pandoc is FOSS; Render free tier covers Phase-2 traffic; revisit if cost grows |

## 9. Cross-lane handoffs

| Direction | What | Counterparty |
|-----------|------|--------------|
| **Consumes** auth + tier | `useAuth()` for userId; `useTier()` for premium gating of EPUB/DOCX/custom cover | Lane E |
| **Consumes** FocusSession state | writing during a running focus session contributes to that session's word count metric | Lane A `useFocusSession()` |
| **Emits** `writing.manuscript.50k` to ProgressionEvent stream | PolyCo.World Office cabin unlocks Author's Quill decoration | Lane C subscriber |
| **Emits** chapter-completion → manuscript-completion → cabin exterior upgrade (PRD §3.4.6) | Lane C unlock rules consume the events | Lane C decoration-rules.ts |
| **Coordinates** new `writing.*` event names | canonical taxonomy update | Lane F (Coordination) |
| **Consumes** vaultbrain client + api-client | autosave + manuscript persistence | Lane F adapters |
| **Consumes** UI tokens | typography (Space Grotesk + Inter), color tokens, spacing scale | `@njz-os/ui` |

## 10. Out of scope (this module / phase)

- Co-authoring / multi-cursor — Phase 4+.
- AI writing assistant (autocomplete, restructure, polish) — Phase 4
  via agent-gateway integration.
- Direct publishing to Kindle Direct Publishing — manual EPUB export
  covers it.
- Image / illustration embedding inside chapters — Phase 3.
- Real-time word-count target nagging / streak shame — never; per
  ROOT_AXIOMS PR-03 (Trust & Privacy → opt-in for everything beyond
  core function).
- Plagiarism detection — out of scope entirely.
- Citation manager / footnote import from Zotero — Phase 5.
- Comments / margin notes — Phase 4.
- Version history beyond LWW conflict markers — Phase 4 (CRDT or full
  history snapshots).

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| **Editor library** (PRIMARY question — blocks everything) | Tiptap / Lexical / Slate / raw ProseMirror | Tiptap — mobile-first + React + rich-text breadth; bundle reasonable | Architect → ADR-0015 |
| Canonical body format — Markdown or HTML or ProseMirror JSON? | (a) Markdown (b) HTML (c) PM JSON | (a) Markdown — diff-friendly, portable, lossless for our subset | Architect |
| Where does *cover image* live? | (a) vaultbrain blob (b) services/api Postgres bytea (c) R2 | (a) Phase 2; consider (c) at scale | Architect |
| Conflict-marker UX — inline or sidebar? | (a) inline `>>>>>>> ` (b) sidebar diff view | (a) Phase 2 — simpler; (b) Phase 4 if user friction surfaces | Designer |
| Pinch-zoom font scaling — opt-in or default? | (a) default-on (b) setting | (a) — mobile users expect it; opt-out via setting | Designer |
| Autosave interval | 5s / 10s / 30s | 10s — survives accidental tab close, doesn't hammer the API | Implementer |
| Free-tier PDF — client or server? | (a) client (b) server | (a) — privacy + cost; covers must be simple in Phase 2 | Architect |
| Premium DOCX — client (mammoth/docx.js) or server (pandoc)? | (a) client (b) server | (b) — pandoc fidelity is better; BFF is the right home | Architect |
| Voice dictation — continuous or push-to-talk? | (a) continuous (b) PTT | (a) — matches PRD §3.4.5 Brainstorm Mode; PTT toggle in settings | Designer |
| Manuscript share-to-web — public or password-default? | (a) public (b) password-default | (a) — default to public with optional password; matches creator-friendly UX | Designer |
| Should completing a chapter contribute to Focus Hero streak? | (a) yes (counts as a session) (b) no | (a) — cross-module integration thesis; emits `session.complete` on chapter complete | Architect |
| Mobile soft-keyboard handling | (a) `scrollIntoView` (b) `visualViewport` API (c) both | (c) — both, for robustness | Implementer |

---

> **When implementing**, open ADR-0015 first to lock the editor library
> choice. Do not start Task W2 without ADR-0015 Accepted. Per the
> ROOT_AXIOMS/03_PROCEDURES/00-add-an-adr.md procedure, the ADR is
> a one-PR landing before any module code.

> **Do NOT** touch `.agents/PHASE_GATES.md`, ADRs 0001–0014, or other
> module routes. Stay inside `apps/web/src/modules/writing-space/`,
> `packages/@njz-os/writing/`, and `tests/fixtures/manuscripts/`.

> **See also:** PS-004, PRD §3.4, MARKET_REVIEW.md (Gap 5),
> PERSONAS.md (Creative Professional), `@njz-os/writing/src/{manuscript,export}.ts`.

## 12. Enterprise refinement plan

This lane's implementation has an enterprise-grade refinement plan
documented at `docs/program-management/PR-25-portfolio-uplift.md`. The
W-lane work items referenced there are:

- **PRX-25-SPRINT-01** — Editor-stack benchmark (settles ADR-0015).
- **PRX-25-PERF-01** — Bundle-size budget instrumentation.
- **PRX-25-PATCH-01** — Standardised event-emitter surface.
- **PRX-25-PATCH-02** — Shared progression-state hook.
- **PRX-25-ENH-02** — Optimistic UI updates (manuscript autosave).
- **PRX-25-ENH-05** — Shared design-token compile step.

In addition, the lane consumes the portfolio-wide **PRX-25-EPIC-01**
(`vaultbrain-client` production-grade adapter), which becomes the
manuscript persistence + sync layer. Open PR-25 before starting Task W2
to confirm the sprint cadence and ICE-ranked sequence for this lane.
