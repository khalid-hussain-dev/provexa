# PROVEXA — Design System

> **Design baseline: v1.0**
>
> This document is the visual source of truth for PROVEXA.
> It exists specifically to prevent independently generated UI from drifting into generic AI/SaaS aesthetics.

---

## 1. Design direction

PROVEXA should feel like a **career intelligence instrument**, not an AI chatbot, generic dashboard, HR portal, or futuristic AI landing page.

The visual language should communicate:

- evidence
- assessment
- precision
- progression
- confidence
- professional credibility
- controlled intelligence

The interface should feel closer to a **high-end analytical workspace mixed with an editorial career tool** than a conventional SaaS dashboard.

### Core visual principle

> **Quiet confidence over visual hype.**

Do not decorate the interface simply to make it look "AI-powered."

---

# 2. Anti-generic rule

The following visual patterns are explicitly discouraged unless required by usability:

- generic electric-blue AI gradients
- cyan/purple neon gradients
- glowing glassmorphism
- excessive rounded cards
- floating blobs
- glowing neural-network illustrations
- robot/brain imagery
- excessive dark-mode "AI cockpit" styling
- gradient text used as decoration
- excessive use of violet as an AI indicator
- arbitrary purple/blue/pink accent combinations
- stock illustrations of people interacting with holographic screens

If a visual element could be copied into 500 AI startup landing pages without looking out of place, **do not use it**.

---

# 3. Color concept

PROVEXA's palette is built around **graphite, parchment, mineral green, and restrained vermilion**.

The intent is deliberately different from the standard "blue SaaS" vocabulary.

## 3.1 Core palette

| Token | Hex | Role |
|---|---|---|
| `ink-950` | `#171715` | Primary dark / strongest text |
| `ink-900` | `#22221F` | Dark surfaces |
| `ink-700` | `#4A4943` | Secondary text |
| `stone-500` | `#8A877D` | Muted text / metadata |
| `paper-50` | `#F7F5EF` | Main light background |
| `paper-100` | `#EEECE4` | Secondary surface |
| `paper-200` | `#DEDCD2` | Borders / separators |
| `mineral-700` | `#315C4A` | Primary brand accent |
| `mineral-600` | `#3F705B` | Interactive accent |
| `mineral-100` | `#DCE8E0` | Soft accent surface |
| `vermilion-600` | `#B64B36` | Attention / decisive action |
| `vermilion-100` | `#F2DDD7` | Soft warning surface |
| `ochre-600` | `#A4762C` | Caution / assessment |
| `ochre-100` | `#F0E5CD` | Soft caution surface |

### Why this palette?

**Graphite + parchment** creates an editorial, document-oriented foundation.

**Mineral green** represents progress, evidence, and readiness without falling into the conventional technology-blue vocabulary.

**Vermilion** is reserved for moments that require attention or a meaningful decision.

**Ochre** is used for caution and intermediate states.

The result should feel mature and intentional rather than "AI themed."

---

# 4. Color usage rules

### Primary action

Use `mineral-700`.

Examples:

- Analyze
- Continue
- Generate
- Start Interview
- Build Resume

### High-attention action

Use `vermilion-600` sparingly.

Examples:

- Important gap
- Failed requirement
- Destructive action
- Significant warning

Do **not** use vermilion merely as a decorative accent.

### Caution

Use `ochre-600`.

Examples:

- Partial match
- Needs improvement
- Unverified evidence

### Success/readiness

Use `mineral-700`.

Avoid introducing a separate generic "success green."

### Neutral information

Use graphite/stone rather than introducing another accent color.

---

# 5. Evidence visualization

Evidence is one of PROVEXA's defining concepts.

Visualizations should distinguish:

```text
CLAIMED
   ↓
SUPPORTED
   ↓
DEMONSTRATED
   ↓
STRONG
```

Do not rely solely on color.

Use:

- labels
- icons
- weight
- patterns
- progress indicators
- evidence counts

Example:

```text
Python
STRONG
██████████████████░░ 91
7 supporting evidence items
```

The evidence count should be visually meaningful.

---

# 6. Match score visualization

Avoid the generic glowing circular "AI score" whenever possible.

Prefer:

### Option A — Editorial meter

```text
ROLE MATCH

82 / 100

████████████████░░░░
```

### Option B — Segmented readiness bar

```text
████ ████ ████ ███░ ░░░
```

### Option C — Requirement matrix

```text
Requirement       Evidence       Match
Python            Strong         ✓
FastAPI           Strong         ✓
Docker            Partial        ~
Kubernetes        Missing        ×
```

The interface should make **why** the score exists more prominent than the score itself.

---

# 7. Typography

The typography should reinforce the editorial/documentary character.

### Primary UI font

Use a clean humanist or neo-grotesk sans-serif.

Recommended:

```text
Inter
```

or an equivalent system sans-serif if Inter is unavailable.

### Display / editorial headings

A restrained serif may be used selectively for major product storytelling or section headings.

Recommended direction:

```text
DM Serif Display
```

or a similar high-quality serif.

Do not use the serif everywhere.

### Monospace

Use a monospace font only for:

- technical evidence
- repository names
- code
- API/provider information
- technical metadata

---

# 8. Typography hierarchy

```text
Display       48–64px
H1            36–48px
H2            28–36px
H3            20–24px
Body          15–17px
Small         13–14px
Micro         11–12px
```

Use generous line-height for editorial sections.

Avoid oversized headings whose only purpose is to look impressive.

---

# 9. Layout philosophy

PROVEXA should feel **structured but not boxed-in**.

Prefer:

- strong alignment
- generous whitespace
- asymmetric editorial sections
- thin separators
- restrained cards
- clear information hierarchy
- dense data only where it helps decisions

Avoid:

```text
[ CARD ]
[ CARD ]
[ CARD ]
[ CARD ]
```

everywhere.

Not every section needs a card.

Use whitespace and separators to establish hierarchy.

---

# 10. Border radius

Use restrained geometry.

Recommended:

```text
Buttons:       8px
Inputs:        8px
Cards:         12px
Large panels:  16px
Pills:         full
```

Do not make every element excessively pill-shaped.

---

# 11. Shadows

Shadows should be subtle.

Prefer:

- low-opacity
- large blur
- minimal elevation

In many cases, a border is preferable to a shadow.

---

# 12. Buttons

Primary:

```text
Mineral background
Dark/white high-contrast text as appropriate
8px radius
Medium weight
```

Secondary:

```text
Transparent/paper surface
Graphite border
```

Tertiary:

```text
Text-only
```

Avoid gradient buttons.

Avoid glowing buttons.

---

# 13. Cards

Cards should communicate a meaningful boundary.

A card is justified when it represents:

- a job
- an analysis result
- a capability
- an interview stage
- a course module
- a resume
- evidence

Do not put every paragraph into a card.

---

# 14. AI interaction design

PROVEXA should not present AI as a magical black box.

Instead of:

> "✨ AI has analyzed your profile!"

Prefer:

> **Assessment complete**
>
> 14 capabilities identified  
> 11 supported by evidence  
> 3 require stronger proof

AI output should feel **auditable**.

Where appropriate, show:

```text
Finding
Why it matters
Evidence
Recommendation
```

---

# 15. Interview interface

The interview should feel like a professional assessment environment.

Avoid chatbot-style:

```text
🤖 AI Interviewer
Hey! Let's chat!
```

Prefer:

```text
PROVEXA ASSESSMENT

Backend Engineer
Round 2 of 6

Competency
System Design

Question
Design a service that...
```

The interface should create a sense of seriousness without becoming intimidating.

---

# 16. Course interface

The generated course should visually communicate progression.

Preferred pattern:

```text
READINESS PATH

01  Docker fundamentals        ✓
02  Container orchestration    62%
03  Kubernetes deployment      ○
04  Production observability   ○
```

The course should look like a **personal progression plan**, not a generic LMS.

---

# 17. Resume builder

The resume builder should feel closer to a document editor than a conventional SaaS form.

Use:

- paper-like resume preview
- strong typography
- controlled spacing
- live tailoring indicators
- evidence references
- version history

The job-specific tailoring should be visible but not visually noisy.

Example:

```text
TAILORED FOR
Backend Engineer — Example Corp

+ FastAPI emphasis
+ PostgreSQL evidence
+ API project highlighted
```

---

# 18. Dashboard

The dashboard's primary question should be:

> **"Where do I stand, and what should I do next?"**

Recommended information hierarchy:

```text
READINESS
82%

Target role
Backend Engineer

────────────────────

Strong evidence
11 capabilities

Gaps
3 capabilities

────────────────────

NEXT BEST ACTION
Complete Kubernetes module

────────────────────

Recommended opportunities
...
```

Do not turn the dashboard into a collection of unrelated metrics.

---

# 19. Icons and illustrations

Prefer:

- simple line icons
- geometric marks
- document/evidence metaphors
- understated diagrams

Avoid:

- robots
- brains
- glowing neural networks
- generic AI stars
- magic wand icons for every AI action

AI should be communicated through **behavior**, not cliché imagery.

---

# 20. Motion

Motion should explain state changes.

Good uses:

- analysis progress
- score transitions
- interview question progression
- course completion
- evidence state changes

Avoid:

- constant floating animations
- excessive page transitions
- animated gradients
- decorative particle effects

The product should feel fast and deliberate.

---

# 21. Responsive behavior

Desktop is the primary hackathon demonstration environment.

Nevertheless:

- mobile layouts must remain functional
- tables should collapse intelligently
- interview UI should work on narrow screens
- resume preview should remain usable
- no horizontal scrolling for core workflows

---

# 22. Accessibility

Do not encode meaning using color alone.

Every status must have at least two signals:

```text
color + label
color + icon
color + pattern
```

Maintain readable contrast.

Interactive elements must have clear focus states.

---

# 23. AI-generated UI implementation rule

Any AI coding agent generating UI for PROVEXA must:

1. Read this document first.
2. Reuse the defined tokens.
3. Avoid inventing new accent colors.
4. Avoid introducing gradients unless explicitly approved.
5. Avoid generic AI visual motifs.
6. Preserve the information hierarchy.
7. Prefer evidence and explanation over decoration.
8. Use existing components before creating visually inconsistent alternatives.

---

# 24. Brand relationship

## VANTERIX

Team identity:

> **See differently. Build intelligently. Go beyond.**

Its visual identity should not automatically dictate the application.

## PROVEXA

Product identity:

> **From potential to proof.**

PROVEXA should visually communicate:

> **Potential → Evidence → Assessment → Proof → Improvement → Readiness → Opportunity**

The product is the primary visual system during the hackathon demo.

---

# 25. Final design test

Before accepting a screen, ask:

### 1. Does this look like a generic AI SaaS dashboard?

If yes → redesign.

### 2. Does the color palette communicate PROVEXA rather than "AI"?

If no → redesign.

### 3. Is the user's evidence visible?

If not → consider whether it should be.

### 4. Does the interface explain *why* something happened?

If not → improve the information hierarchy.

### 5. Is decoration competing with decision-making?

If yes → remove it.

### 6. Would the interface still look credible if every mention of "AI" were removed?

If yes → **good.**

---

## Design north star

> **PROVEXA should look like a serious instrument for proving professional readiness — not another application trying to convince you that it uses AI.**
