using Toybox.Time;
using Toybox.WatchUi;

// A single quest. Points are derived from the level (not stored per quest).
// `slot` is the stable 0-based index into the level's fixed slot array and is
// what links a quest to its persisted completion state, so it survives the
// user re-typing the quest text on the phone.
class Quest {
    public var level;        // Levels.DAILY | WEEKLY | MONTHLY
    public var slot;         // 0 .. Levels.SLOTS[level]-1
    public var title;        // user-authored text
    public var category;     // category index 0..4
    public var points;       // derived from level
    public var deadline;     // Time.Moment: end of the current period for this level
    public var completed;    // Boolean
    public var completedAt;  // Time.Moment or null

    function initialize(levelIn, slotIn, titleIn, categoryIn, deadlineIn) {
        level       = levelIn;
        slot        = slotIn;
        title       = titleIn;
        category    = categoryIn;
        points      = Levels.POINTS[levelIn];
        deadline    = deadlineIn;
        completed   = false;
        completedAt = null;
    }

    // Localized category label.
    function categoryName() {
        var ids = [Rez.Strings.Cat0, Rez.Strings.Cat1, Rez.Strings.Cat2,
                   Rez.Strings.Cat3, Rez.Strings.Cat4];
        var idx = (category >= 0 && category < ids.size()) ? category : 4;
        return WatchUi.loadResource(ids[idx]);
    }
}
