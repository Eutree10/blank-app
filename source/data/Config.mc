using Toybox.Application;
using Toybox.Application.Properties;
using Toybox.Lang;

// Reads the user's quest configuration from Application.Properties (authored in
// the Garmin Connect phone app via settings.xml). This layer ONLY reads
// configuration; persisted runtime state lives in Store.mc.
module Config {

    // Builds the list of *visible* quests for a level: enabled slots with a
    // non-empty title. `deadlineMoment` is the shared end-of-period for the level.
    function readLevel(level, deadlineMoment) {
        var quests = [];
        var slots  = Levels.SLOTS[level];
        var prefix = Levels.PREFIX[level];
        for (var i = 0; i < slots; i++) {
            var on    = getBool(prefix + i + "_on");
            var title = getString(prefix + i + "_title");
            if (on && title.length() > 0) {
                var cat = getNumber(prefix + i + "_cat");
                quests.add(new Quest(level, i, title, cat, deadlineMoment));
            }
        }
        return quests;
    }

    // Slot indices that are currently enabled with text, used when closing a
    // period to decide whether it was 100% completed (streak evaluation).
    function enabledSlots(level) {
        var result = [];
        var slots  = Levels.SLOTS[level];
        var prefix = Levels.PREFIX[level];
        for (var i = 0; i < slots; i++) {
            if (getBool(prefix + i + "_on") && getString(prefix + i + "_title").length() > 0) {
                result.add(i);
            }
        }
        return result;
    }

    // ---- Typed, null-safe property accessors --------------------------------

    function getBool(key) {
        var v = readProperty(key);
        return (v != null) ? (v == true) : false;
    }

    function getString(key) {
        var v = readProperty(key);
        if (v == null) { return ""; }
        var s = v.toString();
        // Trim leading/trailing whitespace so an accidental space isn't "text".
        return trim(s);
    }

    function getNumber(key) {
        var v = readProperty(key);
        if (v == null) { return 0; }
        if (v instanceof Lang.Number) { return v; }
        if (v instanceof Lang.Float)  { return v.toNumber(); }
        if (v instanceof Lang.String) {
            try { return v.toNumber(); } catch (e) { return 0; }
        }
        return 0;
    }

    function readProperty(key) {
        // Properties.getValue throws if the key is unknown; guard it.
        try {
            return Properties.getValue(key);
        } catch (e) {
            return null;
        }
    }

    function trim(s) {
        var start = 0;
        var end = s.length();
        while (start < end && s.substring(start, start + 1).equals(" ")) { start += 1; }
        while (end > start && s.substring(end - 1, end).equals(" ")) { end -= 1; }
        return s.substring(start, end);
    }
}
