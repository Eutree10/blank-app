using Toybox.Application;
using Toybox.WatchUi as Ui;
using Toybox.Timer;
using Toybox.Lang;

// Application entry point. Owns the single QuestService instance and a
// once-per-minute timer that refreshes the countdown (per-minute, never
// per-second, to protect battery / AMOLED).
class QuestlineApp extends Application.AppBase {

    public var service;
    private var _timer;

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state) {
        service = new QuestService();
        _timer = new Timer.Timer();
        _timer.start(method(:onTick), 60000, true); // 60s, repeating
    }

    function onStop(state) {
        if (_timer != null) {
            _timer.stop();
            _timer = null;
        }
    }

    // Per-minute tick: only rebuild the model if a period actually rolled over
    // while the app was open; otherwise just repaint the countdown.
    function onTick() {
        if (service != null && service.rolledOver()) {
            service.load();
        }
        Ui.requestUpdate();
    }

    function getInitialView() {
        var view = new HubView();
        return [view, new HubDelegate(view)];
    }

    // Garmin Connect settings changed on the phone: rebuild quests from config.
    function onSettingsChanged() {
        if (service != null) {
            service.load();
        }
        Ui.requestUpdate();
    }
}

// Convenience accessor with the concrete type, used by views to reach the
// shared service.
function getApp() as QuestlineApp {
    return Application.getApp() as QuestlineApp;
}
