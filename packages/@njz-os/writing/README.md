# @njz-os/writing

Manuscript + chapter data model + export descriptors.

## Surface (Phase 0 stubs)

- `manuscript` — `Manuscript`, `Chapter`, `ChapterStatus`
- `export` — `ExportFormat`, `ExportOptions`

## Phase 2 Implementation

Editor lives in `apps/web/src/modules/writing-space/`. Stack TBD via ADR-0011 (candidates: Tiptap, Lexical, Slate, ProseMirror direct).

PDF/EPUB rendering client-side; DOCX rendering server-side via `services/api`.

See `docs/prototype-systems/PS-004-writing-space.md`.
