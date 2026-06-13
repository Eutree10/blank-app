# Questline — Garmin Connect IQ Watch App

Questline is a gamified mission system you build yourself. You write your own
**daily**, **weekly** and **monthly** quests from your phone, each one counts
down "Fortnite-style" to its deadline, and completing them earns XP. It is a
100% on-device app — no GPS, sensors, network or FIT recording — so it needs no
permissions and is light on battery.

- **Daily** quests = 100 XP · 24h window · resets at local midnight
- **Weekly** quests = 300 XP · resets **Monday 00:00 local**
- **Monthly** quests = 500 XP · resets on the **1st at 00:00 local**

Points and time windows are **fixed per level** (never per quest).

> The sample quest texts that ship in the default settings ("Sample daily
> quest 1", …) are neutral placeholders only. Real quests are authored by the
> user in the Garmin Connect phone app.

## Screens

1. **Hub** — gold logo, two stat cards (`TOTAL XP` in lime, `COMPLETED` in
   green/blue) and three level rows with `X/Y` counters and progress bars.
2. **Level list** — countdown header, a scrolling list of quest cards (blue =
   pending, green = done), a `COMPLETED` section, side arrows to switch level.
3. **Quest detail** — title, countdown, the card, and a pill button:
   green **COMPLETE** or red **RESET**, with a lime `+XP` flash on completion.

## Navigation (buttons *and* touch, one codebase)

Built entirely on `WatchUi.BehaviorDelegate` semantic callbacks, so Garmin maps
both physical buttons and touch gestures to the same behaviors:

| Behavior | Physical button | Touch |
|---|---|---|
| `onSelect` | START/ENTER | tap |
| `onBack` | BACK | back gesture |
| `onNextPage` / `onPreviousPage` | DOWN / UP | vertical swipe (scroll list) |
| `onMenu` | MENU | long press → level switcher |
| switch level | MENU → pick level | swipe left / right |

## Project layout

```
manifest.xml            App metadata, device list, (no) permissions
monkey.jungle           Build config (single runtime-adaptive resource set)
source/
  QuestlineApp.mc       Entry point, owns QuestService + per-minute timer
  QuestService.mc       Engine: resets, model build, complete/reset, stats
  models/               Quest, Levels (fixed points/windows/slots)
  data/                 Config (reads Properties) · Store (Application.Storage)
  util/                 Periods (date math) · Format (countdown / XP)
  ui/                   Theme, Fonts, Layout, TextUtil, Components (drawing)
  views/                Hub / QuestList / QuestDetail / LevelMenu + delegates
resources/
  strings/ drawables/ settings/ properties/ fonts/
scripts/gen_assets.py   Regenerates the PNG logo/icon from the brand geometry
```

**Data model.** A `Quest` has `id/slot`, `title`, `category`, `level`, derived
`points`, `completed`, `deadline` and `completedAt`. Global state (period ids,
lifetime XP, completed count, per-level streaks) lives in `Application.Storage`
via `Store.mc`; configuration is read separately in `Config.mc`. The two layers
never mix.

## Configuring quests (phone)

Quests are authored in **Garmin Connect → the app → Settings**. Connect IQ
settings only support fixed fields, so each level has a **fixed number of
slots** (≥ the required minimums): **6 daily / 8 weekly / 12 monthly**. Per slot
there is a toggle (enabled), a text field (the quest), and a category dropdown
(Physical / Task / Mental / Habit / Other). Empty-titled or disabled slots are
simply not shown. The default active set is **3 / 5 / 10** with neutral
placeholder text.

## Run in the simulator (VS Code)

1. Install the [Connect IQ SDK](https://developer.garmin.com/connect-iq/sdk/)
   and the **Monkey C** VS Code extension; run **Connect IQ: Verify Installation**.
2. Open this folder. Build & run with **Connect IQ: Run App** (or `Ctrl/Cmd+F5`)
   and pick a device.
3. Edit phone settings in the simulator via
   **File → Edit Persistent Storage / Settings** (the `settings.xml` UI).
4. Test resets without waiting: in the simulator use **Settings → Time** to jump
   the clock past midnight / Monday / the 1st, then relaunch — the affected
   level resets and a 100%-completed period bumps that level's streak.

CLI build/run alternative:

```bash
monkeyc -d venu3 -f monkey.jungle -o bin/Questline.prg -y developer_key.der
connectiq            # start the simulator
monkeydo bin/Questline.prg venu3
```

## Test on a real device

1. Generate a developer key once (or use **Connect IQ: Generate a Developer
   Key** in VS Code).
2. Build a `.prg` for your device (above) and copy it to the watch's
   `GARMIN/APPS/` folder over USB, or sideload via the simulator.
3. Author quests from Garmin Connect Mobile and verify countdowns/resets.

## Publish to the Connect IQ Store

1. **Build a release `.iq`**: VS Code **Connect IQ: Build for Export**, signing
   with your developer key. This bundles every device in `manifest.xml`.
2. At [Connect IQ Developer](https://apps.garmin.com/developer): create the app,
   upload the `.iq`, and provide:
   - **App icon** (`resources/drawables/launcher_icon.png` / the SVG source),
   - **Screenshots per device** (capture from the simulator for round,
     semi-round and rectangular screens),
   - **Supported devices** (must match the manifest),
   - **Title & description** (category — Productivity / Tools).
3. Because there are **no permissions**, review is straightforward. Submit.

## Design decisions (defaults chosen where the brief left them open)

- Week = **calendar week, Monday 00:00 local**; Month = **calendar month, 1st**.
- A **streak** = consecutive periods completed **100%** for that level,
  evaluated when the period closes.
- **Completed** section shows the **current period** only (no history).
- Slots **6 / 8 / 12**, active defaults **3 / 5 / 10**.
- Targets **both AMOLED and MIP**; pure-black background and once-per-minute
  refresh suit both.

## Fonts

Ships using device system fonts. To embed JetBrains Mono (numbers) and a rounded
sans (titles) per the design, follow `resources/fonts/README.md` — it's a
one-file change in `source/ui/Fonts.mc`.
