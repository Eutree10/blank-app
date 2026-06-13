using Toybox.Graphics as Gfx;

// Questline color palette. Each color owns a single role so they never compete.
// See the design brief: base neutrals + four functional accents.
module Theme {
    // --- Base / neutrals ---
    const BG          = 0x000000;   // pure black (AMOLED-friendly)
    const SURFACE     = 0x15161A;   // card / detail panel background
    const BORDER      = 0x2A2C31;   // hairline borders
    const TEXT        = 0xFFFFFF;   // primary text
    const TEXT_DIM    = 0x8A8F98;   // secondary text
    const RAIL        = 0x2E323A;   // progress-bar track

    // --- Functional accents ---
    const GOLD        = 0xF4B400;   // brand + time (logo, stopwatch, countdown, focus)
    const BLUE        = 0x2F86C5;   // pending quests + the hub COMPLETED card accent
    const BLUE_PANEL  = 0x13384B;   // darker points panel on a pending card
    const LIME        = 0xA3E635;   // energy: XP + points (the bolt and the numbers)
    const GREEN       = 0x3FB950;   // completed / success (done cards, COMPLETE, bars)
    const RED         = 0xF85149;   // destructive (RESET)

    // A slightly deepened blue for the pending-card fill so white text on top
    // keeps strong contrast.
    const BLUE_CARD   = 0x256AA0;
}
