[Ver001.000]

# PS-004 — Writing Space

- **Status:** Draft (Phase 0); flips to Approved when ADR-0011 lands.
- **Owner:** Implementer (Phase 2)
- **Phase:** 2
- **Package:** `@njz-os/writing`
- **Gate:** `G2.writing-space`

## Purpose

Mobile-first distraction-free chapter editor for creative writing. Targets the Creative Professional persona. Wins where Ulysses (Apple-only), Scrivener (desktop-only), and iA Writer (not chapter-oriented) fall short.

## Surface

```ts
import { createManuscript, exportManuscript, type Manuscript } from '@njz-os/writing';

const m = createManuscript({ title, targetWords: 80000 });
m.addChapter({ title: 'Chapter 1' });
const pdf = await exportManuscript(m, { format: 'pdf' });
```

UI in `apps/web`:

- `/write` — project dashboard (manuscripts grid).
- `/write/:id` — manuscript view (chapter list + word count + heat map).
- `/write/:id/c/:chapter` — full-screen editor.

## Domain Types

- `Manuscript`, `Chapter`, `ExportFormat` (see SCHEMA_REGISTRY).

## Integration Points

- **Vaultbrain:** chapter metadata + small content snapshots; full content in `services/api` Postgres.
- **Focus Hero:** writing during a focus session contributes to session word-count metric.
- **PolyCo.World:** chapter completion adds books to Office cabin bookshelf; 50K+ words unlocks Author's Quill.
- **Analytics:** word-count series feeds writing-streak progression.

## Risks

- **Autosave conflict on poor connectivity.** Concurrent edits across devices risk overwrite. Mitigation: CRDT or last-write-wins with conflict markers; explicit per-chapter locking optional.
- **Export fidelity.** EPUB / DOCX edge cases (footnotes, italics in headings). Mitigation: golden tests against reference manuscripts.
- **Voice-to-text variance across devices.** OS-native APIs differ. Mitigation: degrade gracefully; offer keyboard fallback always.

## Verification

- Unit: chapter reorder maintains content integrity.
- Unit: export functions produce valid PDF / EPUB / DOCX (validated with markdown-pdf, epubcheck, docx-validator).
- E2E: write 1000 words on mobile; close tab; reopen; content present.

## Out of Scope (Phase 2)

- Co-authoring / multi-cursor (Phase 4+).
- AI writing assistant (Phase 4+, integration via agent-gateway).
- Direct publishing to Kindle Direct Publishing — manual EPUB export covers it.
- Image / illustration embedding in manuscripts — Phase 3.

## References

- PRD §3.4.
- ADR-0011 (editor stack — TBD; candidates: Tiptap, Lexical, Slate, ProseMirror direct).

---

> **Implementation-ready expanded spec:** `docs/modules/writing-space/EXPANDED.md`
