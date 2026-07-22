# BookNotes — Premium Book Annotation & Reading Companion

A design reference and interactive prototype for **BookNotes**, a calm, premium
companion app for everything you learn while reading — notes, quotes, characters,
chapters, themes and ideas, organized the reader's own way.

BookNotes is **not** an eBook reader. It's a place to capture and revisit thoughts
about any book you read, in whatever structure fits you: by chapter, by page, by
quote, by character, or nothing at all. The app adapts to the reader instead of
forcing a workflow.

> Open [`index.html`](index.html) in any browser to explore the interactive prototype.
> On Apple devices the type renders as SF Pro. Use the **iPhone / iPad** toggle at
> the top to preview both form factors.

## What's in the prototype

A single self-contained `index.html` (no build step, no dependencies) presenting a
high-fidelity, tappable prototype in a device frame:

| Area | Highlights |
|------|-----------|
| **Home** | Continue reading, reading streak, weekly stats, recent notes, currently-reading shelf, recently-viewed characters, quick-add strip |
| **Library** | Grid / list toggle, collection filters (Reading · Finished · Favorites · Wishlist · Fiction), progress, favorites |
| **Book workspace** | Modular sections you can enable, rename, reorder or ignore — Overview, Notes, Characters, Quotes, Chapters, Themes, Timeline, Questions + custom sections |
| **Flexible editor** | Title, optional attributes (book · page · chapter · tag · character), rich content with checklists & block quotes, formatting toolbar, autosave indicator |
| **Character pages** | Description, relationships, appearances, quotes, development, custom properties |
| **Quotes** | Quote cards with source, reflection, favorite & share |
| **Search** | Live search across books, characters and notes with match highlighting, scopes and recent searches |
| **Profile / Stats** | Interactive reading-time chart (week/month/year), key metrics, preference toggles (sessions, AI assist, iCloud, haptics) |
| **Quick Capture** | Floating `+` opens a bottom sheet — Note · Quote · Character · Chapter note · Voice · Photo |

## Design language

Built to feel like a native SwiftUI iOS & iPadOS product — minimal, elegant,
distraction-free.

- **Palette** — Deep Indigo `#3F51F5` (primary actions & active states only),
  Warm White `#FAFAF8` canvas, Pure White cards, Near-Black `#161616` text,
  Medium Gray `#6E6E73` secondary, Soft Gold `#D8A94A` reserved for earned
  moments (streaks, favorites).
- **Type** — SF Pro Display / Text scale (Large Title → Caption), generous
  spacing, never more than ~6–7 primary elements per screen.
- **Navigation** — five-tab bottom bar (Home · Library · Notes · Search · Profile);
  everything reachable in 2–3 taps, no hamburger menus.
- **Motion** — expandable cards, slide-in transitions, a slide-up capture sheet
  with dimmed backdrop, subtle press states and (where supported) haptic feedback.
- **Empty states** — encouraging prompts instead of blank pages.

## Principles reflected in the design

- **Adaptive, not rigid** — every reader builds their own system; sections and
  fields are optional and customizable.
- **Flexible notes** — a note can be one line or a rich document with page,
  chapter, character, tags, voice, images and checklists — all optional.
- **Calm by design** — color guides attention; the gray ramp carries everything else.
- **Everything connected** — characters, chapters, quotes, pages and themes link
  to each other and surface where they're relevant.
- **Offline-first** — designed around local-first notes with cloud sync and
  version history; AI features are optional assists that never replace your notes.

## Notes

This is a front-end design prototype intended to communicate the product's look,
feel and information architecture ahead of a native build. Data is seeded for
illustration and interactions are simulated client-side.
