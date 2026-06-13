using Toybox.Time;
using Toybox.Lang;

// The engine. Holds the in-memory model and is the single source of truth for
// the views. Created once by the app and reached via Application.getApp().service.
//
// Responsibilities:
//   * detect period rollovers and reset the affected level (closing the old
//     period and updating its streak),
//   * build the visible quest lists from configuration + persisted state,
//   * complete / reset quests and keep lifetime stats in sync.
class QuestService {

    public var quests;       // [ Array<Quest>, Array<Quest>, Array<Quest> ]  per level
    public var deadlines;    // [ Time.Moment x3 ]
    public var xpTotal;
    public var completedTotal;
    public var streaks;      // [ Number x3 ]

    function initialize() {
        quests    = [[], [], []];
        deadlines = [null, null, null];
        streaks   = [0, 0, 0];
        load();
    }

    // Full (re)load: apply resets, recompute deadlines, rebuild quests from
    // configuration and pull global stats. Safe to call on launch and whenever
    // settings change.
    function load() {
        checkResets();
        for (var lvl = 0; lvl < Levels.COUNT; lvl++) {
            deadlines[lvl] = Periods.deadline(lvl);
            quests[lvl]    = Config.readLevel(lvl, deadlines[lvl]);
            applyDoneState(lvl);
            streaks[lvl]   = Store.getStreak(lvl);
        }
        xpTotal        = Store.getXp();
        completedTotal = Store.getCompletedCount();
    }

    // Detects rollover per level. If the stored period id differs from the
    // current one, the previous period is closed (failed quests simply never
    // scored) and the level's completion bitmap is cleared for the new period.
    function checkResets() {
        for (var lvl = 0; lvl < Levels.COUNT; lvl++) {
            var nowId    = Periods.currentId(lvl);
            var storedId = Store.getPeriod(lvl);
            if (storedId != nowId) {
                if (storedId != -1) {
                    closePeriod(lvl); // evaluate streak on the period that ended
                }
                Store.setDone(lvl, Store.newBoolArray(Levels.SLOTS[lvl]));
                Store.setPeriod(lvl, nowId);
            }
        }
    }

    // Streak rule: a streak increments when a level finished its period 100%
    // completed (every enabled quest done), otherwise it resets to 0.
    function closePeriod(level) {
        var done    = Store.getDone(level);
        var enabled = Config.enabledSlots(level);
        var full    = (enabled.size() > 0);
        for (var i = 0; i < enabled.size(); i++) {
            if (!done[enabled[i]]) { full = false; break; }
        }
        var streak = Store.getStreak(level);
        streak = full ? (streak + 1) : 0;
        Store.setStreak(level, streak);
    }

    // Stamp the persisted completion bitmap onto the freshly built quests.
    function applyDoneState(level) {
        var done = Store.getDone(level);
        var list = quests[level];
        for (var i = 0; i < list.size(); i++) {
            var q = list[i];
            q.completed = done[q.slot];
        }
    }

    // Cheap, non-mutating check: has any level's period rolled over since the
    // last persisted id? Used by the per-minute timer to decide if a full
    // reload is needed (vs. just repainting the countdown).
    function rolledOver() {
        for (var lvl = 0; lvl < Levels.COUNT; lvl++) {
            if (Periods.currentId(lvl) != Store.getPeriod(lvl)) { return true; }
        }
        return false;
    }

    // ---- Queries used by the views ----

    function questsFor(level)      { return quests[level]; }
    function deadlineFor(level)    { return deadlines[level]; }
    function secondsLeft(level)    { return Periods.secondsUntil(deadlines[level]); }
    function streakFor(level)      { return streaks[level]; }

    // [doneCount, total] over the visible quests of a level.
    function progress(level) {
        var list = quests[level];
        var done = 0;
        for (var i = 0; i < list.size(); i++) {
            if (list[i].completed) { done += 1; }
        }
        return [done, list.size()];
    }

    // ---- Mutations ----

    // Completes a quest once per period: awards XP and bumps counters. Returns
    // the points awarded (for the +XP flash), or 0 if it was already complete.
    function complete(quest) {
        if (quest.completed) { return 0; }
        quest.completed   = true;
        quest.completedAt = Time.now();

        var done = Store.getDone(quest.level);
        done[quest.slot] = true;
        Store.setDone(quest.level, done);

        xpTotal += quest.points;
        completedTotal += 1;
        Store.setXp(xpTotal);
        Store.setCompletedCount(completedTotal);
        return quest.points;
    }

    // Undo a completion within the same period.
    function reset(quest) {
        if (!quest.completed) { return; }
        quest.completed   = false;
        quest.completedAt = null;

        var done = Store.getDone(quest.level);
        done[quest.slot] = false;
        Store.setDone(quest.level, done);

        xpTotal = xpTotal - quest.points;
        if (xpTotal < 0) { xpTotal = 0; }
        completedTotal = completedTotal - 1;
        if (completedTotal < 0) { completedTotal = 0; }
        Store.setXp(xpTotal);
        Store.setCompletedCount(completedTotal);
    }
}
