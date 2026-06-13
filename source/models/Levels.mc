// Static, per-level configuration. Points and time windows are FIXED by level
// (never configured per quest), as required by the brief.
module Levels {
    enum {
        DAILY   = 0,
        WEEKLY  = 1,
        MONTHLY = 2
    }

    const COUNT = 3;

    // Fixed number of configuration slots per level. These are >= the required
    // minimums (3 daily / 5 weekly / 10 monthly); the user fills the ones they
    // want and empty-titled slots are simply not shown.
    const SLOTS = [6, 8, 12];

    // Fixed XP awarded for completing a quest at each level.
    const POINTS = [100, 300, 500];

    // Property-key prefix per level (see resources/properties/properties.xml).
    const PREFIX = ["d", "w", "m"];

    // Returns the localized string id used for a level title.
    function nameResource(level) {
        if (level == DAILY)   { return Rez.Strings.DailyQuests; }
        if (level == WEEKLY)  { return Rez.Strings.WeeklyQuests; }
        return Rez.Strings.MonthlyQuests;
    }

    function shortNameResource(level) {
        if (level == DAILY)   { return Rez.Strings.LevelDaily; }
        if (level == WEEKLY)  { return Rez.Strings.LevelWeekly; }
        return Rez.Strings.LevelMonthly;
    }
}
