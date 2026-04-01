# Optimized Prompt: Wireframe Generation v3
## For Established Chats (1 Token Per Response)

---

## PROMPT (COPY & PASTE)

```
AGENT: IMPLEMENTER [#ORG]
TASK: TENET Portal Wireframe v3

SPEC (STRICT):
├── Background: #0A0A0A
├── Border-radius: 0px (ALL elements)
├── 4 HUB tiles: 280×320px, 2×2 grid
│   ├── ROTAS (teal accent #14B8A6)
│   ├── SATOR (teal accent)
│   ├── OPERA (orange accent #F97316)
│   └── AREPO (orange accent)
├── 2 Game tiles: 360×200px
│   ├── Valorant (vignette + LIVE badge #FF4655)
│   └── CS2 (vignette + OFFLINE overlay)
├── ZERO feature cards (remove 4×2 grid)
├── Color rules:
│   ├── #14B8A6 (TEAL) → Data only
│   ├── #F97316 (ORG) → Buttons only
│   └── #F8FAFC → Text only
└── Typography: Inter + JetBrains Mono

VALIDATE BEFORE SUBMIT:
[ ] 0px radius everywhere
[ ] Exactly 4 HUB tiles
[ ] Zero feature cards
[ ] Teal only on data/hover
[ ] Orange only on CTAs
[ ] Vignette masks on games
[ ] No scroll (100vh)

OUTPUT: Single HTML file, inline CSS.
START NOW. CONFIRM RECEIPT.
```

---

## DELIVERABLE CHECKLIST

Agent responds with:

```
RECEIVED. Implementing TENET Portal v3.

VALIDATION:
[✓] Radius: 0px
[✓] 4 HUB tiles
[✓] 0 feature cards
[✓] Teal: data only
[✓] Orange: CTAs only
[✓] Vignettes: applied
[✓] No scroll: confirmed

FILE: 01-tenet-portal-v3.html
SIZE: XX KB
READY FOR CRIT.
```

---

## IF SPEC AMBIGUOUS

Agent asks:
```
CLARIFY: [specific question]
OPTIONS: [A] [B] [C]
```

You respond with letter only.

---

## COMMUNICATION PROTOCOL

| You Say | Agent Does |
|---------|------------|
| "START" | Confirms receipt, begins work |
| "CHECK" | Reports progress % |
| "STOP" | Pauses, saves state |
| "CRIT" | Sends to CRITIC agent |
| "DONE?" | Returns validation checklist |

---

## ERROR HANDLING

If agent violates spec:
```
VIOLATION: [specific issue]
FIX: [exact correction]
RESUBMIT: Yes/No
```

You respond: "FIX" or "REJECT"

---

## TOKEN OPTIMIZATION

Each response from agent must:
- Be under 400 tokens
- Include validation checklist
- No prose, no explanations
- Code blocks only when delivering

---

Prompt Version: 3.0.0
Optimization: 1-token responses
Last Updated: 2026-03-31
