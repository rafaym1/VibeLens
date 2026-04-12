# VibeLens Design System

## 1. Visual Theme & Atmosphere

VibeLens is a dense, data-rich analysis tool built on a dark zinc canvas. The design prioritizes information density and scannability over decoration. Every surface is a shade of zinc — from near-black (`zinc-950`) for the deepest background to cool gray (`zinc-800`) for elevated controls — creating a layered cockpit where data emerges from darkness through carefully calibrated luminance steps.

The color system is achromatic at its core, with semantic accent colors assigned by function rather than aesthetics. Cyan is the primary accent — navigation, session identifiers, and interactive highlights all share this cool blue tone. A supporting cast of violet, teal, amber, rose, and emerald each own a single semantic lane (sub-agents, skills, friction, errors, success). No color appears in two roles. This strict mapping means users learn the system once and can scan by color alone.

Typography is system-native — the app inherits the operating system's sans-serif stack (`-apple-system`, `Segoe UI`, `Roboto`) for UI text, and uses Geist Mono for all code and numeric data. There is no custom display typeface. Headlines are small (18-24px) because this is a tool, not a marketing page. The largest text in the entire app is the brand name "VibeLens" at 24px. Most content lives at 11-14px, optimized for dense data tables, session lists, and metric displays.

The overall impression is a mission-control interface: dark, focused, information-forward, with color used as signal rather than style.

**Key Characteristics:**
- Dark and light mode with system preference detection (3-way toggle: System / Light / Dark)
- CSS custom property token layer with semantic Tailwind classes (`bg-canvas`, `bg-panel`, `bg-control`, `text-primary`, etc.)
- Cyan as the singular primary accent, with five supporting semantic colors
- System sans-serif for UI, Geist Mono for code and numbers
- Dense, small-type layouts optimized for data analysis workflows
- Tailwind CSS utility classes as the styling primitive — no custom CSS framework
- Lucide React for all iconography
- No gradients on surfaces, no textures, no decorative elements

## 2. Color Palette & Roles

### Background Surfaces

| Token | Tailwind | Hex | Use |
|-------|----------|-----|-----|
| Canvas | `bg-zinc-950` | `#09090b` | App root, main content area, deepest background |
| Panel | `bg-zinc-900` | `#18181b` | Sidebar, modal cards, nav bar, right panels |
| Control | `bg-zinc-800` | `#27272a` | Inputs, buttons, dropdowns, code header bars |
| Subtle | `bg-zinc-800/50` | — | Hover states, stat boxes, confirm card backgrounds |
| Overlay | `bg-black/60` | — | Modal backdrop (paired with `backdrop-blur-sm`) |

### Text Hierarchy

| Role | Tailwind | Use |
|------|----------|-----|
| Primary | `text-zinc-100` | Headings, key values, modal titles |
| Secondary | `text-zinc-200` | Body text, paragraph content, stat row values |
| Muted | `text-zinc-400` | Labels, metadata, sidebar info, axis labels |
| Dimmed | `text-zinc-500` | Placeholders, timestamps, disabled states, icon defaults |
| Faint | `text-zinc-600` | Breadcrumb separators, background stats |

### Semantic Accent Colors

Each accent color owns exactly one semantic lane. Never repurpose a color for a different meaning.

| Color | Role | Primary Classes | Where Used |
|-------|------|----------------|------------|
| **Cyan** | Navigation, primary interactive | `text-cyan-400`, `bg-cyan-600`, `border-cyan-700/40` | Session IDs, selected states, main CTAs, links, chart fills, resize handles, brand logo |
| **Violet** | Sub-agents, uploads, continuations | `text-violet-400`, `bg-violet-600`, `border-violet-700/40` | Upload button, sub-agent badges, continuation chain pills, shared session banner |
| **Teal** | Skills, plan entries, personalization | `text-teal-300`, `bg-teal-600/20`, `border-teal-500/30` | Skills tab, plan/auto-prompt entries, skill-related banners |
| **Amber** | Friction, productivity, thinking | `text-amber-300`, `bg-amber-600/30`, `border-amber-400/40` | Friction/productivity tab, thinking blocks, warning banners, example badges |
| **Rose** | Errors, destructive actions, donate | `text-rose-300`, `bg-rose-600`, `border-rose-800/50` | Donate button, error states, delete confirmations, debugging phase |
| **Emerald** | Success, completion, privacy | `text-emerald-400`, `bg-emerald-500/10`, `border-emerald-700/30` | Upload success, copy confirmation, privacy protection stats, connected status dots |
| **Indigo** | Conversation tab, exploration phase | `text-indigo-200`, `bg-indigo-600/30`, `border-indigo-400/40` | Conversation view toggle, exploration phase border, mixed phase |
| **Blue** | File read operations, exploration | `text-blue-400`, `bg-blue-500/20` | File read tool category, exploration phase styling |
| **Sky** | Search operations, low-severity | `text-sky-300`, `bg-sky-500/20` | Search tool category, severity level 2 badges |
| **Orange** | Web operations, high-severity | `text-orange-300`, `bg-orange-500/20` | Web tool category, severity level 4 badges |

### Border Hierarchy

| Tailwind | Use |
|----------|-----|
| `border-zinc-800` | Primary dividers: sidebar borders, section separators, modal header/footer |
| `border-zinc-700` | Card borders, input borders, modal outer border |
| `border-zinc-700/60` | Softer card borders (dashboard stat cards, chart panels) |
| `border-zinc-600` | Hover-elevated borders, blockquote accents |

### Phase Colors

Used for left-border accents on conversation steps to indicate development phases:

| Phase | Border | Label | Dot | Background |
|-------|--------|-------|-----|------------|
| Exploration | `border-l-blue-400` | `text-blue-400` | `bg-blue-400` | `bg-blue-500/[0.03]` |
| Implementation | `border-l-emerald-400` | `text-emerald-400` | `bg-emerald-400` | `bg-emerald-500/[0.03]` |
| Debugging | `border-l-red-400` | `text-red-400` | `bg-red-400` | `bg-red-500/[0.03]` |
| Verification | `border-l-amber-400` | `text-amber-400` | `bg-amber-400` | `bg-amber-500/[0.03]` |
| Planning | `border-l-violet-400` | `text-violet-400` | `bg-violet-400` | `bg-violet-500/[0.03]` |
| Mixed | `border-l-indigo-400` | `text-indigo-400` | `bg-indigo-400` | `bg-indigo-500/[0.03]` |

### Tool Category Colors

Used for tool call badges and distribution charts:

| Category | Background | Ring | Text |
|----------|-----------|------|------|
| File Read | `bg-blue-500/20` | `ring-blue-400/60` | `text-blue-300` |
| File Write | `bg-emerald-500/20` | `ring-emerald-400/60` | `text-emerald-300` |
| Shell | `bg-amber-500/20` | `ring-amber-400/60` | `text-amber-300` |
| Search | `bg-sky-500/20` | `ring-sky-400/60` | `text-sky-300` |
| Web | `bg-orange-500/20` | `ring-orange-400/60` | `text-orange-300` |
| Agent | `bg-violet-500/20` | `ring-violet-400/60` | `text-violet-300` |
| Task | `bg-rose-500/20` | `ring-rose-400/60` | `text-rose-300` |
| Other | `bg-zinc-500/20` | `ring-zinc-400/60` | `text-zinc-400` |

### Severity Scale (Friction Analysis)

| Level | Background | Text | Border |
|-------|-----------|------|--------|
| 1 (Low) | `bg-zinc-700/50` | `text-zinc-300` | `border-zinc-600/40` |
| 2 | `bg-sky-900/40` | `text-sky-300` | `border-sky-700/30` |
| 3 (Medium) | `bg-yellow-900/40` | `text-yellow-300` | `border-yellow-700/30` |
| 4 | `bg-orange-900/50` | `text-orange-200` | `border-orange-600/40` |
| 5 (High) | `bg-rose-900/50` | `text-rose-200` | `border-rose-600/40` |

## 3. Typography Rules

### Font Families

| Role | Stack | Use |
|------|-------|-----|
| UI / Body | `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif` | All interface text — labels, headings, body, buttons |
| Code / Numbers | `'Geist Mono', 'SF Mono', 'Fira Code', 'Fira Mono', 'Roboto Mono', monospace` | Code blocks, token counts, costs, session IDs, stat values |

Geist Mono is loaded via Google Fonts at weights 400, 500, and 600.

### Type Scale

| Role | Size | Weight | Extra | Use |
|------|------|--------|-------|-----|
| Brand | `text-2xl` (24px) | `font-bold` | `text-cyan-400` | "VibeLens" in sidebar header |
| Page Title | `text-xl` (20px) | `font-semibold` | — | Dashboard heading |
| Section Title | `text-lg` (18px) | `font-medium` | — | Session title in header |
| Chart Heading | `text-base` (16px) | `font-medium` | — | Chart section headings within panels |
| Body | `text-sm` (14px) | normal | — | Dialog messages, session list items, body text |
| Label | `text-xs` (12px) | `font-medium` / `font-semibold` | — | Buttons, stat labels, pill text, secondary info |
| Description | `text-[11px]` | normal | — | Card descriptions, tooltip text, badge text, session IDs |
| Section Header | `text-[10px]` | `font-medium` | `uppercase tracking-wider` | Dashboard section labels, settings group headers |
| Micro | `text-[9px]` | `font-medium` | — | Example badges, small overflow counts |

### Monospace Patterns

| Pattern | Classes | Use |
|---------|---------|-----|
| Stat Value | `font-mono tabular-nums` | Token counts, costs, session counts |
| Code Block | `font-mono text-xs` | Command displays, code content |
| Session ID | `font-mono text-[11px]` | Truncated UUIDs in session headers |
| Stat Card Value | `text-3xl font-bold tabular-nums tracking-tight` | Dashboard big numbers |

### Typography Principles

- **No display type.** This is a tool, not a landing page. The largest text is 24px (brand name). Most UI text is 11-14px.
- **System fonts for speed.** No custom web fonts for UI text. The OS provides the best reading experience at small sizes.
- **Geist Mono for data.** All numeric values, costs, token counts, and code use the monospace stack. `tabular-nums` ensures columns align.
- **Uppercase sparingly.** Reserved for section header labels (`text-[10px] font-medium uppercase tracking-wider text-zinc-400`). Never on body text or headings.
- **Weight range is narrow.** Normal (400), medium (500), semibold (600), and bold (700). No light weights. Bold is rare — used only for stat card values and the brand name.

## 4. Component Stylings

### Buttons

**Primary (Accent-Colored)**
Each feature area uses its own accent color, but all follow the same shape:
```
inline-flex items-center gap-2 px-4 py-2
bg-{accent}-600 hover:bg-{accent}-500 text-white
text-sm font-medium rounded-lg transition
disabled:opacity-40 disabled:cursor-not-allowed
```
- Cyan: main actions (confirm, connect)
- Violet: upload actions
- Teal: skill actions
- Amber: cost estimate actions
- Rose: donate, destructive actions

**Secondary / Ghost**
```
px-3 py-1.5 text-xs
text-zinc-400 hover:text-zinc-200
border border-zinc-700 hover:border-zinc-600
rounded transition
```

**Icon-Only**
```
p-1.5 text-zinc-500 hover:text-zinc-300
hover:bg-zinc-800 rounded transition
```

**Segmented Toggle (shared constant from `styles.ts`)**
```
Container: flex gap-0.5 bg-zinc-800 rounded p-0.5
Button:    flex-1 flex items-center justify-center gap-1.5 text-xs py-1.5 rounded transition
Active:    bg-zinc-700 text-zinc-100
Inactive:  text-zinc-500 hover:text-zinc-300
```

**View Mode Toggle (header tabs)**
```
Active:   min-w-[100px] text-center px-4 py-1.5 text-sm font-semibold rounded-md
          bg-{accent}-600/30 text-{accent}-200 border border-{accent}-400/40
          shadow-sm shadow-{accent}-900/40 transition
Inactive: min-w-[100px] text-center px-4 py-1.5 text-sm font-semibold rounded-md
          text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition
```

**Pill Selector**
```
Active:   px-3 py-1 text-xs rounded-full bg-violet-600 text-white
Inactive: px-3 py-1 text-xs rounded-full bg-zinc-800 text-zinc-400
          border border-zinc-700 hover:border-zinc-500 hover:text-zinc-200
```

### Cards & Containers

**Dashboard Stat Card**
```
rounded-xl border border-zinc-700/60 bg-zinc-900/80
px-5 py-5 hover:border-zinc-500/60 transition-colors
```
- Label: `text-xs font-semibold text-zinc-200 uppercase tracking-wider`
- Value: `text-3xl font-bold text-cyan-400 tabular-nums tracking-tight`
- Divider: `border-t border-zinc-700/40 pt-2.5`

**Dashboard Section Card**
```
rounded-xl border border-zinc-700/60 bg-zinc-900/80 p-5
```

**Info Card (dialogs, confirmations)**
```
bg-zinc-800/50 border border-zinc-700 rounded-lg p-4 space-y-2.5
```

**Success Card**
```
rounded-lg border border-emerald-700/30 bg-emerald-950/10 px-4 py-3
```

### Inputs & Forms

**Text Input**
```
w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg
text-sm text-zinc-200 placeholder-zinc-500
focus:outline-none focus:border-cyan-600
```
Focus border color changes per panel: `focus:border-amber-600` (friction), `focus:border-teal-600` (skills).

**Search Input (with icon)**
```
w-full bg-zinc-800 text-zinc-200 text-sm rounded
pl-7 pr-8 py-1.5 border border-zinc-700
focus:outline-none focus:border-cyan-600 placeholder:text-zinc-500
```
Search icon: absolute positioned, `left-2 top-1/2 -translate-y-1/2`, `w-3.5 h-3.5 text-zinc-500`.

**Checkbox**
```
accent-cyan-500 w-4 h-4 rounded border-zinc-600 bg-zinc-800
```

**Form Label**
```
block text-xs font-medium text-zinc-300 mb-1
```

**Section Header**
```
text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3
```

### Badges & Pills

**MetaPill (session header)**
```
inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px]
bg-zinc-800 border border-zinc-700/50
```
Session ID variant: `bg-cyan-950/50 border-cyan-800/30 text-cyan-300 font-mono`

**Continuation Chain Pill**
```
inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
bg-violet-900/30 border border-violet-700/40 text-xs text-violet-300
hover:bg-violet-800/40 hover:border-violet-600/50 transition-colors
```

**Tag Badge**
```
text-xs px-1.5 py-0.5 rounded bg-zinc-700/60 text-zinc-300
```

**Tool Badge (monospace)**
```
text-[10px] px-1.5 py-0.5 rounded bg-cyan-900/20 text-cyan-400/70 font-mono
```

**Example Badge**
```
px-1 py-0.5 text-[9px] font-medium
bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded
```

**Status Dot**
```
w-1.5 h-1.5 rounded-full bg-emerald-400
```

### Custom Dropdown

VibeLens uses custom dropdown components instead of native `<select>` elements. Native selects break the dark theme.

```
Trigger:  w-full flex items-center justify-between px-3 py-2
          bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200
          focus:outline-none focus:border-cyan-600 transition
Chevron:  w-3.5 h-3.5 text-zinc-500 transition (rotate-180 when open)
Menu:     absolute z-20 mt-1 w-full max-h-64 overflow-y-auto
          bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl
Option:   w-full text-left px-3 py-2 text-sm hover:bg-zinc-700 transition
Selected: text-cyan-400 (or accent color) with Check icon
```

### Modals

Built from four composable parts (`modal.tsx`):

```
Overlay:  fixed inset-0 z-50, backdrop bg-black/60 backdrop-blur-sm
Card:     bg-zinc-900 border border-zinc-700 rounded-lg shadow-2xl
          max-h-[85vh] w-full {maxWidth} mx-4 flex flex-col
Header:   px-5 py-4 border-b border-zinc-800
          Title: text-sm font-semibold text-zinc-100
          Close: text-zinc-500 hover:text-zinc-300 transition, X icon w-4 h-4
Body:     flex-1 min-h-0 overflow-y-auto px-5 py-4 space-y-4
Footer:   flex justify-end gap-2 px-5 py-3 border-t border-zinc-800
```

### Tooltip

Portal-rendered, instant-show, auto-flips vertically:
```
z-[9999] px-3 py-2 text-xs leading-relaxed text-zinc-100
bg-zinc-800/95 border border-zinc-600 rounded-lg shadow-2xl
max-w-[300px] w-max text-center pointer-events-none break-words
```

### Banners

All banners follow the same structure with accent-specific colors:

| Type | Background | Border | Icon Color | Text Color |
|------|-----------|--------|------------|------------|
| Info (Cyan) | `bg-cyan-900/20` | `border-cyan-700/30` | `text-cyan-400` | `text-cyan-300/90` |
| Warning (Amber) | `bg-amber-900/20` | `border-amber-700/30` | `text-amber-400` | `text-amber-300/90` |
| Error (Rose) | `bg-rose-900/20` | `border-rose-800/50` | `text-rose-400` | `text-rose-300` |
| Success (Emerald) | `bg-emerald-950/10` | `border-emerald-700/30` | `text-emerald-400` | `text-emerald-400` |

Structure: `px-3 py-2 rounded-lg {bg} border {border}`, icon `w-3.5 h-3.5 shrink-0 mt-0.5`, text `text-xs`.

### Bar Charts

```
Track: flex-1 h-5 bg-zinc-800/60 rounded-md overflow-hidden
Fill:  h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-md transition-all
Label: w-32 truncate text-zinc-300 group-hover:text-zinc-100
Value: w-10 text-right text-zinc-300 tabular-nums font-medium
```

Progress bar (thin): `h-1.5 bg-zinc-800/60 rounded-full` with fill `from-cyan-600 to-cyan-400 rounded-full`.

### CollapsiblePill

```
Outer:   rounded-lg border {colorClass} overflow-hidden
Toggle:  flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-white/5 transition-colors
Chevron: ChevronDown/Right w-3 h-3
Label:   font-medium
Content: border-t border-inherit
```

### Loading States

**Full-area spinner:** Three concentric animated rings with pulsing center dot. Colors: cyan, amber, teal. Label: `text-sm font-medium text-zinc-200`.

**Inline spinner:** `<Loader2 className="w-4 h-4 animate-spin text-zinc-500" />`

**Success state:** `w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/20` with `CheckCircle2 w-7 h-7 text-emerald-400`.

**Error state:** `bg-rose-900/20 border border-rose-800 rounded-lg p-6` with title `text-sm font-semibold text-rose-300`.

### Empty / Welcome State

```
flex items-center justify-center h-full
text-center
Icon:     text-5xl mb-4 opacity-50
Title:    text-lg font-medium text-zinc-300 mb-1
Subtitle: text-sm text-zinc-500 mb-6
```

## 5. Layout Principles

### App Shell

The app is a fixed-viewport three-column layout:

```
Root:    flex h-full overflow-hidden bg-zinc-950 text-zinc-100
Left:    Sidebar — resizable, 240-600px, default 280px
         bg-zinc-900, border-r border-zinc-800
Center:  Main content — flex-1 min-w-0 bg-zinc-950
Right:   Optional panel — 180-400px, default 252px
         border-l border-zinc-800 bg-zinc-900/50
```

### Sidebar

- Header: `h-[75px] px-4 border-b border-zinc-800 sticky top-0`
- Footer: `border-t border-zinc-800 px-3 py-2 text-xs text-zinc-400`
- Resize handle: `w-1 cursor-col-resize hover:bg-cyan-500/40 active:bg-cyan-500/60`

### Dashboard Grid

```
Container: max-w-[1400px] mx-auto p-6 space-y-5
Stat row:  grid grid-cols-5 gap-4
Content:   grid grid-cols-2 gap-4
```

### Session View

```
Header:  px-4 py-2
Content: max-w-5xl mx-auto px-4 py-6 space-y-3
User messages: max-w-[85%]
```

### Top Nav Bar

```
flex items-center justify-between px-4 py-2
border-b-2 border-zinc-700/60 bg-zinc-900 shadow-sm shadow-black/30
```

### Spacing Conventions

| Context | Padding |
|---------|---------|
| Modal header/body | `px-5 py-4` |
| Modal footer | `px-5 py-3` |
| Stat cards | `px-5 py-5` |
| Dashboard panels | `p-5` |
| Small inputs | `px-2.5 py-1.5` |
| Standard inputs | `px-3 py-2` |
| Small buttons | `px-3 py-1.5` |
| Primary buttons | `px-4 py-2` |
| Banners | `px-3 py-2` |

### Shared Width Constants

```
SIDEBAR_DEFAULT_WIDTH = 252
SIDEBAR_MIN_WIDTH     = 180
SIDEBAR_MAX_WIDTH     = 400
```

All right-side panels (prompt nav, friction history, skills history) must use these shared values. Never hardcode panel widths locally.

### Whitespace Philosophy

- **Density over breath.** VibeLens is an analysis tool. Screen real estate is for data, not decoration. Padding is functional (readability, click targets), never atmospheric.
- **Sections divide by borders, not space.** Horizontal dividers (`border-b border-zinc-800`) separate sections. No large empty gaps between content areas.
- **Cards contain, not float.** Cards sit flush in grids with `gap-4`, not surrounded by generous margins. The dark background IS the negative space.

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat (Level 0) | No shadow, `bg-zinc-950` | App canvas, main content area |
| Surface (Level 1) | `bg-zinc-900`, `border border-zinc-800` | Sidebar, nav bar, right panels |
| Card (Level 2) | `bg-zinc-900/80`, `border border-zinc-700/60` | Dashboard cards, chart panels, stat cards |
| Control (Level 3) | `bg-zinc-800`, `border border-zinc-700` | Inputs, dropdown triggers, code blocks |
| Elevated (Level 4) | `bg-zinc-800`, `border border-zinc-700`, `shadow-xl` | Dropdown menus |
| Modal (Level 5) | `bg-zinc-900`, `border border-zinc-700`, `shadow-2xl` | Modals, dialogs |
| Tooltip (Level 6) | `bg-zinc-800/95`, `border border-zinc-600`, `shadow-2xl`, `z-[9999]` | Tooltip popups |

**Shadow Philosophy:** Shadows are rare and minimal. The dark canvas makes traditional drop shadows nearly invisible, so elevation is communicated primarily through background luminance steps (`zinc-950` -> `zinc-900` -> `zinc-800`) and border visibility. The only significant shadows appear on modals (`shadow-2xl`), dropdown menus (`shadow-xl`), and the nav bar (`shadow-sm shadow-black/30`). Tooltips use `shadow-2xl` because they must visually float above all content.

### Modal Backdrop

```
bg-black/60 backdrop-blur-sm
```

The backdrop dims the entire viewport and applies a subtle blur, creating focus isolation for the modal card.

### Border Radius Scale

| Size | Tailwind | Use |
|------|----------|-----|
| Micro | `rounded` (4px) | Small controls, inputs, toggle buttons |
| Standard | `rounded-md` (6px) | Buttons, dropdown items |
| Comfortable | `rounded-lg` (8px) | Cards, modals, banners, code blocks, most containers |
| Large | `rounded-xl` (12px) | Dashboard stat cards, chart panels |
| Full | `rounded-full` | Pills, progress bars, status dots, circular buttons |

## 7. Do's and Don'ts

### Do

- Use the zinc surface hierarchy consistently: `zinc-950` (canvas) > `zinc-900` (panels) > `zinc-800` (controls)
- Assign each accent color to exactly one semantic role (cyan = navigation, violet = sub-agents, etc.)
- Use `font-mono tabular-nums` for all numeric data — costs, token counts, session counts, percentages
- Match focus border color to the panel's accent: `focus:border-cyan-600` in main views, `focus:border-amber-600` in friction, `focus:border-teal-600` in skills
- Use the shared `Modal` / `ModalHeader` / `ModalBody` / `ModalFooter` from `components/modal.tsx` for all dialogs
- Use the shared `Tooltip` from `components/tooltip.tsx` — it renders via portal, shows instantly, and auto-flips
- Use custom dropdown components instead of native `<select>` elements (native selects break the dark theme)
- Use `text-zinc-100` for primary text — not pure white, which is too harsh on dark backgrounds
- Apply `transition` or `transition-colors` on all interactive elements for smooth state changes
- Use Lucide React for all icons, sized with `w-{n} h-{n}` classes
- Keep button text at `text-xs` (12px) for standard buttons, `text-sm` (14px) for primary CTAs
- Use `uppercase tracking-wider` only on section header labels at `text-[10px]` or `text-xs`

### Don't

- Don't use pure white (`#ffffff`) as a background or primary text color — use `text-zinc-100` or lower
- Don't use native `<select>`, `<input type="checkbox">` without styling, or browser-default form controls — they break the dark theme
- Don't use native `title` attributes for tooltips — they have delayed display and unstyled appearance; use the shared `Tooltip` component
- Don't hand-roll modal overlay markup — use the shared `Modal` component which handles backdrop, focus trap, and z-indexing
- Don't introduce warm accent colors (yellow, orange, red) for non-error/non-warning UI elements
- Don't use gradients on surfaces or backgrounds — backgrounds are always solid zinc values or semi-transparent
- Don't hardcode sidebar or panel widths — use `SIDEBAR_DEFAULT_WIDTH`, `SIDEBAR_MIN_WIDTH`, `SIDEBAR_MAX_WIDTH` from `styles.ts`
- Don't use `text-white` for button text on colored backgrounds — use `text-white` only, never `text-zinc-50` (the distinction matters in opacity compositing)
- Don't use `font-bold` outside of stat card values and the brand name — `font-semibold` is the maximum for headings, `font-medium` for labels
- Don't add decorative elements, illustrations, or ornamental spacing — the interface is utilitarian
- Don't use `shadow-md` or `shadow-lg` on cards — cards get elevation from border and background color, not shadows

## 8. Responsive Behavior

VibeLens is designed as a **desktop-first dense application**. The UI assumes a wide viewport (1280px+) and does not include mobile layouts.

### Current Breakpoints

| Breakpoint | Use |
|-----------|-----|
| `xl` (1280px) | Right-side prompt nav panel appears (`hidden xl:flex`) |

No other responsive breakpoints are used. Dashboard grids (`grid-cols-5`, `grid-cols-2`) and session view layouts are fixed.

### Theme System

VibeLens supports dark and light mode via a CSS custom property token layer. Colors are defined as CSS variables in `:root` (light) and `.dark` (dark), referenced through Tailwind's `theme.extend.colors`.

**How it works:**
- `frontend/src/index.css` defines ~60 CSS variables in `:root` (light defaults) and `.dark` (dark overrides)
- `frontend/tailwind.config.js` maps semantic names to CSS variables (e.g., `canvas` -> `var(--color-bg-canvas)`)
- Components use semantic classes like `bg-canvas`, `text-primary`, `border-default` instead of hardcoded zinc values
- `settings-context.tsx` manages the 3-way toggle (System / Light / Dark) with localStorage persistence and `prefers-color-scheme` media query detection

**Adding a new theme color:**
1. Add the CSS variable to both `:root` and `.dark` in `index.css`
2. Add the Tailwind mapping in `tailwind.config.js` under `theme.extend.colors`
3. Use the new semantic class in components (e.g., `bg-my-token`)

### Scrollbar Styling

Custom WebKit scrollbar:
```css
width/height: 6px
thumb: rgba(63,63,70,0.5)  /* zinc-700/50 */
thumb hover: rgba(82,82,91,0.7)
border-radius: 3px
```

## 9. Agent Prompt Guide

### Quick Color Reference

```
App background:    bg-zinc-950
Panel background:  bg-zinc-900
Control surface:   bg-zinc-800
Primary text:      text-zinc-100
Body text:         text-zinc-200
Muted text:        text-zinc-400
Dimmed text:       text-zinc-500
Primary accent:    cyan-400 / cyan-600
Primary border:    border-zinc-800
Card border:       border-zinc-700/60
Input border:      border-zinc-700
Focus ring:        focus:border-cyan-600
Modal backdrop:    bg-black/60 backdrop-blur-sm
Modal shadow:      shadow-2xl
```

### Example Component Prompts

- **Stat card:** "Create a dashboard stat card: `rounded-xl border border-zinc-700/60 bg-zinc-900/80 px-5 py-5`. Label at `text-xs font-semibold text-zinc-200 uppercase tracking-wider`. Value at `text-3xl font-bold text-cyan-400 tabular-nums tracking-tight`. Rows below `border-t border-zinc-700/40` with label `text-zinc-400` and value `text-zinc-200 tabular-nums font-medium`."

- **Button pair:** "Primary button: `px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium rounded-lg transition`. Cancel button: `px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 border border-zinc-700 hover:border-zinc-600 rounded transition`."

- **Modal:** "Full modal: backdrop `fixed inset-0 z-50 bg-black/60 backdrop-blur-sm`. Card `bg-zinc-900 border border-zinc-700 rounded-lg shadow-2xl max-w-lg mx-4 max-h-[85vh]`. Header `px-5 py-4 border-b border-zinc-800` with title `text-sm font-semibold text-zinc-100`. Body `px-5 py-4 space-y-4`. Footer `px-5 py-3 border-t border-zinc-800 flex justify-end gap-2`."

- **Banner:** "Info banner: `px-3 py-2 rounded-lg bg-cyan-900/20 border border-cyan-700/30`. Icon `Info w-3.5 h-3.5 text-cyan-400`. Text `text-xs text-cyan-300/90`."

- **Data bar:** "Horizontal bar chart row: `flex items-center gap-2.5 text-[13px] hover:bg-zinc-800/60 px-2.5 py-1.5 rounded-md transition`. Label `w-32 truncate text-zinc-300`. Track `flex-1 h-5 bg-zinc-800/60 rounded-md`. Fill `bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-md`. Value `w-10 text-right text-zinc-300 tabular-nums font-medium`."

- **Dropdown:** "Custom dropdown: trigger `px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:border-cyan-600`. Menu `absolute z-20 mt-1 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl max-h-64 overflow-y-auto`. Option `px-3 py-2 text-sm hover:bg-zinc-700 transition`. Selected option `text-cyan-400` with check icon."

### Iteration Guide

1. Surface hierarchy is the foundation: every element must sit on the correct zinc level (`950` > `900` > `800`)
2. Accent color is cyan for all primary interactions; use the feature-specific accent only within that feature's panel
3. All numbers and costs use `font-mono tabular-nums` — never render numeric data in the proportional font
4. Borders are the primary depth indicator on dark surfaces, not shadows — use `border-zinc-700/60` for cards, `border-zinc-800` for dividers
5. Interactive elements get `transition` or `transition-colors` — no element should change state without an animation
6. Icons from Lucide React, sized `w-3.5 h-3.5` (small) to `w-4 h-4` (standard), colored to match their text context
7. Form inputs match their panel's accent on focus: cyan in main views, amber in friction, teal in skills

### Chart Styling Reference

```
Line stroke:     rgb(34,211,238)           /* cyan-400 */
Area gradient:   rgba(34,211,238,0.3) top → rgba(34,211,238,0.02) bottom
Grid lines:      rgba(255,255,255,0.06)
Axis baseline:   rgba(255,255,255,0.08)
Axis text:       #a1a1aa                    /* zinc-400 */
Data points:     cyan filled circles, 3px default, 5px active
Crosshair:       rgba(34,211,238,0.4) dashed
Bar fill:        gradient from-cyan-600 to-cyan-400
Bar track:       bg-zinc-800/60 rounded-md
```

Heatmap (5-level cyan scale):
```
Level 0: rgba(34,211,238,0.06)
Level 1: rgba(34,211,238,0.25)
Level 2: rgba(34,211,238,0.45)
Level 3: rgba(34,211,238,0.65)
Level 4: rgba(34,211,238,0.85)
```

Model distribution colors: `blue-500`, `amber-400`, `rose-500`, `emerald-500`, `violet-500`, `orange-500`, `cyan-400`, `fuchsia-500`.

Tool distribution colors: `cyan-500`, `teal-400`, `sky-500`, `indigo-400`, `emerald-500`, `amber-400`, `violet-500`, `rose-400`, `orange-400`, `lime-400`, `pink-400`, `blue-400`. Overflow: `zinc-600`.
