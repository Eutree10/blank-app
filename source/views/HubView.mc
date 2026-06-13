using Toybox.WatchUi as Ui;
using Toybox.Graphics as Gfx;
using Toybox.Lang;

// Hub / home screen: brand logo, two stat cards (TOTAL XP, COMPLETED) and the
// three level rows with progress bars. One level row is "focused" for
// button-based navigation; the focus ring is gold.
class HubView extends Ui.View {

    public var focusRow;          // 0..2, the highlighted level row
    private var _rowRects;        // cached [x,y,w,h] per level row for tap hit-testing
    private var _logo;

    function initialize() {
        View.initialize();
        focusRow = Levels.DAILY;
        _rowRects = [null, null, null];
    }

    function onLayout(dc) {
        _logo = Ui.loadResource(Rez.Drawables.Logo);
    }

    function onShow() {
        // Returning to the hub: refresh stats and catch any rollover.
        var app = getApp();
        if (app.service != null) {
            app.service.load();
        }
    }

    function onUpdate(dc) {
        var service = getApp().service;
        Components.fillBackground(dc);

        var w      = dc.getWidth();
        var h      = dc.getHeight();
        var cx     = w / 2;
        var margin = Layout.sideMargin(dc);
        var cw     = w - 2 * margin;

        // --- Logo (gold emblem) centered at the top ---
        var y = Layout.topInset(dc);
        if (_logo != null) {
            dc.drawBitmap(cx - _logo.getWidth() / 2, y, _logo);
            y += _logo.getHeight() + (h * 0.02);
        } else {
            y += h * 0.10;
        }

        // --- Two stat cards side by side ---
        var gap     = (cw * 0.06).toNumber();
        var cardW   = (cw - gap) / 2;
        var cardH   = (h * 0.20).toNumber();
        var xpStr   = Format.abbreviate(service.xpTotal);
        var doneStr = service.completedTotal.format("%d");
        Components.drawStatCard(dc, margin, y, cardW, cardH,
            Ui.loadResource(Rez.Strings.TotalXp), xpStr,
            Theme.LIME, Theme.LIME, "bolt");
        Components.drawStatCard(dc, margin + cardW + gap, y, cardW, cardH,
            Ui.loadResource(Rez.Strings.Completed), doneStr,
            Theme.BLUE, Theme.GREEN, "stopwatch");
        y += cardH + (h * 0.04);

        // --- Three level rows ---
        var rowGap = (h * 0.02).toNumber();
        var remaining = h - y - Layout.topInset(dc) / 2;
        var rowH = ((remaining - 2 * rowGap) / 3).toNumber();
        for (var lvl = 0; lvl < Levels.COUNT; lvl++) {
            var p = service.progress(lvl);
            var name = Ui.loadResource(Levels.nameResource(lvl));
            _rowRects[lvl] = [margin, y, cw, rowH];
            Components.drawLevelRow(dc, margin, y, cw, rowH, name, p[0], p[1],
                                    service.streakFor(lvl), lvl == focusRow);
            y += rowH + rowGap;
        }
    }

    // Returns the level whose row contains screen y, or -1.
    function levelAt(px, py) {
        for (var lvl = 0; lvl < Levels.COUNT; lvl++) {
            var r = _rowRects[lvl];
            if (r != null && py >= r[1] && py <= r[1] + r[3]) {
                return lvl;
            }
        }
        return -1;
    }

    function moveFocus(delta) {
        focusRow = (focusRow + delta + Levels.COUNT) % Levels.COUNT;
        Ui.requestUpdate();
    }
}
