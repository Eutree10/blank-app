using Toybox.WatchUi as Ui;

// Menu2 level switcher for button-only devices (touch devices use left/right
// swipes). Each item's id is the level constant.
class LevelMenu extends Ui.Menu2 {
    function initialize(currentLevel) {
        Menu2.initialize({ :title => Ui.loadResource(Rez.Strings.SwitchLevel) });
        addItem(new Ui.MenuItem(Ui.loadResource(Rez.Strings.DailyQuests),   null, Levels.DAILY,   null));
        addItem(new Ui.MenuItem(Ui.loadResource(Rez.Strings.WeeklyQuests),  null, Levels.WEEKLY,  null));
        addItem(new Ui.MenuItem(Ui.loadResource(Rez.Strings.MonthlyQuests), null, Levels.MONTHLY, null));
    }
}

class LevelMenuDelegate extends Ui.Menu2InputDelegate {
    private var _listView;

    function initialize(listView) {
        Menu2InputDelegate.initialize();
        _listView = listView;
    }

    function onSelect(item) {
        _listView.setLevel(item.getId());
        Ui.popView(Ui.SLIDE_DOWN);
    }

    function onBack() {
        Ui.popView(Ui.SLIDE_DOWN);
        return true;
    }
}
