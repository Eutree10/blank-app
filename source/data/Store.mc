using Toybox.Application;
using Toybox.Application.Storage;
using Toybox.Lang;

// Persistence layer (Application.Storage). Kept separate from configuration
// reading (Config.mc). Stores: per-level completion bitmaps and period ids,
// lifetime XP, total completed count, and per-level streaks.
module Store {

    const K_PERIOD  = ["period_d", "period_w", "period_m"];
    const K_DONE    = ["done_d", "done_w", "done_m"];
    const K_STREAK  = ["streak_d", "streak_w", "streak_m"];
    const K_XP      = "xp_total";
    const K_DONECNT = "completed_total";

    // ---- Period ids ----

    function getPeriod(level) {
        var v = Storage.getValue(K_PERIOD[level]);
        return (v instanceof Lang.Number) ? v : -1;
    }

    function setPeriod(level, id) {
        Storage.setValue(K_PERIOD[level], id);
    }

    // ---- Completion bitmaps (Array<Boolean> of length Levels.SLOTS[level]) ----

    function getDone(level) {
        var size = Levels.SLOTS[level];
        var v = Storage.getValue(K_DONE[level]);
        if (!(v instanceof Lang.Array) || v.size() != size) {
            return newBoolArray(size);
        }
        return v;
    }

    function setDone(level, arr) {
        Storage.setValue(K_DONE[level], arr);
    }

    function newBoolArray(size) {
        var a = new [size];
        for (var i = 0; i < size; i++) { a[i] = false; }
        return a;
    }

    // ---- Lifetime XP ----

    function getXp() {
        var v = Storage.getValue(K_XP);
        return (v instanceof Lang.Number) ? v : 0;
    }

    function setXp(value) {
        Storage.setValue(K_XP, value);
    }

    // ---- Total completed count ----

    function getCompletedCount() {
        var v = Storage.getValue(K_DONECNT);
        return (v instanceof Lang.Number) ? v : 0;
    }

    function setCompletedCount(value) {
        Storage.setValue(K_DONECNT, value);
    }

    // ---- Streaks ----

    function getStreak(level) {
        var v = Storage.getValue(K_STREAK[level]);
        return (v instanceof Lang.Number) ? v : 0;
    }

    function setStreak(level, value) {
        Storage.setValue(K_STREAK[level], value);
    }
}
