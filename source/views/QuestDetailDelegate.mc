using Toybox.WatchUi as Ui;

// Detail input. select (start button) or a tap on the pill toggles
// complete/reset; back returns to the list.
class QuestDetailDelegate extends Ui.BehaviorDelegate {

    private var _view;

    function initialize(view) {
        BehaviorDelegate.initialize();
        _view = view;
    }

    function onSelect() {
        _view.toggle();
        return true;
    }

    function onTap(evt) {
        var coord = evt.getCoordinates();
        if (_view.buttonContains(coord[0], coord[1])) {
            _view.toggle();
            return true;
        }
        return false;
    }
}
