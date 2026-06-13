using Toybox.WatchUi as Ui;

// Hub input. Uses BehaviorDelegate semantic callbacks so the SAME code drives
// both physical buttons and touch:
//   * next/previous page (down/up buttons or vertical swipe) -> move focus
//   * select (start button or tap) -> open the focused level
//   * tap (touch only) -> open the tapped level row directly
class HubDelegate extends Ui.BehaviorDelegate {

    private var _view;

    function initialize(view) {
        BehaviorDelegate.initialize();
        _view = view;
    }

    function onNextPage() {
        _view.moveFocus(1);
        return true;
    }

    function onPreviousPage() {
        _view.moveFocus(-1);
        return true;
    }

    function onSelect() {
        openLevel(_view.focusRow);
        return true;
    }

    // Touch: open the specific row tapped (and sync focus).
    function onTap(evt) {
        var coord = evt.getCoordinates();
        var lvl = _view.levelAt(coord[0], coord[1]);
        if (lvl >= 0) {
            _view.focusRow = lvl;
            openLevel(lvl);
            return true;
        }
        return false;
    }

    function openLevel(level) {
        var view = new QuestListView(level);
        Ui.pushView(view, new QuestListDelegate(view), Ui.SLIDE_LEFT);
    }
}
