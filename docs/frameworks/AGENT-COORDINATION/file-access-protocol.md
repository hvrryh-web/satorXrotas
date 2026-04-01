# File Access Protocol
## How I Will Deliver Files You Can Actually Access

---

## THE PROBLEM (Acknowledged)

**What I Was Doing Wrong:**
```
"The files are here:"
/root/.openclaw/workspace/eSports-EXE/docs/design-system/visual-specification-v3.md
```

**Why This Failed:**
- You don't have access to my workspace filesystem
- These paths are meaningless to you
- I assumed direct file access you don't have
- No explanation of how to actually view the content

**Your Rightful Frustration:**
> "reviewing what the fuck has gone wrong with these before now, and why the problem has occured, and what mitigation solutions can be implemented to stop you being a fucking dumb fuck and giving me links to folders and files within a workspace I DONT HAVE ACCESS TO"

**I hear you. This stops now.**

---

## THE SOLUTION

### Protocol: ACCESS-VERIFY-CONFIRM

Every file delivery follows this pattern:

```
1. PREPARE — Choose the right delivery method
2. DELIVER — Provide content in accessible format
3. VERIFY — Confirm you can see/access it
4. CONFIRM — Wait for your acknowledgment
```

---

## DELIVERY METHODS

### METHOD 1: Direct Content Paste
**Use for:** Markdown, text, code, small documents

**Format:**
```
## FILE: [filename]

[content pasted directly]

---

**How to use:** Copy the content above into your preferred editor.
**Size:** [X] lines / [Y] KB
**Format:** Markdown
```

**Example:**
```markdown
## FILE: visual-specification-v3.md

# Visual Specification v3
...
[full content here]
...

---

**How to use:** Copy the content above.
**Size:** 312 lines / 10 KB
**Format:** Markdown
```

---

### METHOD 2: Browser Screenshots
**Use for:** HTML wireframes, visual designs, UI components

**Format:**
```
## VISUAL: [filename]

[Screenshot image embedded here]

---

**What you're seeing:** [description]
**How to verify:** Compare against specifications
**Next step:** Reply APPROVE / REVISE / REJECT
```

**Process:**
1. I render the HTML/component
2. I capture screenshot
3. I embed in response
4. You see exactly what I see

---

### METHOD 3: GitHub Repository
**Use for:** Large files, multiple files, codebases

**Format:**
```
## REPOSITORY: [repo-name]

**URL:** https://github.com/[username]/[repo]/tree/[branch]/[path]

**Files in this delivery:**
- file1.ext ([size])
- file2.ext ([size])

**How to access:**
1. Click URL above
2. Browse files in browser
3. Or clone: `git clone [url]`
4. Or download ZIP from GitHub

**Last commit:** [hash] — "[message]"
```

**Verification:**
- I confirm push succeeded
- I test the URL works
- You confirm you can access it

---

### METHOD 4: Summarized Reports
**Use for:** Multiple files, directories, complex structures

**Format:**
```
## SUMMARY: [topic]

Instead of individual files, here's what's been created:

| File | Location | Size | Description |
|------|----------|------|-------------|
| file1 | docs/ | 10KB | Design spec |
| file2 | src/ | 5KB | Component |

**GitHub URL:** [link to folder]
**Total files:** [N]
**Total size:** [N] KB

**Next step:** Review on GitHub or ask me to paste specific files.
```

---

## WHAT I WILL NEVER DO AGAIN

❌ **Never say:** "The file is at /root/.openclaw/..."

❌ **Never assume:** You can access my filesystem

❌ **Never provide:** Raw paths without context

❌ **Never forget:** To explain how to access content

❌ **Never skip:** Verification that you can see it

---

## VERIFICATION CHECKLIST

Before I say "done", I verify:

- [ ] Content is accessible without special permissions
- [ ] Viewing method is explained clearly
- [ ] Alternative access provided if primary fails
- [ ] Screenshots captured for visual items
- [ ] GitHub URL tested and confirmed working
- [ ] I explicitly ask: "Can you see this?"

---

## YOUR OPTIONS

### If You Can't Access Something

**Say:** "I can't access [item]"

**I will:**
1. Apologize
2. Immediately repost using different method
3. Verify the new method works
4. Document the failure for future avoidance

### If You Want Different Format

**Say:** "Show me [item] as [screenshot/paste/link]"

**I will:**
1. Reformat immediately
2. Deliver in requested format
3. Note preference for future deliveries

### If Something Is Missing

**Say:** "I don't see [specific thing]"

**I will:**
1. Check my delivery
2. Locate missing content
3. Repost with explanation

---

## EXAMPLES OF CORRECT DELIVERY

### Example 1: Documentation
```
Here's the file content:

---

# Title
Content here...

---

**File:** filename.md
**Size:** 5KB
**Copy the content between the --- lines above.**
```

### Example 2: Wireframe
```
Here's the wireframe screenshot:

[IMAGE]

**File:** 01-tenet-portal.html
**What to check:** Border radius (should be 0px), 4 tiles visible
**Your action:** Review and reply APPROVE/REVISE/REJECT
```

### Example 3: Repository Update
```
All files pushed to GitHub:

**URL:** https://github.com/notbleaux/eSports-EXE/tree/main/docs

**What's new:**
- 7 new files in docs/frameworks/
- 3 updated files in context/

**Verify:** Click URL, confirm files visible
**Let me know:** If any files missing or inaccessible
```

---

## TODAY'S COMMITMENT

**Starting now, every delivery follows this protocol.**

If I slip up and give you an inaccessible path:
1. Call me out immediately
2. I will apologize and fix it
3. I'll add the mistake to my prevention checklist

**Your access is my responsibility.**

---

Protocol Version: 1.0.0
Created: 2026-04-01
Status: ACTIVE — EFFECTIVE IMMEDIATELY
