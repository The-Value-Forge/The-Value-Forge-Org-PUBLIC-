# TVF Art Assignment Step — paste into translator routine after Step One

**Version:** v1 — 14 Jun 2026
**Status:** LIVE — paste into the weekly translator routine (Claude.ai) as a new step,
immediately after the existing Step One (read ROUTINE-OUTPUTS).
**Dual-home:** this file lives at `docs/translation/ROUTINE-art-assignment-step.md` in the
repo AND should be copied to Drive: Projects/THE VALUE FORGE/Routines/.

---

## ART STEP — Assign cover images to each new article

⚠️ THIS STEP IS NOT COMPLETE UNTIL card_image IS WRITTEN INTO EVERY NEW ARTICLE'S
FRONTMATTER. Do not proceed to the next step without confirming this.

### What you are doing

For each new article you are about to write (signal, synthesis, monthly), you must assign
a cover image from the Art Pool on Drive. You are doing **content-level matching** — reading
what the article is actually about and picking the image whose description most closely fits.

### Where the Art Pool lives

Google Drive → Projects → THE VALUE FORGE → Art Pool

Six subfolders:
- `d01--acute-frailty/`
- `d02--clinical-psychology/`
- `d03--palliative-care/`
- `d04--therapies-ahps/`
- `d05--opat/`
- `cross--synthesis-multi-domain/`   ← use for syntheses and multi-domain signals

### Step by step

**A. For each new article you are writing this session:**

1. Identify the article's **primary domain** from its `domain:` frontmatter field.
   - Single domain → use that domain's subfolder (e.g. `d01` → `d01--acute-frailty/`).
   - Multiple domains → use `cross--synthesis-multi-domain/`.
   - Synthesis → always use `cross--synthesis-multi-domain/`.

2. List the image files in that subfolder. Each filename is a description:
   e.g. `d01--older-person-by-window-morning-light.webp`

3. Read the article's title and description. Extract the key **visual and thematic
   concepts** (what scene, setting, or subject would best illustrate this clinical finding?).

4. Score each image in the pool by how well its description matches those concepts.
   Pick the **highest-scoring image that has not already been used in a previous article
   this session** (check your session's used list below).

5. If no image scores > 0, pick the next unused image in alphabetical order from the
   domain subfolder. If the domain subfolder is empty, use `cross--synthesis-multi-domain/`.
   If that is also empty, leave `card_image:` blank — the GitHub Action will use the
   generative SVG fallback, and the sync script will assign from the pool next run.

**B. Write the assignment into the article frontmatter:**

Add this line to the article's YAML frontmatter, directly after `finding_status:`:
```yaml
card_image: "cards/<domain>/<filename>"
```

Example:
```yaml
card_image: "cards/d01/d01--older-person-by-window-morning-light.webp"
```

The path is always: `cards/` + the domain subfolder prefix + `/` + the exact filename.

**C. Track what you have used this session:**

Maintain a simple list as you work:
```
USED THIS SESSION:
- d01/d01--older-person-by-window-morning-light.webp  →  2026-06-19-frailty-signal-slug
- cross/cross--abstract-network-nodes-teal.webp       →  synthesis--2026-06-19-week-ending
```

Do not assign the same image to two articles in the same session. Across sessions, the
GitHub Action's `data/card_art.json` manifest tracks the full used-ledger and prevents
repeats; you only need to avoid intra-session duplicates.

### If the Art Pool is empty

If a subfolder has no images yet, skip the assignment for that article and note it in
your session log. Write:
```yaml
card_image: ""
```
The sync script will assign automatically when images are available.

### Quality check before proceeding

Before moving to the next step, confirm:
- [ ] Every new article has a `card_image:` line in its frontmatter (or an explicit
      blank with a note if the pool was empty).
- [ ] No two articles this session share the same image.
- [ ] The domain path prefix matches the article's primary domain.

---

*This step is part of the dual-homed routine set. The code-side implementation is in
`scripts/art_sync.py` (fallback/download) and `layouts/partials/card-art.html` (render).*
