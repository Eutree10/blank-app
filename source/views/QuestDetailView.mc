using Toybox.WatchUi as Ui;
using Toybox.Graphics as Gfx;
using Toybox.Timer;
using Toybox.Time;
using Toybox.Lang;

// Detail of a single quest: title, countdown, the quest card, and the primary
// pill button (green COMPLETE when pending, red RESET when done) plus a Back
// link. Completing flashes a lime "+points" badge as feedback.
class QuestDetailView extends Ui.View {

    public var quest;
    private var _buttonRect;     // [x,y,w,h] for tap hit-testing
    private var _flashText;      // e.g. "+100" or null
    private var _flashTimer;

    function initialize(questIn) {
        View.initialize();
        quest = questIn;
        _buttonRect = null;
        _flashText = null;
    }

    function onUpdate(dc) {
        var service = getApp().service;
        Components.fillBackground(dc);

        var w      = dc.getWidth();
        var h      = dc.getHeight();
        var cx     = w / 2;
        var margin = Layout.sideMargin(dc);
        var cw     = w - 2 * margin;

        // Title (centered, white), up to 2 lines.
        var y = Layout.topInset(dc);
        var titleFont = Fonts.title();
        var lines = TextUtil.wrap(dc, quest.title, titleFont, cw, 2);
        var lineH = dc.getFontHeight(titleFont);
        dc.setColor(Theme.TEXT, Gfx.COLOR_TRANSPARENT);
        for (var i = 0; i < lines.size(); i++) {
            dc.drawText(cx, y, titleFont, lines[i], Gfx.TEXT_JUSTIFY_CENTER);
            y += lineH;
        }

        // Countdown (gold) with stopwatch.
        var cd = Format.countdown(service.secondsLeft(quest.level));
        var monoF = Fonts.mono();
        var cdW = dc.getTextWidthInPixels(cd, monoF);
        dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx + lineH * 0.4, y, monoF, cd, Gfx.TEXT_JUSTIFY_LEFT);
        Components.drawStopwatch(dc, cx - cdW / 2 - lineH * 0.2, y + dc.getFontHeight(monoF) / 2,
                                 dc.getFontHeight(monoF) * 0.9, Theme.GOLD);
        y += dc.getFontHeight(monoF) + (h * 0.03);

        // Quest card.
        var cardH = (h * 0.20).toNumber();
        Components.drawQuestCard(dc, margin, y, cw, cardH, quest, false);
        y += cardH + (h * 0.05);

        // Primary pill button.
        var btnW = (cw * 0.8).toNumber();
        var btnH = (h * 0.13).toNumber();
        var label = quest.completed
            ? Ui.loadResource(Rez.Strings.ActionReset)
            : Ui.loadResource(Rez.Strings.ActionComplete);
        var bg = quest.completed ? Theme.RED : Theme.GREEN;
        Components.drawPillButton(dc, cx, y, btnW, btnH, label, bg, Theme.BG, true);
        _buttonRect = [cx - btnW / 2, y, btnW, btnH];
        y += btnH + (h * 0.03);

        // Back link.
        dc.setColor(Theme.TEXT_DIM, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, y, Fonts.label(), Ui.loadResource(Rez.Strings.ActionBack),
                    Gfx.TEXT_JUSTIFY_CENTER);

        // Flash feedback (lime "+points").
        if (_flashText != null) {
            dc.setColor(Theme.LIME, Gfx.COLOR_TRANSPARENT);
            dc.drawText(cx, h * 0.30, Fonts.bigNumber(), _flashText, Gfx.TEXT_JUSTIFY_CENTER);
        }
    }

    // ---- Action -----------------------------------------------------------

    function toggle() {
        var service = getApp().service;
        if (quest.completed) {
            service.reset(quest);
            _flashText = null;
        } else {
            var pts = service.complete(quest);
            _flashText = "+" + pts.format("%d");
            startFlashTimer();
        }
        Ui.requestUpdate();
    }

    function startFlashTimer() {
        if (_flashTimer != null) { _flashTimer.stop(); }
        _flashTimer = new Timer.Timer();
        _flashTimer.start(method(:clearFlash), 900, false);
    }

    function clearFlash() {
        _flashText = null;
        if (_flashTimer != null) { _flashTimer.stop(); _flashTimer = null; }
        Ui.requestUpdate();
    }

    // Tap hit-test for the button.
    function buttonContains(px, py) {
        var r = _buttonRect;
        return r != null && px >= r[0] && px <= r[0] + r[2]
                         && py >= r[1] && py <= r[1] + r[3];
    }
}
