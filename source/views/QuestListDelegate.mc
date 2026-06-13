using Toybox.WatchUi as Ui;

// Quest list input. Unified buttons + touch:
//   * next/previous page (down/up button or vertical swipe) -> move focus/scroll
//   * select (start button or tap) -> open the focused quest detail
//   * tap (touch) -> open the tapped card
//   * menu (menu button or long press) -> level switch menu (button devices)
//   * swipe left / right (touch) -> previous / next level
//   * back -> return to the hub
class QuestListDelegate extends Ui.BehaviorDelegate {

    private var _view;

    function initialize(view) {
        BehaviorDelegate.initialize();
        _view = view;
    }

    function onNextPage() {
        _view.focusNext();
        return true;
    }

    function onPreviousPage() {
        _view.focusPrev();
        return true;
    }

    function onSelect() {
        openFocused();
        return true;
    }

    function onTap(evt) {
        var coord = evt.getCoordinates();
        var quest = _view.questAt(coord[0], coord[1]);
        if (quest != null) {
            openQuest(quest);
            return true;
        }
        return false;
    }

    // Touch swipes: horizontal switches level; vertical falls through to the
    // page behaviors above.
    function onSwipe(evt) {
        var dir = evt.getDirection();
        if (dir == Ui.SWIPE_LEFT) {
            switchLevel(1);
            return true;
        } else if (dir == Ui.SWIPE_RIGHT) {
            switchLevel(-1);
            return true;
        }
        return false;
    }

    // Button devices switch level through a menu.
    function onMenu() {
        Ui.pushView(new LevelMenu(_view.level), new LevelMenuDelegate(_view), Ui.SLIDE_UP);
        return true;
    }

    function openFocused() {
        var quest = _view.focusedQuest();
        if (quest != null) {
            openQuest(quest);
        }
    }

    function openQuest(quest) {
        var detail = new QuestDetailView(quest);
        Ui.pushView(detail, new QuestDetailDelegate(detail), Ui.SLIDE_LEFT);
    }

    function switchLevel(delta) {
        var next = (_view.level + delta + Levels.COUNT) % Levels.COUNT;
        var view = new QuestListView(next);
        var anim = (delta > 0) ? Ui.SLIDE_LEFT : Ui.SLIDE_RIGHT;
        Ui.switchToView(view, new QuestListDelegate(view), anim);
    }
}
