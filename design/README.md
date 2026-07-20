# Pennywise — Personal Finance App Design

A complete **mobile-first iPhone design** for a personal finance tracking app. The
goal: help people understand where their money goes, organize every expense into
categories, control budgets, and build better habits — without making finance feel
complicated.

> Open [`design/index.html`](./index.html) in any browser to view all 13 screens as
> interactive iPhone mockups. It's a single self-contained file — no build step.

## What's inside

Every screen requested, rendered in an iPhone frame with safe-area spacing and a
floating 5-item bottom navigation:

| Flow | Screens |
|------|---------|
| **Welcome & Onboarding** | Splash, then one question per step — name & currency, income & main goal, spending categories (choose or create your own), monthly limit, subscriptions & manual-vs-bank input |
| **Everyday** | Home overview, Add-expense sheet, Transactions ledger, Transaction detail |
| **Categories & Budgets** | Categories list, Category detail (trend + top merchants), Budgets |
| **Insights, Goals & Profile** | Insights (touchable charts), Financial goals, Subscriptions, Profile & settings |

## Design language

Inspired by premium, athletic sports-app aesthetics, translated into a **light**
interface that feels calm and trustworthy.

- **Palette** — Warm Sand: warm-white/soft-beige backgrounds (`#FBF7F1`), strong ink
  black type (`#1B1712`), soft warm gray for secondary text, and a single vibrant
  **orange** accent (`#FF5A1F`) reserved for primary actions and live states. Green/red
  only for income vs. overspend.
- **Type** — SF Pro / Inter system stack. Large, bold headlines; **mono, tabular
  numerals** for every money value so digits stay aligned and scannable.
- **Form** — generously rounded cards (16–30px), subtle two-layer shadows, roomy
  spacing, simple outlined icons. No heavy gradients, no glass, no tiny text.

## UX principles

- One clear primary action per screen; never more than ~6–7 important elements visible.
- An expense is recordable in a few taps; most-used categories & payment methods surface
  first.
- Charts are made to be touched — drag across a date to reveal that period's total.
- Every element answers one of four questions:
  **How much do I have? Where did it go? Am I spending too much? What should I change?**

---

*Design concept — not affiliated with any real financial institution. Sample data is
illustrative.*
